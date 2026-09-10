"""Process-separated protected-world generation, estimation, and scoring."""

from __future__ import annotations

import json
import math
import secrets
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from geocausal.artifacts import atomic_write_json, canonical_hash, utc_now
from geocausal.aware import AwareSelector
from geocausal.config import ExperimentConfig
from geocausal.decision import decide
from geocausal.dgp import ObservedWorld, generate_world
from geocausal.diagnostics import diagnostic_features
from geocausal.estimators import Estimate, estimate_all
from geocausal.simulation.benchmark import METHODS, _bootstrap_ci


def create_protected_seed_set(root: Path, config: ExperimentConfig) -> dict[str, Any]:
    path = root / "data" / "protected" / "final_world_seeds.json"
    if path.exists():
        raise FileExistsError("Protected final seed set already exists")
    scenarios = ["S00"] * 3 + [f"S{i:02d}" for i in range(1, 14)]
    worlds = [
        {
            "index": index,
            "world_id": f"FINAL-{index:05d}",
            "scenario_id": scenarios[index % len(scenarios)],
            "effect_scale": (0.0, 0.025, 0.05, 0.075)[index % 4],
            "seed": secrets.randbits(63),
        }
        for index in range(config.worlds.final)
    ]
    atomic_write_json(path, {"worlds": worlds})
    identities = [
        {
            "world_id": item["world_id"],
            "scenario_id": item["scenario_id"],
            "identity_hash": canonical_hash(item),
        }
        for item in worlds
    ]
    public = {
        "world_count": len(worlds),
        "seed_set_hash": canonical_hash(worlds),
        "world_identities": identities,
    }
    atomic_write_json(
        root / "evidence" / "freeze" / "final_world_identities.json", public
    )
    return public


def prepare_protected_worlds(
    root: Path, config: ExperimentConfig, protocol_id: str
) -> dict[str, Any]:
    seeds = json.loads(
        (root / "data" / "protected" / "final_world_seeds.json").read_text()
    )["worlds"]
    observed_root = root / "data" / "protected" / "final" / "observed"
    truth_root = root / "data" / "protected" / "final" / "truth"
    observed_root.mkdir(parents=True, exist_ok=False)
    truth_root.mkdir(parents=True, exist_ok=False)
    for item in seeds:
        world, truth = generate_world(
            seed=int(item["seed"]),
            world_id=str(item["world_id"]),
            scenario_id=str(item["scenario_id"]),
            n_geos=config.n_geos,
            pre_days=config.pre_days,
            test_days=config.test_days,
            cooldown_days=config.cooldown_days,
            treatment_share=config.treatment_share,
            effect_scale=float(item["effect_scale"]),
        )
        np.savez_compressed(
            observed_root / f"{world.world_id}.npz",
            outcomes=world.outcomes,
            spend=world.spend,
            assigned=world.assigned,
            delivered_dose=world.delivered_dose,
        )
        np.savez_compressed(
            truth_root / f"{world.world_id}.npz",
            itt_total=truth.itt_total,
            delivered_dose_effect=truth.delivered_dose_effect,
            no_treatment_analysis=truth.no_treatment_analysis,
        )
    marker = {
        "protocol_id": protocol_id,
        "worlds": len(seeds),
        "observed_root": str(observed_root),
        "truth_root": str(truth_root),
        "world_index": [
            {"world_id": item["world_id"], "scenario_id": item["scenario_id"]}
            for item in seeds
        ],
    }
    atomic_write_json(
        root / "artifacts" / "final_committed" / "generation.json", marker
    )
    return marker


def _load_world(
    path: Path, item: dict[str, Any], config: ExperimentConfig
) -> ObservedWorld:
    with np.load(path) as arrays:
        return ObservedWorld(
            world_id=str(item["world_id"]),
            scenario_id=str(item["scenario_id"]),
            outcomes=arrays["outcomes"],
            spend=arrays["spend"],
            assigned=arrays["assigned"],
            delivered_dose=arrays["delivered_dose"],
            pre_days=config.pre_days,
            test_days=config.test_days,
            cooldown_days=config.cooldown_days,
        )


