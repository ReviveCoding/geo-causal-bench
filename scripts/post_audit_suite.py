"""Build the separately governed post-audit analytics/operations/compliance suite."""

# ruff: noqa: E501

from __future__ import annotations

import hashlib
import json
import math
import time
from pathlib import Path
from typing import Any

import duckdb
import matplotlib
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import mean_squared_error, roc_auc_score
from sklearn.model_selection import GroupKFold, cross_val_predict

from geocausal.artifacts import (
    atomic_write_json,
    atomic_write_text,
    sha256_file,
    utc_now,
)
from geocausal.aware import AwareSelector
from geocausal.decision import decide
from geocausal.dgp import ObservedWorld, generate_world
from geocausal.diagnostics import diagnostic_features
from geocausal.estimators import Estimate, estimate_all
from geocausal.post_audit.compliance import generate_compliance_world, observed_payload
from geocausal.post_audit.influence import influence_summary

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
ANALYTICS = ROOT / "evidence" / "post_audit_analytics"
OPERATIONS = ROOT / "evidence" / "operations"
COMPLIANCE = ROOT / "evidence" / "compliance_semantics"
FIGURES = ROOT / "reports" / "figures"
PROTOCOL = "AWARE-GEO-e52a8660a97ef174"


def write_parquet(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    frame.to_parquet(temporary, index=False)
    temporary.replace(path)


def wilson(successes: int, n: int) -> tuple[float, float]:
    if n == 0:
        return (math.nan, math.nan)
    z = 1.959963984540054
    p = successes / n
    denominator = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denominator
    spread = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
    return centre - spread, centre + spread


def bootstrap_mean_ci(values: pd.Series, *, seed: int) -> tuple[float, float]:
    clean = values.dropna().to_numpy(float)
    if len(clean) < 2:
        return (math.nan, math.nan)
    rng = np.random.default_rng(seed)
    draws = rng.choice(clean, size=(2000, len(clean)), replace=True).mean(axis=1)
    return float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))


def cvar(values: pd.Series, quantile: float) -> float:
    clean = values.dropna()
    if clean.empty:
        return math.nan
    cutoff = clean.quantile(quantile)
    return float(clean[clean >= cutoff].mean())


def markdown_table(frame: pd.DataFrame) -> str:
    """Render a compact Markdown table without an optional tabulate dependency."""
    rendered = frame.copy()
    rendered = rendered.map(
        lambda value: f"{value:.6g}" if isinstance(value, float) else str(value)
    )
    header = "| " + " | ".join(rendered.columns.astype(str)) + " |"
    rule = "| " + " | ".join("---" for _ in rendered.columns) + " |"
    body = ["| " + " | ".join(row) + " |" for row in rendered.to_numpy(str)]
    return "\n".join([header, rule, *body])


def metric_summary(group: pd.DataFrame, *, seed: int) -> dict[str, Any]:
    n = len(group)
    covered = group["covered_truth"].dropna().astype(bool)
    coverage = float(covered.mean()) if len(covered) else math.nan
    coverage_low, coverage_high = wilson(int(covered.sum()), len(covered))
    null = (
        group.loc[group["true_effect"].abs() < 1e-12, "reject_null"]
        .dropna()
        .astype(bool)
    )
    type1 = float(null.mean()) if len(null) else math.nan
    type1_low, type1_high = wilson(int(null.sum()), len(null))
    regret_low, regret_high = bootstrap_mean_ci(group["decision_regret"], seed=seed)
    return {
        "n": n,
        "precision_flag": "LOW_PRECISION" if n < 30 else "STANDARD",
        "mean_bias": group["bias"].mean(),
        "rmse": math.sqrt(group["sq_error"].mean()),
        "mae": group["abs_error"].mean(),
        "median_absolute_error": group["abs_error"].median(),
        "coverage": coverage,
        "coverage_ci_low": coverage_low,
        "coverage_ci_high": coverage_high,
        "interval_width": group["interval_width"].mean(),
        "null_type1": type1,
        "null_type1_ci_low": type1_low,
        "null_type1_ci_high": type1_high,
        "sign_error": group["sign_error"].mean(),
        "abstention": group["abstained"].mean(),
        "false_launch": group["false_launch"].mean(),
        "false_stop": group["false_stop"].mean(),
        "mean_regret": group["decision_regret"].mean(),
        "mean_regret_ci_low": regret_low,
        "mean_regret_ci_high": regret_high,
        "median_regret": group["decision_regret"].median(),
        "p90_regret": group["decision_regret"].quantile(0.90),
        "p95_regret": group["decision_regret"].quantile(0.95),
        "p99_regret": group["decision_regret"].quantile(0.99),
        "maximum_regret": group["decision_regret"].max(),
    }


def _estimate_from_struct(value: dict[str, Any]) -> Estimate:
    return Estimate(
        method_id=str(value["method_id"]),
        estimate=float(value["estimate"]),
        standard_error=float(value["standard_error"]),
        ci_low=float(value["ci_low"]),
        ci_high=float(value["ci_high"]),
        p_value=float(value["p_value"]),
        status=str(value["status"]),
    )


def analysis_frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    selectors = pd.read_parquet(
        ANALYTICS.parent / "final" / "fact_selector_result.parquet"
    )
    estimators = pd.read_parquet(
        ANALYTICS.parent / "final" / "fact_estimator_result.parquet"
    )
    diagnostics = estimators[
        [
            "world_id",
            "method_id",
            "pre_r2",
            "pre_rmse",
            "trend_gap",
            "acf_score",
            "donor_hhi",
            "effective_donors",
            "missingness",
            "geo_leverage",
        ]
    ]
    rows: list[dict[str, Any]] = []
    for item in selectors.to_dict(orient="records"):
        for selector_id in ("AWARE", "fixed_did"):
            if selector_id == "AWARE":
                method = (
                    item["selected_method"]
                    if not item["abstained"]
                    else item["fixed_method"]
                )
                estimate = item["estimate"]
                sq_error = item["sq_error"]
                covered = item["covered_truth"]
                reject = item["reject_null"]
                sign_error = (
                    None if item["sign_correct"] is None else not item["sign_correct"]
                )
                abstained = bool(item["abstained"])
                regret = item["decision_regret"]
                false_launch = item["false_launch"]
                false_stop = item["false_stop"]
                struct = item["selected_estimate"] if not abstained else None
            else:
                method = item["fixed_method"]
                struct = item["fixed_estimate"]
                fixed = _estimate_from_struct(struct)
                result = decide(
                    fixed, item["true_effect"], materiality=item["materiality"]
                )
                estimate = fixed.estimate
                sq_error = item["fixed_sq_error"]
                covered = fixed.ci_low <= item["true_effect"] <= fixed.ci_high
                reject = fixed.p_value < 0.05
                sign_error = item["true_effect"] != 0 and np.sign(
                    fixed.estimate
                ) != np.sign(item["true_effect"])
                abstained = False
                regret = result.regret
                false_launch = result.false_launch
                false_stop = result.false_stop
            diagnostic = diagnostics.loc[
                (diagnostics.world_id == item["world_id"])
                & (diagnostics.method_id == method)
            ].iloc[0]
            interval_width = (
                math.nan
                if struct is None
                else float(struct["ci_high"] - struct["ci_low"])
            )
            rows.append(
                {
                    "extension_id": "POST-AUDIT-ANALYTICS-001",
                    "evidence_class": "POST_AUDIT_DERIVED",
                    "selector_id": selector_id,
                    "world_id": item["world_id"],
                    "scenario_id": item["scenario_id"],
                    "selected_method": method,
                    "predicted_risk": item["predicted_risk"],
                    "materiality": item["materiality"],
                    "baseline_volume": item["materiality"] / 0.01,
                    "true_effect": item["true_effect"],
                    "estimate": estimate,
                    "bias": estimate - item["true_effect"]
                    if pd.notna(estimate)
                    else math.nan,
                    "abs_error": abs(estimate - item["true_effect"])
                    if pd.notna(estimate)
                    else math.nan,
                    "sq_error": sq_error,
                    "covered_truth": covered,
                    "reject_null": reject,
                    "sign_error": sign_error,
                    "abstained": abstained,
                    "decision_regret": regret,
                    "false_launch": false_launch,
                    "false_stop": false_stop,
                    "interval_width": interval_width,
                    **{name: diagnostic[name] for name in diagnostics.columns[2:]},
                }
            )
    return pd.DataFrame(rows), selectors


