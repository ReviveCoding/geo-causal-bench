from __future__ import annotations

import numpy as np
import pytest

from geocausal.dgp import SCENARIOS, generate_world


@pytest.mark.scientific
@pytest.mark.parametrize("scenario", SCENARIOS)
def test_randomized_world_shapes_and_truth_separation(scenario):
    world, truth = generate_world(
        seed=123, world_id="test", scenario_id=scenario, n_geos=20, pre_days=84
    )
    assert world.outcomes.shape == (20, 119)
    assert world.assigned.sum() == 6
    assert truth.no_treatment_analysis.shape == (20, 35)
    assert not hasattr(world, "itt_total")
    assert truth.world_id == world.world_id


@pytest.mark.scientific
def test_dgp_is_deterministic_and_zero_effect_is_zero_truth():
    first, first_truth = generate_world(
        seed=9, world_id="same", scenario_id="S00", effect_scale=0
    )
    second, second_truth = generate_world(
        seed=9, world_id="same", scenario_id="S00", effect_scale=0
    )
    np.testing.assert_array_equal(first.outcomes, second.outcomes)
    assert first_truth.itt_total == second_truth.itt_total == 0


@pytest.mark.scientific
def test_noncompliance_separates_assignment_and_delivered_dose():
    _, truth = generate_world(
        seed=91, world_id="dose", scenario_id="S10", effect_scale=0.05
    )
    assert truth.itt_total == pytest.approx(truth.delivered_dose_effect)
    assert truth.itt_total > 0