def evaluate_without_truth(
    root: Path,
    config: ExperimentConfig,
    protocol_id: str,
    selector_artifact: dict[str, Any],
) -> dict[str, Any]:
    """Estimator process: this function has no path or parameter for truth."""
    selector = AwareSelector.restore(selector_artifact)
    fixed_method = str(selector_artifact["strongest_fixed"])
    items = json.loads(
        (root / "artifacts" / "final_committed" / "generation.json").read_text()
    )["world_index"]
    observed_root = root / "data" / "protected" / "final" / "observed"
    estimator_rows: list[dict[str, Any]] = []
    selector_rows: list[dict[str, Any]] = []
    for item in items:
        world = _load_world(observed_root / f"{item['world_id']}.npz", item, config)
        features = {method: diagnostic_features(world, method) for method in METHODS}
        selection = selector.select(features)
        estimates = estimate_all(world)
        for method, estimate in estimates.items():
            estimator_rows.append(
                {
                    "protocol_id": protocol_id,
                    "evidence_class": "SIMULATED",
                    "world_id": world.world_id,
                    "scenario_id": world.scenario_id,
                    "method_id": method,
                    **asdict(estimate),
                    **features[method],
                }
            )
        selected = (
            None if selection.abstained else estimates[selection.selected_method or ""]
        )
        fixed = estimates[fixed_method]
        materiality = max(
            float(np.nansum(world.outcomes[:, : world.pre_days]) * 0.005), 1.0
        )
        committed = {
            "protocol_id": protocol_id,
            "world_id": world.world_id,
            "scenario_id": world.scenario_id,
            "selected_method": selection.selected_method,
            "eligible_methods": list(selection.eligible_methods),
            "predicted_risk": selection.predicted_risk,
            "abstained": selection.abstained,
            "selected_estimate": None if selected is None else asdict(selected),
            "fixed_method": fixed_method,
            "fixed_estimate": asdict(fixed),
            "materiality": materiality,
        }
        committed["commitment_hash"] = canonical_hash(committed)
        selector_rows.append(committed)
    target = root / "artifacts" / "final_committed"
    pd.DataFrame(estimator_rows).to_parquet(target / "estimates.parquet", index=False)
    pd.DataFrame(selector_rows).to_parquet(target / "selections.parquet", index=False)
    marker = {"protocol_id": protocol_id, "worlds": len(items), "truth_access": False}
    atomic_write_json(target / "evaluation_complete.json", marker)
    return marker


def _estimate_from(value: dict[str, Any] | None) -> Estimate | None:
    return None if value is None else Estimate(**value)