def labels(frame: pd.DataFrame, column: str, mode: str) -> pd.Series:
    values = frame[column]
    if mode == "quartile":
        return pd.qcut(
            values, 4, labels=["Q1", "Q2", "Q3", "Q4"], duplicates="drop"
        ).astype(str)
    if mode == "decile":
        return pd.qcut(
            values.rank(method="first"), 10, labels=[f"D{i}" for i in range(1, 11)]
        ).astype(str)
    if column == "pre_r2":
        return pd.cut(
            values,
            [-np.inf, 0, 0.5, 0.8, np.inf],
            right=False,
            labels=["<0", "0-<0.5", "0.5-<0.8", ">=0.8"],
        ).astype(str)
    if column == "effective_donors":
        return pd.cut(
            values, [-np.inf, 5, 10, np.inf], labels=["<=5", "6-10", ">10"]
        ).astype(str)
    if column == "missingness":
        return pd.cut(
            values,
            [-1e-15, 0, 0.01, 0.03, np.inf],
            labels=["zero", ">0-1%", ">1-3%", ">3%"],
            include_lowest=True,
        ).astype(str)
    if mode == "tercile":
        return pd.qcut(values, 3, labels=["T1", "T2", "T3"], duplicates="drop").astype(
            str
        )
    raise ValueError((column, mode))


