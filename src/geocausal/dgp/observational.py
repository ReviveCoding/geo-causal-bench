"""Separately governed staggered-adoption panel generator."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ObservationalTruth:
    world_id: str
    scenario_id: str
    overall_att: float
    event_att: dict[int, float]


OBSERVATIONAL_SCENARIOS = tuple(f"O{i:02d}" for i in range(10))


def generate_observational_world(
    *, seed: int, world_id: str, scenario_id: str, n_units: int = 60, periods: int = 12
) -> tuple[pd.DataFrame, ObservationalTruth]:
    if scenario_id not in OBSERVATIONAL_SCENARIOS:
        raise ValueError(f"Unknown Track B scenario: {scenario_id}")
    rng = np.random.default_rng(seed)
    unit = np.repeat(np.arange(n_units), periods)
    time = np.tile(np.arange(periods), n_units)
    alpha = rng.normal(0, 1, n_units)
    x_unit = rng.normal(0, 1, n_units)
    latent = rng.normal(0, 1, n_units)
    cohort_choices = np.array([5, 7, 9, periods + 10])
    score = x_unit + (0.8 * latent if scenario_id in {"O07", "O09"} else 0)
    rank = pd.qcut(score, 4, labels=False, duplicates="drop").astype(int)
    cohorts = cohort_choices[np.clip(3 - rank, 0, 3)]
    if scenario_id == "O08":
        cohorts[: round(n_units * 0.65)] = 5
    cohort_rows = np.repeat(cohorts, periods)
    treatment = time >= cohort_rows
    event_time = time - cohort_rows
    untreated = alpha[unit] + 0.18 * time + 0.6 * x_unit[unit]
    untreated += rng.normal(0, 0.45, len(unit))
    if scenario_id in {"O01", "O02", "O09"}:
        untreated += 0.10 * x_unit[unit] * time
    if scenario_id in {"O02", "O09"}:
        untreated += 0.08 * (cohorts[unit] == 5) * time
    if scenario_id in {"O07", "O09"}:
        untreated += 0.12 * latent[unit] * time
    tau = np.full(len(unit), 1.0)
    if scenario_id in {"O03", "O09"}:
        tau *= 1 + 0.5 * (cohorts[unit] == 5)
    if scenario_id in {"O04", "O09"}:
        tau *= np.maximum(event_time + 1, 1) / 3
    anticipation = scenario_id in {"O05", "O09"}
    active = treatment | (anticipation & (event_time == -1))
    effect = tau * active
    keep = np.ones(len(unit), dtype=bool)
    if scenario_id == "O06":
        keep = ~((unit % 9 == 0) & (time >= 8))
    frame = pd.DataFrame(
        {
            "unit": unit[keep],
            "time": time[keep],
            "cohort": cohort_rows[keep],
            "x": x_unit[unit][keep],
            "treated": treatment[keep].astype(int),
            "event_time": event_time[keep],
            "outcome": (untreated + effect)[keep],
        }
    )
    event_att = {
        int(event): float(effect[(event_time == event) & treatment].mean())
        for event in sorted(set(event_time[treatment]))
    }
    return frame, ObservationalTruth(
        world_id=world_id,
        scenario_id=scenario_id,
        overall_att=float(effect[treatment].mean()),
        event_att=event_att,
    )
