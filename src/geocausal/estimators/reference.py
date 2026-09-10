"""Transparent independent estimators for high-volume known-truth simulation.

These implementations are not relabeled as official upstream packages. Package
methods have separate qualification/case-study adapters.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy.optimize import nnls

from geocausal.dgp import ObservedWorld


@dataclass(frozen=True)
class Estimate:
    method_id: str
    estimate: float
    standard_error: float
    ci_low: float
    ci_high: float
    p_value: float
    status: str = "SUCCESS"
    failure_reason: str | None = None


def _finish(method_id: str, estimate: float, standard_error: float) -> Estimate:
    # Frozen candidates from the first pre-freeze E08 null calibration. These
    # are empirical procedure intervals, not upstream-native intervals.
    calibration = {
        "independent_tbr": 1.9,
        "independent_did": 1.8,
        "independent_ridge_sc": 3.2,
        "independent_simplex_sc": 3.2,
    }[method_id]
    standard_error = max(float(standard_error) * calibration, 1e-9)
    z = estimate / standard_error
    # Stable two-sided normal approximation without an extra distribution object.
    p_value = float(math.erfc(abs(z) / np.sqrt(2)))
    return Estimate(
        method_id=method_id,
        estimate=float(estimate),
        standard_error=standard_error,
        ci_low=float(estimate - 1.96 * standard_error),
        ci_high=float(estimate + 1.96 * standard_error),
        p_value=p_value,
    )


def _series(world: ObservedWorld) -> tuple[np.ndarray, np.ndarray]:
    outcomes = world.outcomes.copy()
    medians = np.nanmedian(outcomes, axis=1)
    missing_geo, _ = np.where(np.isnan(outcomes))
    outcomes[np.isnan(outcomes)] = medians[missing_geo]
    treated = outcomes[world.assigned].sum(axis=0)
    controls = outcomes[~world.assigned]
    return treated, controls


def estimate_tbr(world: ObservedWorld) -> Estimate:
    treated, controls = _series(world)
    control_total = controls.sum(axis=0)
    fit_days = round(world.pre_days * 0.60)
    x_fit = np.column_stack([np.ones(fit_days), control_total[:fit_days]])
    coefficients = np.linalg.lstsq(x_fit, treated[:fit_days], rcond=None)[0]
    prediction = coefficients[0] + coefficients[1] * control_total
    residual = treated[: world.pre_days] - prediction[: world.pre_days]
    post_residual = treated[world.analysis_slice] - prediction[world.analysis_slice]
    effect = post_residual.sum()
    rho = np.corrcoef(residual[1:], residual[:-1])[0, 1]
    inflation = np.sqrt(
        max(0.25, (1 + np.nan_to_num(rho)) / max(0.1, 1 - np.nan_to_num(rho)))
    )
    se = residual.std(ddof=2) * np.sqrt(len(post_residual)) * inflation
    return _finish("independent_tbr", effect, se)


def estimate_did(world: ObservedWorld) -> Estimate:
    treated, controls = _series(world)
    control_mean = controls.mean(axis=0)
    pre_slice = slice(max(0, world.pre_days - world.test_days), world.pre_days)
    baseline_gap = (
        treated[pre_slice].mean()
        - world.assigned.sum() * control_mean[pre_slice].mean()
    )
    post_gap = (
        treated[world.analysis_slice]
        - world.assigned.sum() * control_mean[world.analysis_slice]
    )
    daily = post_gap - baseline_gap
    return _finish(
        "independent_did", daily.sum(), daily.std(ddof=1) * np.sqrt(len(daily))
    )


def estimate_ridge_sc(world: ObservedWorld) -> Estimate:
    treated, controls = _series(world)
    fit_days = round(world.pre_days * 0.60)
    x = controls[:, :fit_days].T
    y = treated[:fit_days]
    ridge = 1e-2 * np.trace(x.T @ x) / max(1, x.shape[1])
    weights = np.linalg.solve(x.T @ x + ridge * np.eye(x.shape[1]), x.T @ y)
    prediction = controls.T @ weights
    residual = treated[: world.pre_days] - prediction[: world.pre_days]
    daily = treated[world.analysis_slice] - prediction[world.analysis_slice]
    return _finish(
        "independent_ridge_sc", daily.sum(), residual.std(ddof=1) * np.sqrt(len(daily))
    )


def estimate_simplex_sc(world: ObservedWorld) -> Estimate:
    treated, controls = _series(world)
    fit_days = round(world.pre_days * 0.60)
    raw_weights, _ = nnls(controls[:, :fit_days].T, treated[:fit_days])
    weights = raw_weights / max(raw_weights.sum(), 1e-12)
    scale = treated[:fit_days].mean() / max(
        (controls[:, :fit_days].T @ weights).mean(), 1e-12
    )
    prediction = scale * (controls.T @ weights)
    residual = treated[: world.pre_days] - prediction[: world.pre_days]
    daily = treated[world.analysis_slice] - prediction[world.analysis_slice]
    return _finish(
        "independent_simplex_sc",
        daily.sum(),
        residual.std(ddof=1) * np.sqrt(len(daily)),
    )


METHODS = {
    "independent_tbr": estimate_tbr,
    "independent_did": estimate_did,
    "independent_ridge_sc": estimate_ridge_sc,
    "independent_simplex_sc": estimate_simplex_sc,
}


def estimate_all(world: ObservedWorld) -> dict[str, Estimate]:
    results: dict[str, Estimate] = {}
    for method_id, estimator in METHODS.items():
        try:
            results[method_id] = estimator(world)
        except (ValueError, np.linalg.LinAlgError, FloatingPointError) as error:
            results[method_id] = Estimate(
                method_id=method_id,
                estimate=np.nan,
                standard_error=np.nan,
                ci_low=np.nan,
                ci_high=np.nan,
                p_value=np.nan,
                status="NUMERICAL_FAILURE",
                failure_reason=str(error),
            )
    return results
