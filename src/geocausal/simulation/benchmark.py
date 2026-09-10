"""Leakage-controlled development, null, and final Monte Carlo execution."""

from __future__ import annotations

import math
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
from geocausal.dgp import TruthRecord, generate_world
from geocausal.diagnostics import diagnostic_features
from geocausal.estimators import Estimate, estimate_all

METHODS = (
    "independent_tbr",
    "independent_did",
    "independent_ridge_sc",
    "independent_simplex_sc",
)


def _seed(base: int, phase: int, index: int) -> int:
    sequence = np.random.SeedSequence([base, phase, index])
    return int(sequence.generate_state(1, dtype=np.uint32)[0])


def _loss(estimate: Estimate, truth: TruthRecord, scale: float) -> float:
    if estimate.status != "SUCCESS" or not np.isfinite(estimate.estimate):
        return 2.0
    normalized_error = abs(estimate.estimate - truth.itt_total) / max(scale, 1.0)
    miscoverage = float(not (estimate.ci_low <= truth.itt_total <= estimate.ci_high))
    false_positive = float(truth.itt_total == 0 and estimate.p_value < 0.05)
    sign_error = float(
        truth.itt_total != 0 and np.sign(estimate.estimate) != np.sign(truth.itt_total)
    )
    return float(
        normalized_error + 0.5 * miscoverage + false_positive + 1.5 * sign_error
    )


def _estimator_row(
    *,
    protocol_id: str,
    phase: str,
    scenario: str,
    world_id: str,
    truth: TruthRecord,
    estimate: Estimate,
    diagnostics: dict[str, float],
) -> dict[str, Any]:
    error = estimate.estimate - truth.itt_total
    return {
        "protocol_id": protocol_id,
        "evidence_class": "SIMULATED",
        "phase": phase,
        "world_id": world_id,
        "dataset_id": "DGP_A_v1",
        "scenario_id": scenario,
        "dgp_family": "randomized_geo",
        "method_id": estimate.method_id,
        "selector_id": None,
        "design_id": "stratified_v1",
        "n_geos": 40,
        "pre_days": 168,
        "test_days": 28,
        "canonical_estimand": "track_a_assignment_itt_total_incremental_conversions",
        "true_effect": truth.itt_total,
        "true_value": truth.itt_total,
        "estimate": estimate.estimate,
        "standard_error": estimate.standard_error,
        "ci_low": estimate.ci_low,
        "ci_high": estimate.ci_high,
        "bias": error,
        "abs_error": abs(error),
        "sq_error": error**2,
        "covered_truth": estimate.ci_low <= truth.itt_total <= estimate.ci_high,
        "p_value": estimate.p_value,
        "reject_null": estimate.p_value < 0.05,
        "sign_correct": truth.itt_total == 0
        or np.sign(estimate.estimate) == np.sign(truth.itt_total),
        **diagnostics,
        "selected_method": None,
        "abstained": False,
        "decision": None,
        "oracle_decision": None,
        "decision_regret": None,
        "false_launch": None,
        "false_stop": None,
        "runtime_sec": None,
        "peak_memory_mb": None,
        "status": estimate.status,
        "failure_reason": estimate.failure_reason,
        "package_version": "geo-causal-bench-independent-0.1.0",
        "artifact_hash": None,
    }


def run_development(
    root: Path, config: ExperimentConfig, protocol_id: str
) -> dict[str, Any]:
    feature_rows: list[dict[str, float]] = []
    losses: list[float] = []
    rows: list[dict[str, Any]] = []
    worlds = config.worlds.development
    scenarios = [f"S{i:02d}" for i in range(13)]
    for index in range(worlds):
        scenario = scenarios[index % len(scenarios)]
        world_id = f"DEV-{index:05d}"
        effect_scale = (0.0, 0.025, 0.05, 0.075)[index % 4]
        world, truth = generate_world(
            seed=_seed(config.seed, 11, index),
            world_id=world_id,
            scenario_id=scenario,
            n_geos=config.n_geos,
            pre_days=config.pre_days,
            test_days=config.test_days,
            cooldown_days=config.cooldown_days,
            treatment_share=config.treatment_share,
            effect_scale=effect_scale,
        )
        estimates = estimate_all(world)
        scale = max(
            world.outcomes[:, : config.pre_days].sum() * 0.01, abs(truth.itt_total)
        )
        for method_id, estimate in estimates.items():
            features = diagnostic_features(world, method_id)
            feature_rows.append(features)
            losses.append(_loss(estimate, truth, scale))
            rows.append(
                _estimator_row(
                    protocol_id=protocol_id,
                    phase="E11",
                    scenario=scenario,
                    world_id=world_id,
                    truth=truth,
                    estimate=estimate,
                    diagnostics=features,
                )
            )

    selector = AwareSelector(risk_limit=1.25)
    selector.fit(feature_rows, np.asarray(losses))
    method_rmse = (
        pd.DataFrame(rows)
        .groupby("method_id", as_index=False)["sq_error"]
        .mean()
        .assign(rmse=lambda x: np.sqrt(x["sq_error"]))
    )
    strongest_fixed = str(method_rmse.sort_values("rmse").iloc[0]["method_id"])
    selector_artifact = selector.export() | {
        "development_protocol_id": protocol_id,
        "strongest_fixed": strongest_fixed,
        "training_rows": len(feature_rows),
        "excluded_ood_scenario": "S13",
    }
    artifact_path = root / "artifacts" / "aware" / "selector_development.json"
    atomic_write_json(artifact_path, selector_artifact)
    frame = pd.DataFrame(rows)
    evidence_path = root / "evidence" / "development" / "fact_estimator_result.parquet"
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(evidence_path, index=False)
    return {
        "selector_artifact": str(artifact_path.relative_to(root)),
        "selector_hash": canonical_hash(selector_artifact),
        "strongest_fixed": strongest_fixed,
        "method_rmse": dict(zip(method_rmse.method_id, method_rmse.rmse, strict=True)),
        "worlds": worlds,
    }


