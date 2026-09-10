"""Leakage-safe diagnostic feature construction."""

from __future__ import annotations

import numpy as np

from geocausal.dgp import ObservedWorld


def diagnostic_features(world: ObservedWorld, method_id: str) -> dict[str, float]:
    outcomes, _, assigned = world.pre_treatment_view()
    outcomes = outcomes.copy()
    medians = np.nanmedian(outcomes, axis=1)
    missing_geo, _ = np.where(np.isnan(outcomes))
    outcomes[np.isnan(outcomes)] = medians[missing_geo]
    treated = outcomes[assigned].sum(axis=0)
    controls = outcomes[~assigned]
    control_total = controls.sum(axis=0)
    fit_end = round(world.pre_days * 0.60)
    diagnostic_end = round(world.pre_days * 0.80)
    x_fit = np.column_stack([np.ones(fit_end), control_total[:fit_end]])
    coef = np.linalg.lstsq(x_fit, treated[:fit_end], rcond=None)[0]
    predicted = coef[0] + coef[1] * control_total
    diagnostic = slice(fit_end, diagnostic_end)
    placebo = slice(diagnostic_end, world.pre_days)
    residual = treated - predicted
    ss_res = np.sum(residual[diagnostic] ** 2)
    ss_tot = np.sum((treated[diagnostic] - treated[diagnostic].mean()) ** 2)
    pre_r2 = 1 - ss_res / max(ss_tot, 1e-12)
    rmse = np.sqrt(np.mean(residual[diagnostic] ** 2)) / max(
        treated[diagnostic].mean(), 1e-12
    )
    treated_slope = np.polyfit(
        np.arange(fit_end, diagnostic_end), treated[diagnostic], 1
    )[0]
    control_slope = np.polyfit(
        np.arange(fit_end, diagnostic_end), control_total[diagnostic], 1
    )[0]
    trend_gap = abs(
        treated_slope / max(treated[diagnostic].mean(), 1)
        - control_slope / max(control_total[diagnostic].mean(), 1)
    )
    acf = np.corrcoef(residual[1:diagnostic_end], residual[: diagnostic_end - 1])[0, 1]
    placebo_residual = residual[placebo]
    placebo_se = residual[:diagnostic_end].std(ddof=2) * np.sqrt(
        max(1, len(placebo_residual))
    )
    placebo_effect = placebo_residual.sum()
    placebo_fpr = float(abs(placebo_effect) > 1.96 * max(placebo_se, 1e-9))
    placebo_coverage = 1.0 - placebo_fpr

    x = controls[:, :fit_end].T
    weights = np.linalg.lstsq(x, treated[:fit_end], rcond=None)[0]
    absolute = np.abs(weights)
    normalized = absolute / max(absolute.sum(), 1e-12)
    donor_hhi = float(np.sum(normalized**2))
    effective_donors = float(1 / max(donor_hhi, 1e-12))
    return {
        "pre_r2": float(pre_r2),
        "pre_rmse": float(rmse),
        "trend_gap": float(trend_gap),
        "acf_score": float(abs(np.nan_to_num(acf))),
        "placebo_bias": float(placebo_effect / max(treated[placebo].sum(), 1)),
        "placebo_fpr": placebo_fpr,
        "placebo_coverage": placebo_coverage,
        "donor_hhi": donor_hhi,
        "effective_donors": effective_donors,
        "missingness": float(np.isnan(world.outcomes[:, : world.pre_days]).mean()),
        "geo_leverage": float(
            outcomes.mean(axis=1).max() / max(outcomes.mean(axis=1).sum(), 1)
        ),
        "method_is_tbr": float(method_id == "independent_tbr"),
        "method_is_did": float(method_id == "independent_did"),
        "method_is_ridge_sc": float(method_id == "independent_ridge_sc"),
        "method_is_simplex_sc": float(method_id == "independent_simplex_sc"),
    }
