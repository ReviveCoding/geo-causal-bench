import pytest

from geocausal.dgp import OBSERVATIONAL_SCENARIOS, generate_observational_world


@pytest.mark.scientific
@pytest.mark.parametrize("scenario", OBSERVATIONAL_SCENARIOS)
def test_observational_scenarios_have_separate_truth(scenario):
    frame, truth = generate_observational_world(
        seed=99, world_id="obs", scenario_id=scenario
    )
    assert {"unit", "time", "cohort", "treated", "event_time", "outcome"} <= set(frame)
    assert truth.overall_att > 0
    assert not hasattr(frame, "overall_att")


def test_observational_unknown_scenario_rejected():
    with pytest.raises(ValueError):
        generate_observational_world(seed=1, world_id="bad", scenario_id="O99")
