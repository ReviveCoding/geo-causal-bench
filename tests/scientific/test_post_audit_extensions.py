from __future__ import annotations

import numpy as np

from geocausal.post_audit.compliance import (
    generate_compliance_world,
    observed_payload,
)
from geocausal.post_audit.influence import influence_summary


def test_compliance_truth_is_not_in_observed_payload() -> None:
    observed, truth = generate_compliance_world(
        seed=7, world_id="test", compliance_rate=0.5, heterogeneous=False
    )
    payload = observed_payload(observed)
    assert not ({"assignment_itt", "dose_response", "cace"} & payload.keys())
    assert truth.assignment_itt >= 0


def test_zero_and_full_compliance_semantics() -> None:
    _, zero = generate_compliance_world(
        seed=8, world_id="zero", compliance_rate=0, heterogeneous=False
    )
    observed, full = generate_compliance_world(
        seed=8, world_id="full", compliance_rate=1, heterogeneous=False
    )
    assert zero.assignment_itt == 0
    assert zero.dose_response > 0
    realized = float(
        (full.y_z1_d1[observed.assignment] - full.y_z0_d0[observed.assignment]).sum()
    )
    assert full.assignment_itt == realized


def test_influence_dimensions_and_roles() -> None:
    outcomes = np.arange(48, dtype=float).reshape(6, 8)
    treated = np.array([True, True, False, False, False, False])

    def estimator(data: np.ndarray, assigned: np.ndarray) -> float:
        return float(data[assigned].mean() - data[~assigned].mean())

    rows = influence_summary(outcomes, treated, estimator)
    assert len(rows) == 6
    assert {row["removed_role"] for row in rows} == {"treatment", "control"}