def score_committed_once(
    root: Path, config: ExperimentConfig, protocol_id: str
) -> dict[str, Any]:
    final_root = root / "evidence" / "final"
    if (final_root / "confirmatory_metrics.json").exists():
        raise FileExistsError("Canonical E14 score already exists")
    committed_root = root / "artifacts" / "final_committed"
    selectors = pd.read_parquet(committed_root / "selections.parquet")
    estimators = pd.read_parquet(committed_root / "estimates.parquet")
    truth_root = root / "data" / "protected" / "final" / "truth"
    scored_rows: list[dict[str, Any]] = []
    ledger: list[dict[str, str]] = []
    truth_by_world: dict[str, float] = {}
    frozen_identities = {
        item["world_id"]: item["identity_hash"]
        for item in json.loads(
            (root / "evidence" / "freeze" / "final_world_identities.json").read_text()
        )["world_identities"]
    }
    for raw_row in selectors.to_dict(orient="records"):
        row: dict[str, Any] = {str(key): value for key, value in raw_row.items()}
        world_id = str(row["world_id"])
        with np.load(truth_root / f"{world_id}.npz") as truth:
            true_effect = float(truth["itt_total"])
        truth_by_world[world_id] = true_effect
        ledger.append(
            {
                "world_id": world_id,
                "world_identity_hash": frozen_identities[world_id],
                "first_access_timestamp": utc_now(),
                "accessing_stage": "E14_CANONICAL_SCORING",
                "protocol_id": protocol_id,
                "committed_selection_hash": str(row["commitment_hash"]),
            }
        )
        selected = _estimate_from(row["selected_estimate"])
        fixed = _estimate_from(row["fixed_estimate"])
        materiality = float(row["materiality"])
        aware_decision = decide(selected, true_effect, materiality=materiality)
        fixed_decision = decide(fixed, true_effect, materiality=materiality)
        scored_rows.append(
            {
                **row,
                "true_effect": true_effect,
                "estimate": None if selected is None else selected.estimate,
                "sq_error": None
                if selected is None
                else (selected.estimate - true_effect) ** 2,
                "covered_truth": None
                if selected is None
                else selected.ci_low <= true_effect <= selected.ci_high,
                "reject_null": None if selected is None else selected.p_value < 0.05,
                "sign_correct": None
                if selected is None
                else true_effect == 0
                or np.sign(selected.estimate) == np.sign(true_effect),
                "decision": aware_decision.decision,
                "oracle_decision": aware_decision.oracle_decision,
                "decision_regret": aware_decision.regret,
                "false_launch": aware_decision.false_launch,
                "false_stop": aware_decision.false_stop,
                "fixed_sq_error": (fixed.estimate - true_effect) ** 2
                if fixed
                else math.nan,
                "fixed_decision_regret": fixed_decision.regret,
            }
        )
    estimator_scored = estimators.copy()
    estimator_scored["true_effect"] = estimator_scored.world_id.map(truth_by_world)
    estimator_scored["bias"] = estimator_scored.estimate - estimator_scored.true_effect
    estimator_scored["abs_error"] = estimator_scored.bias.abs()
    estimator_scored["sq_error"] = estimator_scored.bias**2
    estimator_scored["covered_truth"] = (
        estimator_scored.ci_low <= estimator_scored.true_effect
    ) & (estimator_scored.true_effect <= estimator_scored.ci_high)
    final_root.mkdir(parents=True, exist_ok=True)
    estimator_scored.to_parquet(
        final_root / "fact_estimator_result.parquet", index=False
    )
    scored = pd.DataFrame(scored_rows)
    scored.to_parquet(final_root / "fact_selector_result.parquet", index=False)
    atomic_write_json(final_root / "truth_access_ledger.json", ledger)
    non_abstained = scored.loc[~scored.abstained]
    clean = scored.loc[(scored.scenario_id == "S00") & ~scored.abstained]
    aware_rmse = float(np.sqrt(clean.sq_error.mean()))
    fixed_rmse = float(np.sqrt(clean.fixed_sq_error.mean()))
    paired = (
        scored.loc[scored.scenario_id != "S00", "decision_regret"]
        - scored.loc[scored.scenario_id != "S00", "fixed_decision_regret"]
    ).to_numpy(float)
    h2_ci = _bootstrap_ci(paired, config.seed + 18)
    null = non_abstained.loc[non_abstained.true_effect == 0]
    h1_pass = aware_rmse / max(fixed_rmse, 1e-12) <= 1.05
    h2_pass = h2_ci[1] < 0
    critical = {
        "null_type_i": float(null.reject_null.mean()) <= 0.075,
        "coverage": float(non_abstained.covered_truth.mean()) >= 0.90,
        "clean_abstention": float(
            scored.loc[scored.scenario_id == "S00", "abstained"].mean()
        )
        <= 0.10,
        "truth_ledger_complete": len(ledger) == config.worlds.final,
    }
    metrics: dict[str, Any] = {
        "protocol_id": protocol_id,
        "worlds": len(scored),
        "strongest_fixed": str(scored.fixed_method.iloc[0]),
        "selection_frequency": dict(Counter(scored.selected_method.dropna())),
        "abstention_rate": float(scored.abstained.mean()),
        "clean_abstention_rate": float(
            scored.loc[scored.scenario_id == "S00", "abstained"].mean()
        ),
        "selection_aware_coverage": float(non_abstained.covered_truth.mean()),
        "selection_aware_null_type_i": float(null.reject_null.mean()),
        "false_launch_rate": float(scored.false_launch.mean()),
        "false_stop_rate": float(scored.false_stop.mean()),
        "aware_mean_regret": float(scored.decision_regret.mean()),
        "fixed_mean_regret": float(scored.fixed_decision_regret.mean()),
        "h1": {
            "aware_clean_rmse": aware_rmse,
            "fixed_clean_rmse": fixed_rmse,
            "ratio": aware_rmse / max(fixed_rmse, 1e-12),
            "margin": 1.05,
            "pass": h1_pass,
        },
        "h2": {
            "mean_paired_regret_difference": float(paired.mean()),
            "ci_low": h2_ci[0],
            "ci_high": h2_ci[1],
            "pass": h2_pass,
        },
        "critical_gates": critical,
        "promotion_eligible": h1_pass and h2_pass and all(critical.values()),
    }
    atomic_write_json(final_root / "confirmatory_metrics.json", metrics)
    return metrics