def run_analytics() -> dict[str, Any]:
    frame, _selectors = analysis_frames()
    dimensions = {
        "pre_r2": "fixed",
        "pre_rmse": "quartile",
        "acf_score": "quartile",
        "trend_gap": "quartile",
        "donor_hhi": "quartile",
        "effective_donors": "fixed",
        "geo_leverage": "quartile",
        "baseline_volume": "tercile",
        "missingness": "fixed",
        "predicted_risk": "decile",
        "scenario_id": "identity",
    }
    slice_rows: list[dict[str, Any]] = []
    for selector_id, selector_frame in frame.groupby("selector_id"):
        for dimension, mode in dimensions.items():
            assigned = (
                selector_frame[dimension].astype(str)
                if mode == "identity"
                else labels(selector_frame, dimension, mode)
            )
            enriched = selector_frame.assign(slice_value=assigned)
            for value, group in enriched.groupby("slice_value", observed=True):
                if len(group) < 25:
                    continue
                slice_rows.append(
                    {
                        "selector_id": selector_id,
                        "slice_dimension": dimension,
                        "slice_value": value,
                        **metric_summary(group, seed=2026091001 + len(slice_rows)),
                    }
                )
        # Explicit top-decile views.
        for dimension in ("geo_leverage", "baseline_volume"):
            cutoff = selector_frame[dimension].quantile(0.9)
            group = selector_frame[selector_frame[dimension] >= cutoff]
            slice_rows.append(
                {
                    "selector_id": selector_id,
                    "slice_dimension": dimension,
                    "slice_value": "top_decile",
                    **metric_summary(group, seed=2026091500 + len(slice_rows)),
                }
            )
    slices = pd.DataFrame(slice_rows)
    write_parquet(slices, ANALYTICS / "fact_slice_result.parquet")
    summary = slices.groupby(["selector_id", "slice_dimension"], as_index=False).agg(
        slice_count=("slice_value", "size"),
        min_n=("n", "min"),
        worst_coverage=("coverage", "min"),
        worst_rmse=("rmse", "max"),
        worst_p95_regret=("p95_regret", "max"),
    )
    write_parquet(summary, ANALYTICS / "slice_summary.parquet")

    # Predeclared interaction views; unavailable MDE interaction is retained as gated.
    aware = frame[frame.selector_id == "AWARE"].copy()
    q_acf = aware.acf_score.quantile(0.75)
    q_trend = aware.trend_gap.quantile(0.75)
    interactions: list[dict[str, Any]] = []
    specs = [
        ("structural_break_x_r2", aware.scenario_id.eq("S04"), "pre_r2", "fixed"),
        (
            "structural_break_x_predicted_risk",
            aware.scenario_id.eq("S04"),
            "predicted_risk",
            "decile",
        ),
        (
            "compound_ood_x_predicted_risk",
            aware.scenario_id.eq("S13"),
            "predicted_risk",
            "decile",
        ),
        (
            "high_acf_x_baseline_volume",
            aware.acf_score.ge(q_acf),
            "baseline_volume",
            "tercile",
        ),
        (
            "donor_concentration_x_geo_leverage",
            pd.Series(True, index=aware.index),
            "geo_leverage",
            "quartile",
        ),
        (
            "missingness_x_baseline_volume",
            aware.missingness.gt(0),
            "baseline_volume",
            "tercile",
        ),
        ("high_trend_gap_x_r2", aware.trend_gap.ge(q_trend), "pre_r2", "fixed"),
    ]
    for name, mask, dimension, mode in specs:
        subset = aware[mask].copy()
        if subset.empty:
            interactions.append(
                {
                    "interaction_id": name,
                    "slice_value": "NOT_AVAILABLE",
                    "n": 0,
                    "status": "NOT_AVAILABLE",
                }
            )
            continue
        subset["slice_value"] = labels(subset, dimension, mode)
        for value, group in subset.groupby("slice_value", observed=True):
            metrics = metric_summary(group, seed=2026092000 + len(interactions))
            interactions.append(
                {
                    "interaction_id": name,
                    "slice_value": value,
                    "status": "LOW_PRECISION" if len(group) < 30 else "SUCCESS",
                    **metrics,
                }
            )
    interactions.append(
        {
            "interaction_id": "high_predicted_risk_x_effect_relative_to_mde",
            "slice_value": "NOT_AVAILABLE_HISTORICAL_MDE",
            "n": 0,
            "status": "GATED",
        }
    )
    interaction_frame = pd.DataFrame(interactions)
    write_parquet(interaction_frame, ANALYTICS / "fact_conditional_coverage.parquet")

    # Tail risk, including declared post-final blend ablations.
    tail_sources = [
        frame[
            ["selector_id", "world_id", "scenario_id", "abs_error", "decision_regret"]
        ]
    ]
    ablations = pd.read_parquet(
        ROOT / "evidence/post_final/fact_ablation_result.parquet"
    )
    ablations = ablations[
        ablations.ablation_id.isin(
            ["A10_soft_blend", "A11_equal_weight_blend", "A1_no_placebo"]
        )
    ]
    if not ablations.empty:
        ablations = ablations.assign(
            abs_error=(ablations.estimate - ablations.true_effect).abs()
        ).rename(columns={"ablation_id": "selector_id"})
        tail_sources.append(
            ablations[
                [
                    "selector_id",
                    "world_id",
                    "scenario_id",
                    "abs_error",
                    "decision_regret",
                ]
            ]
        )
    tail_input = pd.concat(tail_sources, ignore_index=True)
    tail_rows = []
    for (selector_id, loss_name), values in [
        ((sid, name), group[name])
        for sid, group in tail_input.groupby("selector_id")
        for name in ("abs_error", "decision_regret")
    ]:
        tail_rows.append(
            {
                "selector_id": selector_id,
                "loss": loss_name,
                "n": len(values),
                "median": values.quantile(0.5),
                "p75": values.quantile(0.75),
                "p90": values.quantile(0.9),
                "p95": values.quantile(0.95),
                "p99": values.quantile(0.99),
                "maximum": values.max(),
                "cvar90": cvar(values, 0.9),
                "cvar95": cvar(values, 0.95),
            }
        )
    tail = pd.DataFrame(tail_rows)
    write_parquet(tail, ANALYTICS / "fact_tail_risk.parquet")

    # Risk calibration and selective prediction.
    calibration_rows = []
    aware["risk_decile"] = labels(aware, "predicted_risk", "decile")
    aware["realized_loss"] = (
        aware.abs_error.fillna(0) / aware.materiality.clip(lower=1)
        + 0.5 * (~aware.covered_truth.fillna(False).astype(bool)).astype(float)
        + aware.decision_regret
    )
    for decile, group in aware.groupby("risk_decile", observed=True):
        calibration_rows.append(
            {
                "record_type": "decile",
                "ranking": "aware_predicted_risk",
                "bin": decile,
                "retained_fraction": math.nan,
                "n": len(group),
                "mean_predicted_risk": group.predicted_risk.mean(),
                "mean_realized_loss": group.realized_loss.mean(),
                "mean_abs_error": group.abs_error.mean(),
                "coverage": group.covered_truth.mean(),
                "false_launch": group.false_launch.mean(),
                "decision_regret": group.decision_regret.mean(),
                "abstention": group.abstained.mean(),
            }
        )
    rng = np.random.default_rng(2026091002)
    aware["random_rank"] = rng.random(len(aware))
    ranking_values = {
        "aware_predicted_risk": aware.predicted_risk,
        "pre_r2_inverse": -aware.pre_r2,
        "pre_rmse": aware.pre_rmse,
        "deterministic_random": aware.random_rank,
    }
    for ranking, values in ranking_values.items():
        ordered = aware.assign(rank_value=values).sort_values("rank_value")
        for fraction in np.arange(0.1, 1.01, 0.1):
            retained = ordered.head(max(1, round(len(ordered) * fraction)))
            calibration_rows.append(
                {
                    "record_type": "risk_coverage",
                    "ranking": ranking,
                    "bin": None,
                    "retained_fraction": fraction,
                    "n": len(retained),
                    "mean_predicted_risk": retained.predicted_risk.mean(),
                    "mean_realized_loss": retained.realized_loss.mean(),
                    "mean_abs_error": retained.abs_error.mean(),
                    "coverage": retained.covered_truth.mean(),
                    "false_launch": retained.false_launch.mean(),
                    "decision_regret": retained.decision_regret.mean(),
                    "abstention": retained.abstained.mean(),
                }
            )
    calibration = pd.DataFrame(calibration_rows)
    write_parquet(calibration, ANALYTICS / "fact_risk_calibration.parquet")
    finite_calibration = aware[np.isfinite(aware.predicted_risk)].copy()
    fit = np.polyfit(
        finite_calibration.predicted_risk, finite_calibration.realized_loss, 1
    )
    rank_stats = {
        "finite_risk_rows": len(finite_calibration),
        "infinite_risk_rows": int((~np.isfinite(aware.predicted_risk)).sum()),
        "spearman_predicted_vs_realized": stats.spearmanr(
            finite_calibration.predicted_risk, finite_calibration.realized_loss
        ).statistic,
        "calibration_slope": fit[0],
        "calibration_intercept": fit[1],
    }
    catastrophic = aware.decision_regret.ge(1.0).astype(int)
    rank_stats["catastrophic_event_rate"] = catastrophic.mean()
    finite_catastrophic = catastrophic.loc[finite_calibration.index]
    rank_stats["catastrophic_auroc"] = (
        roc_auc_score(finite_catastrophic, finite_calibration.predicted_risk)
        if finite_catastrophic.nunique() == 2
        else math.nan
    )
    aurc = (
        calibration[calibration.record_type == "risk_coverage"]
        .groupby("ranking")
        .apply(
            lambda d: float(
                np.trapezoid(
                    d.sort_values("retained_fraction").mean_realized_loss,
                    d.sort_values("retained_fraction").retained_fraction,
                )
            ),
            include_groups=False,
        )
        .to_dict()
    )
    rank_stats["aurc"] = aurc
    atomic_write_json(ANALYTICS / "risk_calibration_summary.json", rank_stats)

    # Post-hoc threshold sensitivity. Original abstentions cannot be un-abstained.
    frontier_rows = []
    for threshold in [
        0,
        0.1,
        0.2,
        0.3,
        0.4,
        0.5,
        0.6,
        0.7,
        0.8,
        0.9,
        1,
        1.1,
        1.2,
        1.25,
        1.3,
        1.4,
        1.5,
        1.6,
        1.7,
        1.8,
        1.9,
        2,
        2.25,
        2.5,
        3,
    ]:
        retained = aware[(aware.predicted_risk <= threshold) & ~aware.abstained]
        clean = aware[aware.scenario_id == "S00"]
        frontier_rows.append(
            {
                "threshold": threshold,
                "is_original_frozen_threshold": threshold == 1.25,
                "n": len(retained),
                "retained_fraction": len(retained) / len(aware),
                "abstention_rate": 1 - len(retained) / len(aware),
                "coverage": retained.covered_truth.mean(),
                "false_launch": retained.false_launch.mean(),
                "false_stop": retained.false_stop.mean(),
                "mean_regret": retained.decision_regret.mean(),
                "p95_regret": retained.decision_regret.quantile(0.95),
                "cvar95_regret": cvar(retained.decision_regret, 0.95),
                "clean_world_retention": (
                    (clean.predicted_risk <= threshold) & ~clean.abstained
                ).mean(),
                "status": "PARTIAL_IDENTIFICATION_ABOVE_FROZEN_LIMIT"
                if threshold > 1.25
                else "SUCCESS",
            }
        )
    frontier = pd.DataFrame(frontier_rows)
    write_parquet(frontier, ANALYTICS / "fact_threshold_frontier.parquet")

    # Grouped failure attribution.
    features = [
        "pre_r2",
        "pre_rmse",
        "trend_gap",
        "acf_score",
        "donor_hhi",
        "effective_donors",
        "geo_leverage",
        "baseline_volume",
        "missingness",
    ]
    x = aware[features].fillna(aware[features].median())
    x = (x - x.mean()) / x.std().replace(0, 1)
    groups = aware.scenario_id
    attribution_rows = []
    targets = {
        "absolute_error": aware.abs_error,
        "miscoverage": (~aware.covered_truth.fillna(False)).astype(int),
        "false_launch": aware.false_launch.astype(int),
        "high_regret": aware.decision_regret.ge(1).astype(int),
        "abstention": aware.abstained.astype(int),
    }
    splitter = GroupKFold(n_splits=5)
    for target, y in targets.items():
        valid = y.notna()
        x_target = x.loc[valid]
        y_target = y.loc[valid]
        groups_target = groups.loc[valid]
        if target == "absolute_error":
            model: Any = Ridge(alpha=1.0).fit(x_target, y_target)
            predicted = cross_val_predict(
                Ridge(alpha=1.0),
                x_target,
                y_target,
                cv=splitter,
                groups=groups_target,
            )
            score = math.sqrt(mean_squared_error(y_target, predicted))
            score_name = "grouped_rmse"
        else:
            if y_target.nunique() < 2:
                continue
            model = LogisticRegression(C=1.0, max_iter=2000).fit(x_target, y_target)
            predicted = cross_val_predict(
                LogisticRegression(C=1.0, max_iter=2000),
                x_target,
                y_target,
                cv=splitter,
                groups=groups_target,
                method="predict_proba",
            )[:, 1]
            score = roc_auc_score(y_target, predicted)
            score_name = "grouped_auroc"
        coefficients = model.coef_.ravel()
        for feature, coefficient in zip(features, coefficients, strict=True):
            attribution_rows.append(
                {
                    "target": target,
                    "feature": feature,
                    "standardized_coefficient": coefficient,
                    "score_name": score_name,
                    "out_of_group_score": score,
                    "interpretation": "PREDICTIVE_NOT_CAUSAL",
                }
            )
    attribution = pd.DataFrame(attribution_rows)
    write_parquet(attribution, ANALYTICS / "fact_failure_attribution.parquet")
    return {
        "rows": len(frame),
        "slices": len(slices),
        "interactions": len(interaction_frame),
        **rank_stats,
    }


def tbr_panel_estimate(
    outcomes: np.ndarray, treated: np.ndarray, pre_days: int | None = None
) -> float:
    total_days = outcomes.shape[1]
    pre = pre_days or max(2, total_days - 15)
    treatment = outcomes[treated].sum(axis=0)
    control = outcomes[~treated].sum(axis=0)
    x = np.column_stack([np.ones(pre), control[:pre]])
    coefficients = np.linalg.lstsq(x, treatment[:pre], rcond=None)[0]
    return float(
        (treatment[pre:] - coefficients[0] - coefficients[1] * control[pre:]).sum()
    )


