"""Reusable leave-one-unit-out influence summaries."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import numpy.typing as npt

FloatArray = npt.NDArray[np.float64]


def influence_summary(
    outcomes: FloatArray,
    treated: npt.NDArray[np.bool_],
    estimator: Callable[[FloatArray, npt.NDArray[np.bool_]], float],
) -> list[dict[str, float | int | str | bool]]:
    """Evaluate every leave-one-unit-out shift without using causal truth."""
    if outcomes.ndim != 2 or len(treated) != outcomes.shape[0]:
        raise ValueError("outcomes must be unit x time and align with treated")
    full = float(estimator(outcomes, treated))
    rows: list[dict[str, float | int | str | bool]] = []
    for index in range(outcomes.shape[0]):
        keep = np.arange(outcomes.shape[0]) != index
        if not treated[keep].any() or treated[keep].all():
            continue
        estimate = float(estimator(outcomes[keep], treated[keep]))
        shift = estimate - full
        rows.append(
            {
                "removed_unit": int(index),
                "removed_role": "treatment" if treated[index] else "control",
                "full_estimate": full,
                "leave_one_out_estimate": estimate,
                "absolute_estimate_shift": abs(shift),
                "relative_estimate_shift": abs(shift) / max(abs(full), 1e-12),
                "sign_flip": bool(np.sign(estimate) != np.sign(full)),
            }
        )
    return rows
