from geocausal.decision import decide
from geocausal.estimators import Estimate


def estimate(value: float, low: float, high: float) -> Estimate:
    return Estimate("test", value, 1.0, low, high, 0.5)


def test_launch_hold_stop_redesign_and_costs():
    launch = decide(estimate(12, 11, 13), 12, materiality=10)
    assert launch.decision == "LAUNCH" and launch.regret == 0

    false_launch = decide(estimate(12, 11, 13), -2, materiality=10)
    assert false_launch.false_launch and false_launch.regret > 3

    false_stop = decide(estimate(-3, -5, -1), 12, materiality=10)
    assert false_stop.false_stop and false_stop.regret > 1.5

    hold = decide(estimate(2, -1, 5), 2, materiality=10)
    assert hold.decision == "HOLD" and hold.regret == 0.4

    redesign = decide(None, 12, materiality=10)
    assert redesign.decision == "REDESIGN" and redesign.regret == 0.35

    stop_hold = decide(estimate(-3, -5, -1), 1, materiality=10)
    assert stop_hold.regret == 0.5
