"""Post-final AWARE ablations scored on the frozen protected worlds."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from geocausal.aware import AwareSelector
from geocausal.aware.selector import FEATURES
from geocausal.config import ExperimentConfig
from geocausal.decision import decide
from geocausal.diagnostics import diagnostic_features
from geocausal.estimators import Estimate, estimate_all
from geocausal.simulation.benchmark import METHODS
from geocausal.simulation.protected import _load_world

ABLATIONS: dict[str, tuple[str, ...]] = {
    "A0_full_aware": (),
    "A1_no_placebo": ("placebo_bias", "placebo_fpr"),
    "A2_no_coverage": ("placebo_coverage",),
    "A3_no_prefit_r2": ("pre_r2", "pre_rmse"),
    "A4_no_trend": ("trend_gap",),
    "A5_no_autocorrelation": ("acf_score",),
    "A6_no_donor_concentration": ("donor_hhi", "effective_donors"),
    "A7_no_delivery_diagnostic": (),
    "A8_no_carryover_diagnostic": (),
    "A9_no_abstention": (),
    "A10_soft_blend": (),
    "A11_equal_weight_blend": (),
    "A12_boosted_nonlinear": (),
    "A13_half_placebo_budget": ("placebo_bias",),
}


def _blend(estimates: list[Estimate], weights: np.ndarray, method: str) -> Estimate:
    weights = weights / weights.sum()
    estimate = float(np.dot(weights, [item.estimate for item in estimates]))
    standard_error = float(
        np.sqrt(np.dot(weights**2, [item.standard_error**2 for item in estimates]))
    )
    return Estimate(
        method_id=method,
        estimate=estimate,
        standard_error=standard_error,
        ci_low=estimate - 1.96 * standard_error,
        ci_high=estimate + 1.96 * standard_error,
        p_value=float("nan"),
    )


def run_ablations(
    root: Path,
    config: ExperimentConfig,
    protocol_id: str,
    selector_artifact: dict[str, Any],
) -> dict[str, Any]:
    selector = AwareSelector.restore(selector_artifact)
    development = pd.read_parquet(
        root / "evidence" / "development" / "fact_estimator_result.parquet"
    )
    medians = {feature: float(development[feature].median()) for feature in FEATURES}
    import xgboost as xgb

    boosted = xgb.XGBRegressor(
        n_estimators=64,
        max_depth=3,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        tree_method="hist",
        device="cuda",
        random_state=20260909,
    )
    boosted_matrix = development.loc[:, FEATURES].to_numpy(float)
    boosted_target = np.minimum(
        development.abs_error.to_numpy(float)
        / np.maximum(np.abs(development.true_effect.to_numpy(float)), 1.0),
        4.0,
    )
    boosted_started = time.perf_counter()
    boosted.fit(boosted_matrix, boosted_target)
    boosted_runtime = time.perf_counter() - boosted_started
    generation = json.loads(
        (root / "artifacts" / "final_committed" / "generation.json").read_text()
    )
    committed = pd.read_parquet(
        root / "artifacts" / "final_committed" / "selections.parquet"
    ).set_index("world_id")
    rows: list[dict[str, Any]] = []
    observed_root = root / "data" / "protected" / "final" / "observed"
    truth_root = root / "data" / "protected" / "final" / "truth"
    for item in generation["world_index"]:
        world = _load_world(observed_root / f"{item['world_id']}.npz", item, config)
        estimates = estimate_all(world)
        base_features = {
            method: diagnostic_features(world, method) for method in METHODS
        }
        with np.load(truth_root / f"{world.world_id}.npz") as truth:
            true_effect = float(truth["itt_total"])
        materiality_value: Any = committed.at[world.world_id, "materiality"]
        materiality = float(materiality_value)
        for ablation, removed in ABLATIONS.items():
            modified = {
                method: {
                    feature: (medians[feature] if feature in removed else value)
                    for feature, value in features.items()
                }
                for method, features in base_features.items()
            }
            selection = selector.select(modified)
            selected: Estimate | None
            if ablation == "A12_boosted_nonlinear":
                eligible = [
                    method
                    for method in METHODS
                    if selector.eligible(method, modified[method])
                ]
                if eligible:
                    matrix = np.asarray(
                        [
                            [modified[method][name] for name in FEATURES]
                            for method in eligible
                        ]
                    )
                    boosted_risks = boosted.predict(matrix)
                    best = int(np.argmin(boosted_risks))
                    selected = (
                        None
                        if float(boosted_risks[best]) > selector.risk_limit
                        else estimates[eligible[best]]
                    )
                else:
                    selected = None
            elif ablation == "A9_no_abstention" and selection.abstained:
                selected = estimates[str(selector_artifact["strongest_fixed"])]
            elif ablation in {"A10_soft_blend", "A11_equal_weight_blend"}:
                eligible = list(selection.eligible_methods) or [
                    str(selector_artifact["strongest_fixed"])
                ]
                candidates = [estimates[method] for method in eligible]
                if ablation == "A10_soft_blend":
                    matrix = np.asarray(
                        [
                            [modified[method][name] for name in FEATURES]
                            for method in eligible
                        ]
                    )
                    risks = np.maximum(selector.model.predict(matrix), 0)
                    weights = np.exp(-risks)
                else:
                    weights = np.ones(len(candidates))
                selected = _blend(candidates, weights, ablation)
            elif selection.abstained:
                selected = None
            else:
                selected = estimates[selection.selected_method or ""]
            result = decide(selected, true_effect, materiality=materiality)
            rows.append(
                {
                    "protocol_id": protocol_id,
                    "world_id": world.world_id,
                    "scenario_id": world.scenario_id,
                    "ablation_id": ablation,
                    "selected_method": None if selected is None else selected.method_id,
                    "abstained": selected is None,
                    "true_effect": true_effect,
                    "estimate": None if selected is None else selected.estimate,
                    "sq_error": None
                    if selected is None
                    else (selected.estimate - true_effect) ** 2,
                    "covered_truth": None
                    if selected is None
                    else selected.ci_low <= true_effect <= selected.ci_high,
                    "decision_regret": result.regret,
                    "false_launch": result.false_launch,
                    "false_stop": result.false_stop,
                    "uncertainty_status": "EXPLORATORY"
                    if "blend" in ablation
                    else "EMPIRICAL_PROCEDURE",
                }
            )
    frame = pd.DataFrame(rows)
    output = root / "evidence" / "post_final" / "fact_ablation_result.parquet"
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(output, index=False)
    summary = (
        frame.groupby("ablation_id")
        .agg(
            abstention_rate=("abstained", "mean"),
            mean_regret=("decision_regret", "mean"),
            false_launch_rate=("false_launch", "mean"),
            coverage=("covered_truth", "mean"),
        )
        .reset_index()
    )
    summary.to_parquet(
        root / "evidence" / "post_final" / "ablation_summary.parquet", index=False
    )
    runtime = {
        "workload": "A12_XGBoost_reliability_model",
        "device": "cuda",
        "training_rows": len(development),
        "runtime_sec": boosted_runtime,
        "n_estimators": 64,
    }
    (root / "evidence" / "runtime" / "e15_xgboost_gpu.json").write_text(
        json.dumps(runtime, indent=2, sort_keys=True), encoding="utf-8"
    )
    return {
        "rows": len(frame),
        "boosted_gpu": runtime,
        "summary": summary.to_dict(orient="records"),
    }
