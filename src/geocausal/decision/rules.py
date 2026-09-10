"""Uncertainty-aware synthetic business decisions."""

from __future__ import annotations

from dataclasses import dataclass

from geocausal.estimators import Estimate


@dataclass(frozen=True)
class DecisionResult:
    decision: str
    oracle_decision: str
    regret: float
    false_launch: bool
    false_stop: bool


def _oracle(true_value: float, materiality: float) -> str:
    if true_value >= materiality:
        return "LAUNCH"
    if true_value < 0:
        return "STOP"
    return "HOLD"


def decide(
    estimate: Estimate | None, true_value: float, *, materiality: float
) -> DecisionResult:
    oracle = _oracle(true_value, materiality)
    if estimate is None:
        decision = "REDESIGN"
    elif estimate.ci_low >= materiality:
        decision = "LAUNCH"
    elif estimate.ci_high < 0:
        decision = "STOP"
    else:
        decision = "HOLD"
    false_launch = decision == "LAUNCH" and oracle != "LAUNCH"
    false_stop = decision == "STOP" and oracle == "LAUNCH"
    costs = {"LAUNCH": 0.0, "STOP": 0.0, "HOLD": 0.4, "REDESIGN": 0.35}
    regret = costs[decision]
    if false_launch:
        regret += 3.0 + min(2.0, abs(true_value) / max(materiality, 1))
    if false_stop:
        regret += 1.5 + min(2.0, true_value / max(materiality, 1))
    if decision == "STOP" and oracle == "HOLD":
        regret += 0.5
    return DecisionResult(decision, oracle, float(regret), false_launch, false_stop)
