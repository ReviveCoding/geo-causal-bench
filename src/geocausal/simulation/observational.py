"""Known-truth Track B benchmark kept numerically separate from Track A."""

from __future__ import annotations

import math
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pandas as pd

from geocausal.dgp import OBSERVATIONAL_SCENARIOS, generate_observational_world


def _twfe(frame: pd.DataFrame, *, conditional: bool = False) -> tuple[float, float]:
    y = frame["outcome"].to_numpy(float)
    d = frame["treated"].to_numpy(float)
    unit = frame["unit"]
    time = frame["time"]
    y_res = y - frame.groupby("unit")["outcome"].transform("mean").to_numpy()
    y_res -= frame.groupby("time")["outcome"].transform("mean").to_numpy()
    y_res += y.mean()
    d_series = frame["treated"]
    d_res = d - d_series.groupby(unit).transform("mean").to_numpy()
    d_res -= d_series.groupby(time).transform("mean").to_numpy()
    d_res += d.mean()
    if conditional:
        x_time = frame["x"].to_numpy(float) * time.to_numpy(float)
        matrix = np.column_stack([d_res, x_time, np.ones(len(frame))])
        coefficient = np.linalg.lstsq(matrix, y_res, rcond=None)[0]
        residual = y_res - matrix @ coefficient
        estimate = float(coefficient[0])
    else:
        estimate = float(np.dot(d_res, y_res) / max(np.dot(d_res, d_res), 1e-12))
        residual = y_res - estimate * d_res
    se = float(residual.std(ddof=2) / np.sqrt(max(np.dot(d_res, d_res), 1)))
    return estimate, se


def _group_time(frame: pd.DataFrame, *, equal_cohort: bool) -> tuple[float, float]:
    treated_cohorts = sorted(c for c in frame.cohort.unique() if c <= frame.time.max())
    cohort_effects: list[float] = []
    cohort_weights: list[int] = []
    for cohort in treated_cohorts:
        treated_units = frame.loc[frame.cohort == cohort, "unit"].unique()
        before = cohort - 1
        for period in range(int(cohort), int(frame.time.max()) + 1):
            controls = frame.loc[frame.cohort > period, "unit"].unique()
            if not len(controls):
                continue
            treated_post = frame.loc[
                frame.unit.isin(treated_units) & (frame.time == period), "outcome"
            ].mean()
            treated_pre = frame.loc[
                frame.unit.isin(treated_units) & (frame.time == before), "outcome"
            ].mean()
            control_post = frame.loc[
                frame.unit.isin(controls) & (frame.time == period), "outcome"
            ].mean()
            control_pre = frame.loc[
                frame.unit.isin(controls) & (frame.time == before), "outcome"
            ].mean()
            cohort_effects.append(
                float((treated_post - treated_pre) - (control_post - control_pre))
            )
            cohort_weights.append(1 if equal_cohort else len(treated_units))
    values = np.asarray(cohort_effects)
    weights = np.asarray(cohort_weights, dtype=float)
    estimate = float(np.average(values, weights=weights))
    se = float(values.std(ddof=1) / np.sqrt(max(len(values), 1)))
    return estimate, se


def _sdid(frame: pd.DataFrame) -> tuple[float, float]:
    treated_units = frame.loc[frame.treated == 1, "unit"].unique()
    never = frame.loc[frame.cohort > frame.time.max(), "unit"].unique()
    first = int(frame.loc[frame.treated == 1, "time"].min())
    pre = frame.time < first
    post = frame.time >= first
    treated = frame.unit.isin(treated_units)
    control = frame.unit.isin(never)
    effect = (
        frame.loc[treated & post, "outcome"].mean()
        - frame.loc[treated & pre, "outcome"].mean()
        - frame.loc[control & post, "outcome"].mean()
        + frame.loc[control & pre, "outcome"].mean()
    )
    daily = frame.loc[treated & post].groupby("time")["outcome"].mean()
    control_daily = frame.loc[control & post].groupby("time")["outcome"].mean()
    spread = (daily - control_daily).dropna()
    return float(effect), float(spread.std(ddof=1) / np.sqrt(max(len(spread), 1)))


METHODS: dict[str, Callable[[pd.DataFrame], tuple[float, float]]] = {
    "B0_naive_twfe": lambda frame: _twfe(frame),
    "B1_twfe_event_study_aggregate": lambda frame: _twfe(frame),
    "B2_callaway_santanna_reference": lambda frame: _group_time(
        frame, equal_cohort=False
    ),
    "B3_sun_abraham_reference": lambda frame: _group_time(frame, equal_cohort=True),
    "B4_sdid_reference": _sdid,
    "B5_ascm_covariate_adjusted": lambda frame: _twfe(frame, conditional=True),
}


def run_observational_benchmark(
    root: Path, protocol_id: str, *, worlds: int = 300, seed: int = 20260909
) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for index in range(worlds):
        scenario = OBSERVATIONAL_SCENARIOS[index % len(OBSERVATIONAL_SCENARIOS)]
        world_id = f"OBS-{index:05d}"
        frame, truth = generate_observational_world(
            seed=int(np.random.SeedSequence([seed, 16, index]).generate_state(1)[0]),
            world_id=world_id,
            scenario_id=scenario,
        )
        for method, estimator in METHODS.items():
            try:
                estimate, se = estimator(frame)
                status = "SUCCESS"
                reason = None
            except (ValueError, np.linalg.LinAlgError) as error:
                estimate, se = math.nan, math.nan
                status, reason = "NUMERICAL_FAILURE", str(error)
            rows.append(
                {
                    "protocol_id": protocol_id,
                    "evidence_class": "SIMULATED",
                    "track": "B",
                    "world_id": world_id,
                    "scenario_id": scenario,
                    "method_id": method,
                    "canonical_estimand": "overall_ATT",
                    "true_effect": truth.overall_att,
                    "estimate": estimate,
                    "bias": estimate - truth.overall_att,
                    "abs_error": abs(estimate - truth.overall_att),
                    "sq_error": (estimate - truth.overall_att) ** 2,
                    "standard_error": se,
                    "ci_low": estimate - 1.96 * se,
                    "ci_high": estimate + 1.96 * se,
                    "covered_truth": estimate - 1.96 * se
                    <= truth.overall_att
                    <= estimate + 1.96 * se,
                    "status": status,
                    "failure_reason": reason,
                }
            )
    evidence = pd.DataFrame(rows)
    path = root / "evidence" / "observational" / "fact_observational_result.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    evidence.to_parquet(path, index=False)
    summary = (
        evidence.groupby("method_id")
        .agg(
            bias=("bias", "mean"),
            rmse=("sq_error", lambda value: float(np.sqrt(value.mean()))),
            coverage=("covered_truth", "mean"),
            failure_rate=("status", lambda value: float((value != "SUCCESS").mean())),
        )
        .reset_index()
    )
    summary_path = root / "evidence" / "observational" / "method_summary.parquet"
    summary.to_parquet(summary_path, index=False)
    return {
        "worlds": worlds,
        "rows": len(evidence),
        "summary": summary.to_dict(orient="records"),
    }