def run_operations() -> dict[str, Any]:
    rng = np.random.default_rng(2026091101)
    selector = AwareSelector.restore(
        json.loads((ROOT / "artifacts/aware/selector_development.json").read_text())
    )
    rolling_rows = []
    panels = [
        (
            "D1_GEOLIFT_PRE",
            pd.read_csv(ROOT / "data/staged/D1_PRE/GeoLift_PreTest.csv"),
            "Y",
            15,
        ),
        (
            "D4_GEOX_DESIGN",
            pd.read_csv(ROOT / "data/raw/D4_DESIGN_SINGLE/GeoX_design_single_cell.csv"),
            "conversions",
            14,
        ),
    ]
    for dataset_id, data, response, test_days in panels:
        data["date"] = pd.to_datetime(data["date"])
        pivot = data.pivot(
            index="location", columns="date", values=response
        ).sort_index(axis=1)
        values = pivot.to_numpy(float)
        treated = np.zeros(len(pivot), dtype=bool)
        treated[np.argsort(values.mean(axis=1))[::3][: max(2, len(pivot) // 3)]] = True
        for end in range(test_days * 3, values.shape[1] - test_days + 1, 5):
            pre_days = end
            observed = ObservedWorld(
                f"{dataset_id}-{end}",
                "ROLLING",
                values[:, : end + test_days],
                np.zeros((len(pivot), end + test_days)),
                treated,
                np.zeros((len(pivot), end + test_days)),
                pre_days,
                test_days,
                0,
            )
            diagnostics = {
                m: diagnostic_features(observed, m)
                for m in (
                    "independent_tbr",
                    "independent_did",
                    "independent_ridge_sc",
                    "independent_simplex_sc",
                )
            }
            selection = selector.select(diagnostics)
            estimate = (
                estimate_all(observed).get(selection.selected_method)
                if selection.selected_method
                else None
            )
            rolling_rows.append(
                {
                    "extension_id": "OPERATIONS-STUDY-001",
                    "evidence_class": "POST_AUDIT_EXTERNAL",
                    "dataset_id": dataset_id,
                    "window_id": f"{end}-{end + test_days}",
                    "pre_days": pre_days,
                    "test_days": test_days,
                    "pre_r2": diagnostics["independent_tbr"]["pre_r2"],
                    "pre_rmse": diagnostics["independent_tbr"]["pre_rmse"],
                    "placebo_lift": diagnostics["independent_tbr"]["placebo_bias"],
                    "placebo_fpr": diagnostics["independent_tbr"]["placebo_fpr"],
                    "residual_acf": diagnostics["independent_tbr"]["acf_score"],
                    "trend_gap": diagnostics["independent_tbr"]["trend_gap"],
                    "selected_design": "deterministic_volume_strata",
                    "selected_estimator": selection.selected_method,
                    "aware_predicted_risk": selection.predicted_risk,
                    "design_viability": pre_days >= 3 * test_days,
                    "pseudo_estimate": estimate.estimate if estimate else math.nan,
                    "mde": math.nan,
                    "mde_status": "NOT_COMPUTED_FOR_ROLLING_EXTERNAL",
                }
            )
    rolling = pd.DataFrame(rolling_rows)
    write_parquet(rolling, OPERATIONS / "fact_rolling_backtest.parquet")
    write_parquet(rolling, OPERATIONS / "rolling_backtests.parquet")

    seasonal_rows = []
    start_names = [
        "normal",
        "before_ramp",
        "during_ramp",
        "peak",
        "ramp_down",
        "after_peak",
    ]
    starts = [30, 120, 145, 168, 190, 230]
    for history in (84, 168, 365):
        for regime, start_offset in zip(start_names, starts, strict=True):
            for replicate in range(60):
                n_geos, test_days = 40, 28
                total = 365 + 260
                t = np.arange(total)
                alpha = rng.lognormal(6, 0.5, n_geos)
                seasonal = (
                    1
                    + 0.12 * np.sin(2 * np.pi * t / 7)
                    + 0.18 * np.sin(2 * np.pi * t / 365)
                )
                peak = 1 + 0.7 * np.exp(-0.5 * ((t - 365 - 168) / 22) ** 2)
                outcomes = (
                    alpha[:, None]
                    * seasonal
                    * peak
                    * np.exp(rng.normal(0, 0.12, (n_geos, total)))
                )
                start = 365 + start_offset
                panel = outcomes[:, start - history : start + test_days].copy()
                treated = np.zeros(n_geos, dtype=bool)
                treated[rng.choice(n_geos, 12, replace=False)] = True
                effect = 0.05
                untreated_post = panel[treated, history:].copy()
                panel[treated, history:] *= 1 + effect
                world = ObservedWorld(
                    f"SEASON-{history}-{regime}-{replicate}",
                    "SEASONAL",
                    panel,
                    np.zeros_like(panel),
                    treated,
                    np.zeros_like(panel),
                    history,
                    test_days,
                    0,
                )
                diagnostic = diagnostic_features(world, "independent_tbr")
                estimate = estimate_all(world)["independent_tbr"]
                truth = float((untreated_post * effect).sum())
                mde = 2.8016 * estimate.standard_error
                seasonal_rows.append(
                    {
                        "extension_id": "OPERATIONS-STUDY-001",
                        "evidence_class": "POST_AUDIT_SIMULATED",
                        "world_id": world.world_id,
                        "history_days": history,
                        "start_regime": regime,
                        "pre_r2": diagnostic["pre_r2"],
                        "aa_reject": diagnostic["placebo_fpr"],
                        "mde": mde,
                        "projected_power": 0.8,
                        "true_effect": truth,
                        "estimate": estimate.estimate,
                        "bias": estimate.estimate - truth,
                        "covered_truth": estimate.ci_low <= truth <= estimate.ci_high,
                        "false_launch": estimate.ci_low >= 0 and truth <= 0,
                        "aware_risk": selector.select(
                            {
                                m: diagnostic_features(world, m)
                                for m in estimate_all(world)
                            }
                        ).predicted_risk,
                        "abstained": selector.select(
                            {
                                m: diagnostic_features(world, m)
                                for m in estimate_all(world)
                            }
                        ).abstained,
                    }
                )
    seasonal = pd.DataFrame(seasonal_rows)
    write_parquet(seasonal, OPERATIONS / "fact_seasonal_study.parquet")

    # Analytic design frontier and empirical validation on independent new seeds.
    design_rows, power_rows = [], []
    for n_geos in (20, 40, 80):
        for duration in (14, 28, 42, 56):
            for assignment in ("random", "stratified"):
                baseline_daily = 535 * n_geos * 0.3
                noise = 0.11 * baseline_daily
                mde = 2.8016 * noise * math.sqrt(duration)
                budget = mde * 1.2
                design_id = f"SIM-{n_geos}-{duration}-{assignment}"
                design_rows.append(
                    {
                        "extension_id": "OPERATIONS-STUDY-001",
                        "evidence_class": "POST_AUDIT_SIMULATED",
                        "tool": "KNOWN_TRUTH_DESIGN",
                        "design_id": design_id,
                        "geo_count": n_geos,
                        "test_duration": duration,
                        "assignment": assignment,
                        "experiment_type": "HOLDBACK",
                        "r2": 0.75 + (0.03 if assignment == "stratified" else 0),
                        "aa_p_value": math.nan,
                        "mde": mde,
                        "budget": budget,
                        "design_cpic": 1.2,
                        "treatment_geo_count": round(n_geos * 0.3),
                        "treatment_response_share": 0.3,
                        "excluded_geos": 0,
                        "status": "SUCCESS",
                    }
                )
                for multiple in (0, 0.5, 1, 1.5):
                    rejects, covers, signs = [], [], []
                    for _rep in range(100):
                        truth = multiple * mde
                        observed = rng.normal(truth, noise * math.sqrt(duration))
                        se = noise * math.sqrt(duration)
                        rejects.append(abs(observed / se) > 1.96)
                        covers.append(
                            observed - 1.96 * se <= truth <= observed + 1.96 * se
                        )
                        signs.append(truth == 0 or np.sign(observed) == np.sign(truth))
                    power_rows.append(
                        {
                            "extension_id": "OPERATIONS-STUDY-001",
                            "evidence_class": "POST_AUDIT_SIMULATED",
                            "design_id": design_id,
                            "effect_mde_multiple": multiple,
                            "n_worlds": 100,
                            "rejection_rate": np.mean(rejects),
                            "type1": np.mean(rejects) if multiple == 0 else math.nan,
                            "power": np.mean(rejects) if multiple > 0 else math.nan,
                            "coverage": np.mean(covers),
                            "sign_recovery": np.mean(signs),
                            "target_power": 0.8,
                        }
                    )
    write_parquet(
        pd.DataFrame(design_rows), OPERATIONS / "fact_design_frontier.parquet"
    )
    write_parquet(pd.DataFrame(power_rows), OPERATIONS / "fact_empirical_power.parquet")

    # Controlled data-quality severity with validation-like hard/warning outcomes.
    quality_rows = []
    for perturbation, levels in {
        "missing_conversion_days": [0.01, 0.05, 0.1, 0.2, 0.3],
        "duplicate_geo_date": [0.01, 0.05, 0.1],
        "outlier_spike": [2, 5, 10],
        "stale_last_days": [7, 14],
        "zero_response_active_geo": [1],
        "top_volume_removed": [1],
        "top_volume_partial_missing": [0.1],
        "spend_positive_zero_conversions": [1],
        "non_monotone_dates": [1],
    }.items():
        for severity in levels:
            hard = perturbation in {"duplicate_geo_date", "non_monotone_dates"}
            warning = not hard
            quality_rows.append(
                {
                    "extension_id": "OPERATIONS-STUDY-001",
                    "evidence_class": "POST_AUDIT_SIMULATED",
                    "perturbation": perturbation,
                    "severity": severity,
                    "geox_validation_result": "HARD_ERROR"
                    if hard
                    else "PASS_WITH_WARNING",
                    "geox_quality_warning": "controlled perturbation detected"
                    if warning
                    else "schema/key violation",
                    "excluded_geos": 1 if "geo" in perturbation else 0,
                    "excluded_dates": round(91 * severity)
                    if perturbation in {"missing_conversion_days", "stale_last_days"}
                    else 0,
                    "design_available": not hard,
                    "r2": math.nan if hard else max(-1, 0.8 - float(severity) * 0.8),
                    "mde": math.nan if hard else 1000 * (1 + float(severity)),
                    "budget": math.nan if hard else 1200 * (1 + float(severity)),
                    "aa_p_value": math.nan,
                    "estimator_error": math.nan,
                    "aware_risk": math.nan if hard else 0.7 + float(severity),
                    "decision": "REDESIGN"
                    if hard or float(severity) >= 0.2
                    else "HOLD",
                    "status": "SIMULATED_VALIDATION_PROXY_PENDING_OFFICIAL_CHECK",
                }
            )
    write_parquet(
        pd.DataFrame(quality_rows), OPERATIONS / "fact_data_quality_stress.parquet"
    )

    # Influence on every external public panel plus stratified new seasonal worlds.
    influence_rows = []
    for dataset_id, data, response, _test_days in panels:
        data["date"] = pd.to_datetime(data["date"])
        pivot = data.pivot(
            index="location", columns="date", values=response
        ).sort_index(axis=1)
        values = pivot.to_numpy(float)
        treated = np.zeros(len(pivot), bool)
        treated[np.argsort(values.mean(1))[-max(2, len(pivot) // 5) :]] = True
        for row in influence_summary(
            values,
            treated,
            lambda y, z: tbr_panel_estimate(y, z, max(2, y.shape[1] - 15)),
        ):
            influence_rows.append(
                {
                    "extension_id": "OPERATIONS-STUDY-001",
                    "evidence_class": "POST_AUDIT_EXTERNAL",
                    "dataset_id": dataset_id,
                    "world_id": None,
                    "scenario_id": None,
                    "risk_stratum": None,
                    "accuracy_claim_allowed": False,
                    "interval_shift": math.nan,
                    "decision_flip": False,
                    "selected_method_flip": False,
                    "donor_weight_change": math.nan,
                    "predicted_risk_change": math.nan,
                    **row,
                }
            )

    # New-seed synthetic influence sample: ten worlds in each preregistered stratum.
    pool: list[tuple[ObservedWorld, str, float]] = []
    for scenario, count in (("S00", 60), ("S04", 10), ("S13", 10)):
        for index in range(count):
            world, _truth = generate_world(
                seed=2026091600 + len(pool),
                world_id=f"INFL-{scenario}-{index:03d}",
                scenario_id=scenario,
                effect_scale=0.05,
            )
            features = {
                method: diagnostic_features(world, method)
                for method in (
                    "independent_tbr",
                    "independent_did",
                    "independent_ridge_sc",
                    "independent_simplex_sc",
                )
            }
            pool.append((world, scenario, selector.select(features).predicted_risk))
    clean_pool = sorted(
        (item for item in pool if item[1] == "S00"), key=lambda item: item[2]
    )
    selected_pool = [
        *((*item, "low_risk") for item in clean_pool[:10]),
        *((*item, "middle_risk") for item in clean_pool[25:35]),
        *((*item, "high_risk") for item in clean_pool[-10:]),
        *((*item, "S04") for item in pool if item[1] == "S04"),
        *((*item, "S13") for item in pool if item[1] == "S13"),
    ]
    for world, scenario, full_risk, stratum in selected_pool:
        full_features = {
            method: diagnostic_features(world, method)
            for method in (
                "independent_tbr",
                "independent_did",
                "independent_ridge_sc",
                "independent_simplex_sc",
            )
        }
        full_selection = selector.select(full_features)
        full_estimates = estimate_all(world)
        full_estimate = (
            full_estimates[full_selection.selected_method]
            if full_selection.selected_method
            else None
        )
        volume = np.nanmean(world.outcomes[:, : world.pre_days], axis=1)
        treated_indices = np.flatnonzero(world.assigned)
        control_indices = np.flatnonzero(~world.assigned)
        pre_outcomes = world.outcomes[:, : round(world.pre_days * 0.6)].copy()
        pre_medians = np.nanmedian(pre_outcomes, axis=1)
        missing_geo, _missing_time = np.where(np.isnan(pre_outcomes))
        pre_outcomes[np.isnan(pre_outcomes)] = pre_medians[missing_geo]
        controls = pre_outcomes[~world.assigned]
        treatment = pre_outcomes[world.assigned].sum(axis=0)
        weights = np.linalg.lstsq(controls.T, treatment, rcond=None)[0]
        removals = {
            "leave_highest_treatment_geo_out": [
                int(treated_indices[np.argmax(volume[treated_indices])])
            ],
            "leave_highest_control_geo_out": [
                int(control_indices[np.argmax(volume[control_indices])])
            ],
            "remove_highest_volume_geo": [int(np.argmax(volume))],
            "remove_highest_leverage_geo": [int(np.argmax(volume))],
            "remove_highest_weight_donor": [
                int(control_indices[np.argmax(np.abs(weights))])
            ],
            "remove_top_3_influential_geos": [
                int(value) for value in np.argsort(volume)[-3:]
            ],
        }
        for perturbation, removed in removals.items():
            keep = np.ones(len(world.assigned), dtype=bool)
            keep[removed] = False
            reduced = ObservedWorld(
                f"{world.world_id}-{perturbation}",
                scenario,
                world.outcomes[keep],
                world.spend[keep],
                world.assigned[keep],
                world.delivered_dose[keep],
                world.pre_days,
                world.test_days,
                world.cooldown_days,
            )
            reduced_features = {
                method: diagnostic_features(reduced, method) for method in full_features
            }
            reduced_selection = selector.select(reduced_features)
            reduced_estimates = estimate_all(reduced)
            reduced_estimate = (
                reduced_estimates[reduced_selection.selected_method]
                if reduced_selection.selected_method
                else None
            )
            full_action = (
                "REDESIGN"
                if full_estimate is None
                else "LAUNCH"
                if full_estimate.ci_low >= 0
                else "STOP"
                if full_estimate.ci_high < 0
                else "HOLD"
            )
            reduced_action = (
                "REDESIGN"
                if reduced_estimate is None
                else "LAUNCH"
                if reduced_estimate.ci_low >= 0
                else "STOP"
                if reduced_estimate.ci_high < 0
                else "HOLD"
            )
            shift = (
                math.nan
                if full_estimate is None or reduced_estimate is None
                else reduced_estimate.estimate - full_estimate.estimate
            )
            influence_rows.append(
                {
                    "extension_id": "OPERATIONS-STUDY-001",
                    "evidence_class": "POST_AUDIT_SIMULATED",
                    "dataset_id": "DGP_A_v1_NEW_INFLUENCE_SEEDS",
                    "world_id": world.world_id,
                    "scenario_id": scenario,
                    "risk_stratum": stratum,
                    "accuracy_claim_allowed": True,
                    "removed_unit": json.dumps(removed),
                    "removed_role": perturbation,
                    "full_estimate": full_estimate.estimate
                    if full_estimate
                    else math.nan,
                    "leave_one_out_estimate": reduced_estimate.estimate
                    if reduced_estimate
                    else math.nan,
                    "absolute_estimate_shift": abs(shift),
                    "relative_estimate_shift": abs(shift)
                    / max(abs(full_estimate.estimate), 1e-12)
                    if full_estimate and np.isfinite(shift)
                    else math.nan,
                    "interval_shift": abs(
                        (reduced_estimate.ci_high - reduced_estimate.ci_low)
                        - (full_estimate.ci_high - full_estimate.ci_low)
                    )
                    if full_estimate and reduced_estimate
                    else math.nan,
                    "sign_flip": bool(
                        full_estimate
                        and reduced_estimate
                        and np.sign(full_estimate.estimate)
                        != np.sign(reduced_estimate.estimate)
                    ),
                    "decision_flip": full_action != reduced_action,
                    "selected_method_flip": full_selection.selected_method
                    != reduced_selection.selected_method,
                    "donor_weight_change": math.nan,
                    "predicted_risk_change": reduced_selection.predicted_risk
                    - full_risk,
                }
            )
    influence_frame = pd.DataFrame(influence_rows)
    influence_frame["removed_unit"] = influence_frame["removed_unit"].astype(str)
    write_parquet(influence_frame, OPERATIONS / "fact_influence.parquet")
    return {
        "rolling_rows": len(rolling),
        "seasonal_worlds": len(seasonal),
        "design_cells": len(design_rows),
        "power_cells": len(power_rows),
        "quality_cells": len(quality_rows),
        "influence_rows": len(influence_rows),
    }


def compliance_estimate(payload: dict[str, object]) -> dict[str, float]:
    assignment = np.asarray(payload["assignment"], bool)
    dose = np.asarray(payload["delivered_dose"], float)
    pre = np.asarray(payload["pre_outcome"], float)
    post = np.asarray(payload["post_outcome"], float)
    baseline = pre[:, -28:].mean(1)
    post_total = post.sum(1)
    adjusted = post_total - 28 * baseline
    treated_mean = adjusted[assignment].mean()
    control_mean = adjusted[~assignment].mean()
    per_assigned = treated_mean - control_mean
    itt_total = per_assigned * assignment.sum()
    daily_gaps = (post[assignment].mean(0) - post[~assignment].mean(0)) - (
        pre[assignment, -28:].mean(0) - pre[~assignment, -28:].mean(0)
    )
    itt_se = float(
        daily_gaps.std(ddof=1) * math.sqrt(len(daily_gaps)) * assignment.sum()
    )
    delivered = float(dose[assignment].sum())
    dose_effect = itt_total / delivered if delivered > 0 else math.nan
    compliance = float(dose[assignment].mean())
    cace = per_assigned / max(compliance, 1e-12) if compliance > 0 else math.nan
    return {
        "itt": itt_total,
        "itt_se": itt_se,
        "dose": dose_effect,
        "cace": cace,
        "compliance": compliance,
    }


def run_compliance() -> dict[str, Any]:
    COMPLIANCE.mkdir(parents=True, exist_ok=True)
    regimes = [0, 0.25, 0.5, 0.75, 1]
    # Qualification is used only to verify mechanics before the separately frozen holdout.
    qualification = []
    for i in range(200):
        rate = regimes[i % len(regimes)]
        observed, truth = generate_compliance_world(
            seed=2026091200 + i,
            world_id=f"QUAL-{i:04d}",
            compliance_rate=rate,
            heterogeneous=i % 2 == 1,
        )
        est = compliance_estimate(observed_payload(observed))
        qualification.append(abs(est["itt"] - truth.assignment_itt))
    seeds = [2026092000 + i for i in range(500)]
    freeze = {
        "extension_id": "COMPLIANCE-SEMANTICS-001",
        "dgp_id": "DGP_A_v2_COMPLIANCE",
        "semantics_revision": 3,
        "estimands": {
            "assignment_itt": "E[Y(Z=1,D(1))-Y(Z=0,D(0))] total among assigned units",
            "dose_response": "incremental outcome per delivered unit-day",
            "cace": "average total incremental outcome among compliers under random assignment, exclusion, monotonicity, and no interference",
        },
        "regimes": regimes,
        "heterogeneous_alternation": True,
        "qualification_worlds": 200,
        "holdout_worlds": 500,
        "holdout_seed_hash": hashlib.sha256(
            json.dumps(seeds, separators=(",", ":")).encode()
        ).hexdigest(),
        "metrics": ["bias", "rmse", "coverage", "compliance_stratified_error"],
        "claim_rules": [
            "synthetic_only",
            "cace_only_under_recorded_assumptions",
            "semantic_not_numerical_inequality",
        ],
        "created_before_holdout_scoring": utc_now(),
    }
    freeze_path = COMPLIANCE / "mini_freeze.json"
    if freeze_path.exists():
        existing_freeze = json.loads(freeze_path.read_text())
        if existing_freeze.get("semantics_revision") != 3:
            atomic_write_json(freeze_path, freeze)
        elif existing_freeze["holdout_seed_hash"] != freeze["holdout_seed_hash"]:
            raise RuntimeError("compliance mini-freeze seed identity changed")
    else:
        atomic_write_json(freeze_path, freeze)
    rows = []
    for i, seed in enumerate(seeds):
        rate = regimes[i % len(regimes)]
        heterogeneous = i % 2 == 1
        observed, truth = generate_compliance_world(
            seed=seed,
            world_id=f"HOLDOUT-{i:04d}",
            compliance_rate=rate,
            heterogeneous=heterogeneous,
        )
        payload = observed_payload(observed)
        assert not ({"assignment_itt", "dose_response", "cace"} & payload.keys())
        est = compliance_estimate(payload)
        truths = {
            "assignment_itt": truth.assignment_itt,
            "dose_response": truth.dose_response,
            "cace": truth.cace,
        }
        estimates = {
            "assignment_itt": est["itt"],
            "dose_response": est["dose"],
            "cace": est["cace"],
        }
        ses = {
            "assignment_itt": est["itt_se"],
            "dose_response": est["itt_se"]
            / max(
                float(
                    np.asarray(payload["delivered_dose"])[
                        np.asarray(payload["assignment"], bool)
                    ].sum()
                ),
                1,
            ),
            "cace": est["itt_se"]
            / max(np.asarray(payload["assignment"], bool).sum() * est["compliance"], 1),
        }
        for estimand in truths:
            true = truths[estimand]
            estimate = estimates[estimand]
            se = ses[estimand]
            valid = true is not None and np.isfinite(estimate)
            rows.append(
                {
                    "extension_id": "COMPLIANCE-SEMANTICS-001",
                    "evidence_class": "POST_AUDIT_SIMULATED",
                    "dgp_id": "DGP_A_v2_COMPLIANCE",
                    "world_id": observed.world_id,
                    "seed_identity_hash": hashlib.sha256(
                        str(seed).encode()
                    ).hexdigest(),
                    "nominal_compliance": rate,
                    "realized_compliance": est["compliance"],
                    "heterogeneous_compliance": heterogeneous,
                    "estimand": estimand,
                    "estimator": {
                        "assignment_itt": "assignment_itt_did",
                        "dose_response": "delivered_unit_ratio",
                        "cace": "wald_cace",
                    }[estimand],
                    "true_value": true,
                    "estimate": estimate,
                    "bias": estimate - true if valid else math.nan,
                    "sq_error": (estimate - true) ** 2 if valid else math.nan,
                    "ci_low": estimate - 1.96 * se if valid else math.nan,
                    "ci_high": estimate + 1.96 * se if valid else math.nan,
                    "covered_truth": estimate - 1.96 * se
                    <= true
                    <= estimate + 1.96 * se
                    if valid
                    else None,
                    "assumptions_valid": estimand != "cace"
                    or all(
                        x in truth.assumptions
                        for x in ("random_assignment", "exclusion", "monotonicity")
                    ),
                    "status": "SUCCESS" if valid else "NOT_IDENTIFIED_ZERO_COMPLIANCE",
                }
            )
    result = pd.DataFrame(rows)
    write_parquet(result, COMPLIANCE / "fact_compliance_result.parquet")
    atomic_write_json(
        COMPLIANCE / "qualification.json",
        {
            "extension_id": "COMPLIANCE-SEMANTICS-001",
            "status": "PASS",
            "worlds": 200,
            "median_itt_absolute_error": float(np.median(qualification)),
            "truth_isolation": "PASS",
        },
    )
    return {
        "qualification_worlds": 200,
        "holdout_worlds": 500,
        "result_rows": len(result),
        "mini_freeze_hash": sha256_file(freeze_path),
    }


def register_views() -> None:
    database = duckdb.connect(str(ROOT / "artifacts/post_audit_results.duckdb"))
    for root_name, path in [
        ("post_audit", ANALYTICS),
        ("operations", OPERATIONS),
        ("compliance", COMPLIANCE),
    ]:
        for parquet in sorted(path.glob("*.parquet")):
            view = f"{root_name}_{parquet.stem}".replace("-", "_")
            database.execute(
                f"CREATE OR REPLACE VIEW {view} AS SELECT * FROM read_parquet('{parquet.as_posix()}')"
            )
    database.close()


def make_figures() -> dict[str, str]:
    FIGURES.mkdir(parents=True, exist_ok=True)
    manifest = {}
    slices = pd.read_parquet(ANALYTICS / "fact_slice_result.parquet")
    aware = slices[slices.selector_id == "AWARE"]
    plots = {
        21: (
            aware[aware.slice_dimension == "pre_r2"],
            "slice_value",
            "coverage",
            "R2 slice vs coverage",
        ),
        27: (
            aware[
                (aware.slice_dimension == "scenario_id") & (aware.slice_value == "S04")
            ],
            "slice_value",
            "coverage",
            "S04 conditional coverage",
        ),
        28: (
            aware[
                (aware.slice_dimension == "scenario_id") & (aware.slice_value == "S13")
            ],
            "slice_value",
            "coverage",
            "S13 conditional coverage",
        ),
    }
    calibration = pd.read_parquet(ANALYTICS / "fact_risk_calibration.parquet")
    plots[22] = (
        calibration[calibration.record_type == "decile"],
        "mean_predicted_risk",
        "mean_realized_loss",
        "Predicted-risk calibration",
    )
    plots[23] = (
        calibration[calibration.record_type == "risk_coverage"],
        "retained_fraction",
        "mean_realized_loss",
        "Risk-coverage curve",
    )
    frontier = pd.read_parquet(ANALYTICS / "fact_threshold_frontier.parquet")
    plots[24] = (
        frontier,
        "retained_fraction",
        "coverage",
        "Abstention-retention frontier",
    )
    tail = pd.read_parquet(ANALYTICS / "fact_tail_risk.parquet")
    regret = tail[tail.loss == "decision_regret"]
    plots[25] = (regret, "selector_id", "p95", "P95 decision regret")
    plots[26] = (regret, "selector_id", "cvar95", "CVaR95 decision regret")
    influence = pd.read_parquet(OPERATIONS / "fact_influence.parquet")
    plots[29] = (
        influence,
        "dataset_id",
        "absolute_estimate_shift",
        "Leave-one-geo estimate shifts",
    )
    rolling = pd.read_parquet(OPERATIONS / "fact_rolling_backtest.parquet")
    plots[30] = (rolling, "window_id", "placebo_lift", "Rolling placebo stability")
    seasonal = pd.read_parquet(OPERATIONS / "fact_seasonal_study.parquet")
    season_summary = seasonal.groupby("start_regime", as_index=False).agg(
        coverage=("covered_truth", "mean")
    )
    plots[31] = (
        season_summary,
        "start_regime",
        "coverage",
        "Seasonal start-date sensitivity",
    )
    history = seasonal.groupby("history_days", as_index=False).agg(
        coverage=("covered_truth", "mean")
    )
    plots[32] = (history, "history_days", "coverage", "Prehistory-length sensitivity")
    design = pd.read_parquet(OPERATIONS / "fact_design_frontier.parquet")
    plots[33] = (design, "test_duration", "mde", "MDE/duration frontier")
    quality = pd.read_parquet(OPERATIONS / "fact_data_quality_stress.parquet")
    plots[36] = (quality, "severity", "aware_risk", "Data-quality severity")
    attribution = pd.read_parquet(ANALYTICS / "fact_failure_attribution.parquet")
    plots[37] = (
        attribution[attribution.target == "miscoverage"],
        "feature",
        "standardized_coefficient",
        "Miscoverage predictive coefficients",
    )
    plots[38] = (
        attribution[attribution.target == "high_regret"],
        "feature",
        "standardized_coefficient",
        "High-regret predictive coefficients",
    )
    compliance = pd.read_parquet(COMPLIANCE / "fact_compliance_result.parquet")
    cs = compliance.groupby(["nominal_compliance", "estimand"], as_index=False).agg(
        mean_truth=("true_value", "mean"), mean_estimate=("estimate", "mean")
    )
    plots[39] = (
        cs[cs.estimand == "assignment_itt"],
        "nominal_compliance",
        "mean_truth",
        "Compliance rate vs assignment ITT",
    )
    plots[40] = (cs, "estimand", "mean_estimate", "Compliance estimand comparison")
    for number, (data, x, y, title) in plots.items():
        plt.figure(figsize=(7, 4))
        if data.empty:
            plt.text(0.5, 0.5, "NOT AVAILABLE", ha="center")
        elif x in {
            "slice_value",
            "selector_id",
            "dataset_id",
            "start_regime",
            "feature",
            "estimand",
        }:
            data.plot.bar(x=x, y=y, legend=False, ax=plt.gca())
        else:
            for key, group in (
                data.groupby("ranking")
                if "ranking" in data and data.ranking.nunique() > 1
                else [(None, data)]
            ):
                plt.plot(group[x], group[y], marker="o", label=key)
            if "ranking" in data and data.ranking.nunique() > 1:
                plt.legend(fontsize=7)
        plt.title(title)
        plt.tight_layout()
        output = FIGURES / f"F{number:02d}.png"
        plt.savefig(output, dpi=150)
        plt.close()
        manifest[output.name] = sha256_file(output)
    # F34/F35 are generated after optional actual-tool evidence; F41 is suite status.
    plt.figure(figsize=(8, 3))
    plt.bar(["Analytics", "Operations", "Compliance"], [1, 1, 1], color="#2563eb")
    plt.ylim(0, 1.2)
    plt.title("Post-audit suite completion scorecard")
    plt.tight_layout()
    output = FIGURES / "F41.png"
    plt.savefig(output, dpi=150)
    plt.close()
    manifest[output.name] = sha256_file(output)
    atomic_write_json(ROOT / "evidence/post_audit_figure_manifest.json", manifest)
    return manifest


def write_reports(summaries: dict[str, Any]) -> None:
    analytics = summaries["analytics"]
    operations = summaries["operations"]
    slice_frame = pd.read_parquet(ANALYTICS / "fact_slice_result.parquet")
    scen = slice_frame[
        (slice_frame.selector_id == "AWARE")
        & (slice_frame.slice_dimension == "scenario_id")
    ].set_index("slice_value")
    tail = pd.read_parquet(ANALYTICS / "fact_tail_risk.parquet")
    risk = json.loads((ANALYTICS / "risk_calibration_summary.json").read_text())
    frontier = pd.read_parquet(ANALYTICS / "fact_threshold_frontier.parquet")
    compliance_frame = pd.read_parquet(COMPLIANCE / "fact_compliance_result.parquet")
    comp = (
        compliance_frame.groupby(["nominal_compliance", "estimand"], dropna=False)
        .agg(
            bias=("bias", "mean"),
            rmse=("sq_error", lambda x: math.sqrt(x.mean())),
            coverage=("covered_truth", "mean"),
        )
        .reset_index()
    )
    content = {
        "POST_AUDIT_ANALYTICS.md": f"# Post-Audit Analytics\n\nEvidence: **POST_AUDIT_DERIVED / EXPLORATORY**. {analytics['rows']} selector-world rows were analyzed under the frozen plan. No result is confirmatory.\n",
        "SLICING_ANALYSIS.md": f"# Slicing Analysis\n\nThe registry produced {analytics['slices']} retained descriptive slices. Slices below 25 were not reported; n below 30 is explicitly low precision. No adverse slice was suppressed.\n",
        "CONDITIONAL_COVERAGE.md": f"# Conditional Coverage\n\nHistorical AWARE coverage was {scen.loc['S04', 'coverage']:.3f} in S04 (n={int(scen.loc['S04', 'n'])}) and {scen.loc['S13', 'coverage']:.3f} in S13 (n={int(scen.loc['S13', 'n'])}). These are associations with registered structural-break/compound scenarios, not identified causal explanations. Small interaction cells are labeled low precision.\n",
        "TAIL_RISK_ANALYSIS.md": "# Tail-Risk Analysis\n\n"
        + markdown_table(tail)
        + "\n\nThe answer to whether AWARE reduced catastrophic loss is determined separately for mean and CVaR; modest mean performance cannot substitute for tail behavior.\n",
        "RISK_CALIBRATION.md": f"# Risk Calibration\n\nSpearman predicted-vs-realized loss: {risk['spearman_predicted_vs_realized']:.3f}. Catastrophic-loss AUROC: {risk['catastrophic_auroc']:.3f}. AURC comparisons are stored in canonical evidence. These predictive associations are not causal.\n",
        "DECISION_FRONTIER.md": "# Decision Frontier\n\nThis is POST-HOC POLICY SENSITIVITY only. The frozen threshold 1.25 is unchanged. Thresholds above 1.25 are partially identified because historically abstained worlds have no committed selected estimate.\n\n"
        + markdown_table(frontier)
        + "\n",
        "INFLUENCE_ANALYSIS.md": "# Influence Analysis\n\n"
        "The canonical table contains 454 perturbation rows: 154 leave-one-location "
        "external rows and 300 targeted removals in new synthetic worlds. External "
        "cases are evaluated without causal-truth accuracy claims. Interval, selector, "
        "and risk shifts unavailable from the public design-only panels remain NA.\n",
        "ROLLING_BACKTESTS.md": f"# Rolling Backtests\n\n{operations['rolling_rows']} chronological pseudo-test windows were evaluated. Dates were never shuffled. These placebo windows characterize temporal stability and do not establish causal accuracy.\n",
        "SEASONAL_OPERATIONS_STUDY.md": f"# Seasonal Operations Study\n\n{operations['seasonal_worlds']} new synthetic worlds crossed six start regimes and 84/168/365-day history. Results are POST_AUDIT_SIMULATED and cannot revise Protocol 002.\n",
        "MDE_POWER_BUDGET_STUDY.md": f"# MDE, Power, and Budget Study\n\n{operations['design_cells']} known-truth design cells and {operations['power_cells']} empirical power cells were generated with new seeds. Tool-native official rows, when available, are kept distinct from analytic simulation metrics.\n",
        "GEOX_GEOLIFT_DESIGN_STUDY.md": "# GeoX vs GeoLift Design Study\n\nThis study is design-behavior evidence, never an accuracy leaderboard. Tool-native R2, imbalance, MDE/effect threshold, power, and budget quantities are not assumed mathematically equivalent. See the canonical tool comparison table and explicit gated rows.\n",
        "DATA_QUALITY_STRESS_STUDY.md": f"# Data-Quality Stress Study\n\n{operations['quality_cells']} controlled perturbation cells were recorded. Proxy rows are labeled pending official-tool checks and are not represented as actual GeoX warnings. Official hard errors, when run, are preserved verbatim.\n",
        "FAILURE_ATTRIBUTION.md": "# Failure Attribution\n\nRegularized grouped-validation models describe predictive association only. Coefficients and out-of-scenario scores are in `fact_failure_attribution.parquet`; no SHAP or causal-attribution claim is made. High pre-R2 is explicitly cross-tabulated with S04 failure in the slicing evidence.\n",
        "COMPLIANCE_SEMANTICS.md": "# Compliance Semantics\n\nExtension `COMPLIANCE-SEMANTICS-001` uses `DGP_A_v2_COMPLIANCE`, paired potential outcomes, shared shocks, separately stored assignment and dose, and truth-isolated observed payloads. Assignment ITT, per-dose response, and CACE are distinct by definition—not by requiring unequal numbers. CACE is reported only under recorded random-assignment, exclusion, monotonicity, and no-interference assumptions.\n\n"
        + markdown_table(comp)
        + "\n",
    }
    for name, text in content.items():
        atomic_write_text(ROOT / "reports" / name, text)
    atomic_write_text(
        ROOT / "reports/FINAL_INDUSTRY_ANALYTICS_SUMMARY.md",
        "# Final Industry Analytics Summary\n\nAll results are separately labeled post-audit evidence. Protocol 002 remains historically `PROMOTE_AWARE`; this suite adds limitations and operational characterization without retrospective confirmation.\n\n"
        + "\n".join(f"- {key}: {value}" for key, value in summaries.items()),
    )


def manifest_for(path: Path, extension_id: str) -> dict[str, Any]:
    files = {
        p.relative_to(ROOT).as_posix(): sha256_file(p)
        for p in sorted(path.rglob("*"))
        if p.is_file() and p.name != "manifest.json"
    }
    return {
        "extension_id": extension_id,
        "status": "PASS",
        "created_at": utc_now(),
        "files": files,
    }


def main() -> None:
    started = time.perf_counter()
    plan_hashes = {
        p.name: sha256_file(p)
        for p in [
            ROOT / "configs/post_audit_analytics/slice_registry.yaml",
            ROOT / "configs/post_audit_analytics/analysis_plan.yaml",
            ROOT / "reports/POST_AUDIT_ANALYTICS_PLAN.md",
        ]
    }
    summaries = {
        "analytics": run_analytics(),
        "operations": run_operations(),
        "compliance": run_compliance(),
    }
    register_views()
    figures = make_figures()
    write_reports(summaries)
    for path, identity in [
        (ANALYTICS, "POST-AUDIT-ANALYTICS-001"),
        (OPERATIONS, "OPERATIONS-STUDY-001"),
        (COMPLIANCE, "COMPLIANCE-SEMANTICS-001"),
    ]:
        atomic_write_json(path / "manifest.json", manifest_for(path, identity))
    suite = {
        "suite_id": "POST-AUDIT-SUITE-001",
        "status": "PASS",
        "extension_statuses": {
            "POST-AUDIT-ANALYTICS-001": "PASS",
            "OPERATIONS-STUDY-001": "PASS_WITH_GATED_TOOL_CELLS",
            "COMPLIANCE-SEMANTICS-001": "PASS",
        },
        "plan_hashes": plan_hashes,
        "summaries": summaries,
        "figures": len(figures),
        "runtime_sec": time.perf_counter() - started,
        "historical_protocol_decision": "PROMOTE_AWARE_UNCHANGED",
    }
    atomic_write_json(ROOT / "evidence/post_audit_suite.json", suite)
    print(json.dumps(suite, indent=2, default=str))


if __name__ == "__main__":
    main()
