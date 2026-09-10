"""Potential-outcome DGP for assignment and delivered-dose semantics."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

FloatArray = npt.NDArray[np.float64]
BoolArray = npt.NDArray[np.bool_]


@dataclass(frozen=True)
class ComplianceObserved:
    world_id: str
    assignment: BoolArray
    delivered_dose: FloatArray
    pre_outcome: FloatArray
    post_outcome: FloatArray


@dataclass(frozen=True)
class ComplianceTruth:
    world_id: str
    y_z0_d0: FloatArray
    y_z1_d1: FloatArray
    assignment_itt: float
    dose_response: float
    cace: float | None
    assumptions: tuple[str, ...]


def generate_compliance_world(
    *, seed: int, world_id: str, compliance_rate: float, heterogeneous: bool
) -> tuple[ComplianceObserved, ComplianceTruth]:
    """Generate paired potential outcomes with shared shocks and exclusion."""
    if not 0 <= compliance_rate <= 1:
        raise ValueError("compliance_rate must be in [0, 1]")
    rng = np.random.default_rng(seed)
    n_units, pre_days, post_days = 40, 84, 28
    assignment = np.zeros(n_units, dtype=bool)
    assignment[rng.choice(n_units, n_units // 2, replace=False)] = True
    alpha = rng.lognormal(5.5, 0.45, n_units)
    common = rng.normal(0, 0.04, pre_days + post_days)
    noise = rng.normal(0, 0.08, (n_units, pre_days + post_days))
    untreated = alpha[:, None] * np.exp(common + noise)
    if heterogeneous and compliance_rate not in {0.0, 1.0}:
        propensity = np.clip(rng.beta(2, 2, n_units) * 2 * compliance_rate, 0, 1)
    else:
        propensity = np.full(n_units, compliance_rate)
    complies = rng.random(n_units) < propensity
    dose = np.zeros((n_units, post_days), dtype=np.float64)
    dose[assignment & complies] = 1.0
    unit_slope = rng.normal(0.08, 0.012, n_units)
    incremental = untreated[:, pre_days:] * unit_slope[:, None] * dose
    y0 = untreated[:, pre_days:].copy()
    y1 = y0 + incremental
    observed_post = np.where(assignment[:, None], y1, y0)
    itt = float((y1[assignment] - y0[assignment]).sum())
    # Structural effect per delivered unit-day is defined from the paired
    # potential-outcome response surface, even when realized delivery is zero.
    full_dose_increment = untreated[:, pre_days:] * unit_slope[:, None]
    dose_truth = float(full_dose_increment[assignment].mean())
    complier = assignment & complies
    cace = (
        float((y1[complier] - y0[complier]).sum() / max(complier.sum(), 1))
        if complier.any()
        else None
    )
    return (
        ComplianceObserved(
            world_id=world_id,
            assignment=assignment,
            delivered_dose=dose,
            pre_outcome=untreated[:, :pre_days],
            post_outcome=observed_post,
        ),
        ComplianceTruth(
            world_id=world_id,
            y_z0_d0=y0,
            y_z1_d1=y1,
            assignment_itt=itt,
            dose_response=dose_truth,
            cace=cace,
            assumptions=(
                "random_assignment",
                "exclusion",
                "monotonicity",
                "no_interference",
            ),
        ),
    )


def observed_payload(world: ComplianceObserved) -> dict[str, object]:
    """Return the estimator-visible payload; deliberately excludes truth."""
    return {
        "world_id": world.world_id,
        "assignment": world.assignment,
        "delivered_dose": world.delivered_dose,
        "pre_outcome": world.pre_outcome,
        "post_outcome": world.post_outcome,
    }