def run_null(root: Path, config: ExperimentConfig, protocol_id: str) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for index in range(config.worlds.null_calibration):
        world_id = f"NULL-{index:05d}"
        world, truth = generate_world(
            seed=_seed(config.seed, 8, index),
            world_id=world_id,
            scenario_id="S00",
            effect_scale=0.0,
        )
        for method_id, estimate in estimate_all(world).items():
            rows.append(
                _estimator_row(
                    protocol_id=protocol_id,
                    phase="E08",
                    scenario="S00",
                    world_id=world_id,
                    truth=truth,
                    estimate=estimate,
                    diagnostics=diagnostic_features(world, method_id),
                )
            )
    frame = pd.DataFrame(rows)
    path = root / "evidence" / "qualification" / "fact_null_result.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(path, index=False)
    rates = frame.groupby("method_id")["reject_null"].mean().to_dict()
    return {"worlds": config.worlds.null_calibration, "type_i_rate": rates}


def _bootstrap_ci(values: np.ndarray, seed: int) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(values), size=(2000, len(values)))
    means = values[indices].mean(axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def run_final(
    root: Path,
    config: ExperimentConfig,
    protocol_id: str,
    selector_artifact: dict[str, Any],
) -> dict[str, Any]:
    selector = AwareSelector.restore(selector_artifact)
    fixed_method = str(selector_artifact["strongest_fixed"])
    estimator_rows: list[dict[str, Any]] = []
    selector_rows: list[dict[str, Any]] = []
    truth_access: list[dict[str, str]] = []
    scenarios = ["S00"] * 3 + [f"S{i:02d}" for i in range(1, 14)]

    for index in range(config.worlds.final):
        scenario = scenarios[index % len(scenarios)]
        world_id = f"FINAL-{index:05d}"
        effect_scale = (0.0, 0.025, 0.05, 0.075)[index % 4]
        # Truth remains in a separate object and is not passed to diagnostics,
        # eligibility, selector, or estimators.
        world, hidden_truth = generate_world(
            seed=_seed(config.seed, 14, index),
            world_id=world_id,
            scenario_id=scenario,
            effect_scale=effect_scale,
        )
        features_by_method = {
            method: diagnostic_features(world, method) for method in METHODS
        }
        selection = selector.select(features_by_method)
        committed_selection_hash = canonical_hash(
            asdict(selection) | {"world_id": world_id}
        )
        estimates = estimate_all(world)

        # Scoring boundary: first access occurs only after selection and all
        # estimator outputs are committed in memory.
        truth_access.append(
            {
                "world_id": world_id,
                "world_identity_hash": canonical_hash(
                    {
                        "protocol": protocol_id,
                        "world": world_id,
                        "seed": _seed(config.seed, 14, index),
                    }
                ),
                "first_access_timestamp": utc_now(),
                "accessing_stage": "E14_CANONICAL_SCORING",
                "protocol_id": protocol_id,
                "committed_selection_hash": committed_selection_hash,
            }
        )
        truth = hidden_truth
        materiality = max(
            float(world.outcomes[:, : config.pre_days].sum() * 0.005), 1.0
        )
        selected_estimate = (
            None if selection.abstained else estimates[selection.selected_method or ""]
        )
        aware_decision = decide(
            selected_estimate, truth.itt_total, materiality=materiality
        )
        fixed_decision = decide(
            estimates[fixed_method], truth.itt_total, materiality=materiality
        )
        for method_id, estimate in estimates.items():
            estimator_rows.append(
                _estimator_row(
                    protocol_id=protocol_id,
                    phase="E14",
                    scenario=scenario,
                    world_id=world_id,
                    truth=truth,
                    estimate=estimate,
                    diagnostics=features_by_method[method_id],
                )
            )
        selected_error = (
            math.nan
            if selected_estimate is None
            else selected_estimate.estimate - truth.itt_total
        )
        selector_rows.append(
            {
                "protocol_id": protocol_id,
                "evidence_class": "SIMULATED",
                "phase": "E14",
                "world_id": world_id,
                "scenario_id": scenario,
                "selector_id": "P1_AWARE_SELECT",
                "selected_method": selection.selected_method,
                "eligible_methods": list(selection.eligible_methods),
                "predicted_risk": selection.predicted_risk,
                "abstained": selection.abstained,
                "true_effect": truth.itt_total,
                "estimate": None
                if selected_estimate is None
                else selected_estimate.estimate,
                "sq_error": None if selected_estimate is None else selected_error**2,
                "covered_truth": None
                if selected_estimate is None
                else selected_estimate.ci_low
                <= truth.itt_total
                <= selected_estimate.ci_high,
                "reject_null": None
                if selected_estimate is None
                else selected_estimate.p_value < 0.05,
                "sign_correct": None
                if selected_estimate is None
                else truth.itt_total == 0
                or np.sign(selected_estimate.estimate) == np.sign(truth.itt_total),
                "decision": aware_decision.decision,
                "oracle_decision": aware_decision.oracle_decision,
                "decision_regret": aware_decision.regret,
                "false_launch": aware_decision.false_launch,
                "false_stop": aware_decision.false_stop,
                "fixed_method": fixed_method,
                "fixed_sq_error": (estimates[fixed_method].estimate - truth.itt_total)
                ** 2,
                "fixed_decision_regret": fixed_decision.regret,
            }
        )

    estimator_frame = pd.DataFrame(estimator_rows)
    selector_frame = pd.DataFrame(selector_rows)
    final_root = root / "evidence" / "final"
    final_root.mkdir(parents=True, exist_ok=True)
    estimator_frame.to_parquet(
        final_root / "fact_estimator_result.parquet", index=False
    )
    selector_frame.to_parquet(final_root / "fact_selector_result.parquet", index=False)
    atomic_write_json(final_root / "truth_access_ledger.json", truth_access)

    non_abstained = selector_frame.loc[~selector_frame.abstained].copy()
    clean = non_abstained.loc[non_abstained.scenario_id == "S00"]
    aware_rmse = float(np.sqrt(clean.sq_error.mean()))
    fixed_rmse = float(np.sqrt(clean.fixed_sq_error.mean()))
    h1_ratio = aware_rmse / max(fixed_rmse, 1e-12)
    stress = selector_frame.loc[selector_frame.scenario_id != "S00"]
    paired_regret = (stress.decision_regret - stress.fixed_decision_regret).to_numpy(
        float
    )
    h2_ci = _bootstrap_ci(paired_regret, config.seed + 18)
    null_selected = non_abstained.loc[non_abstained.true_effect == 0]
    metrics: dict[str, Any] = {
        "protocol_id": protocol_id,
        "worlds": config.worlds.final,
        "strongest_fixed": fixed_method,
        "selection_frequency": dict(Counter(selector_frame.selected_method.dropna())),
        "abstention_rate": float(selector_frame.abstained.mean()),
        "clean_abstention_rate": float(
            selector_frame.loc[selector_frame.scenario_id == "S00", "abstained"].mean()
        ),
        "selection_aware_coverage": float(non_abstained.covered_truth.mean()),
        "selection_aware_null_type_i": float(null_selected.reject_null.mean()),
        "false_launch_rate": float(selector_frame.false_launch.mean()),
        "false_stop_rate": float(selector_frame.false_stop.mean()),
        "aware_mean_regret": float(selector_frame.decision_regret.mean()),
        "fixed_mean_regret": float(selector_frame.fixed_decision_regret.mean()),
        "h1": {
            "aware_clean_rmse": aware_rmse,
            "fixed_clean_rmse": fixed_rmse,
            "ratio": h1_ratio,
            "margin": 1.05,
            "pass": h1_ratio <= 1.05,
        },
        "h2": {
            "mean_paired_regret_difference": float(paired_regret.mean()),
            "ci_low": h2_ci[0],
            "ci_high": h2_ci[1],
            "pass": h2_ci[1] < 0,
        },
    }
    critical: dict[str, bool] = {
        "null_type_i": metrics["selection_aware_null_type_i"] <= 0.075,
        "coverage": metrics["selection_aware_coverage"] >= 0.90,
        "clean_abstention": metrics["clean_abstention_rate"] <= 0.10,
        "truth_ledger_complete": len(truth_access) == config.worlds.final,
    }
    metrics["critical_gates"] = critical
    h1_pass = bool(h1_ratio <= 1.05)
    h2_pass = bool(h2_ci[1] < 0)
    metrics["promotion_eligible"] = h1_pass and h2_pass and all(critical.values())
    atomic_write_json(final_root / "confirmatory_metrics.json", metrics)
    return metrics
