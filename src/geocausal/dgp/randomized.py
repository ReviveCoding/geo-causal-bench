"""Public-anchor-shaped randomized geo panel generator."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

FloatArray = npt.NDArray[np.float64]
BoolArray = npt.NDArray[np.bool_]


@dataclass(frozen=True)
class ObservedWorld:
    world_id: str
    scenario_id: str
    outcomes: FloatArray
    spend: FloatArray
    assigned: BoolArray
    delivered_dose: FloatArray
    pre_days: int
    test_days: int
    cooldown_days: int

    @property
    def analysis_slice(self) -> slice:
        return slice(self.pre_days, self.pre_days + self.test_days + self.cooldown_days)

    def pre_treatment_view(self) -> tuple[FloatArray, FloatArray, BoolArray]:
        return (
            self.outcomes[:, : self.pre_days],
            self.spend[:, : self.pre_days],
            self.assigned,
        )


@dataclass(frozen=True)
class TruthRecord:
    world_id: str
    scenario_id: str
    itt_total: float
    delivered_dose_effect: float
    no_treatment_analysis: FloatArray


SCENARIOS = tuple(f"S{i:02d}" for i in range(14))


def _stratified_assignment(
    baseline: FloatArray, n_treated: int, rng: np.random.Generator
) -> BoolArray:
    order = np.argsort(baseline)
    assigned = np.zeros(len(baseline), dtype=bool)
    pairs = np.array_split(order, n_treated)
    for group in pairs:
        assigned[rng.choice(group)] = True
    if assigned.sum() > n_treated:
        selected = np.flatnonzero(assigned)
        assigned[rng.choice(selected, assigned.sum() - n_treated, replace=False)] = (
            False
        )
    while assigned.sum() < n_treated:
        available = np.flatnonzero(~assigned)
        assigned[rng.choice(available)] = True
    return assigned


def generate_world(
    *,
    seed: int,
    world_id: str,
    scenario_id: str,
    n_geos: int = 40,
    pre_days: int = 168,
    test_days: int = 28,
    cooldown_days: int = 7,
    treatment_share: float = 0.30,
    effect_scale: float = 0.05,
) -> tuple[ObservedWorld, TruthRecord]:
    """Generate one world while returning observed data and truth separately."""
    if scenario_id not in SCENARIOS:
        raise ValueError(f"Unknown Track A scenario: {scenario_id}")
    rng = np.random.default_rng(seed)
    total_days = pre_days + test_days + cooldown_days
    time = np.arange(total_days, dtype=np.float64)
    # GeoX's public single-cell panel anchors a mean near 535 and CV near 0.66.
    # The log-scale intercept/dispersion are frozen only after E03 validation.
    alpha = rng.normal(6.1, 0.55, n_geos)
    loadings = rng.normal(0.0, 0.22, (n_geos, 2))
    factors = np.vstack(
        [np.sin(2 * np.pi * time / 31), np.cumsum(rng.normal(0, 0.035, total_days))]
    )
    dow = 0.12 * np.sin(2 * np.pi * time / 7) + 0.06 * np.cos(2 * np.pi * time / 7)
    slow = 0.08 * np.sin(2 * np.pi * time / 180)
    trends = rng.normal(0, 0.0007, n_geos)[:, None] * time
    eta = alpha[:, None] + dow + slow + loadings @ factors + trends

    ar = np.zeros((n_geos, total_days), dtype=np.float64)
    innovations = rng.normal(0, 0.10, (n_geos, total_days))
    common = rng.normal(0, 0.035, total_days)
    phi1, phi2 = (0.45, 0.0)
    if scenario_id == "S02":
        phi1, phi2 = (0.65, -0.25)
    for day in range(2, total_days):
        ar[:, day] = (
            phi1 * ar[:, day - 1]
            + phi2 * ar[:, day - 2]
            + innovations[:, day]
            + common[day]
        )
    eta += ar

    if scenario_id == "S01":
        eta[:, pre_days:] += rng.normal(0, 0.004, n_geos)[:, None] * np.arange(
            total_days - pre_days
        )
    if scenario_id in {"S03", "S13"}:
        eta[:, pre_days:] += loadings[:, [0]] * np.linspace(
            0, 1.1, total_days - pre_days
        )
    if scenario_id in {"S04", "S13"}:
        eta[:, pre_days:] += rng.normal(0, 0.28, n_geos)[:, None]
    if scenario_id == "S12":
        eta[:, pre_days + 5 : pre_days + 10] += rng.normal(0.25, 0.10, n_geos)[:, None]

    mean = np.exp(np.clip(eta, 0.5, 7.5))
    dispersion = 18.0
    gamma_rate = rng.gamma(dispersion, mean / dispersion)
    untreated = rng.poisson(gamma_rate).astype(np.float64)
    baseline = untreated[:, :pre_days].mean(axis=1)
    n_treated = max(2, round(n_geos * treatment_share))
    assigned = _stratified_assignment(baseline, n_treated, rng)

    base_spend = np.maximum(
        0, baseline[:, None] * rng.uniform(0.5, 1.2, n_geos)[:, None]
    )
    spend = np.repeat(base_spend, total_days, axis=1)
    delivered = np.zeros_like(spend)
    delivered[assigned, pre_days : pre_days + test_days] = 1.0
    if scenario_id in {"S10", "S13"}:
        compliance = rng.beta(3, 2, assigned.sum())
        delivered[assigned, pre_days : pre_days + test_days] *= compliance[:, None]

    geo_effect = np.full(n_geos, effect_scale)
    if scenario_id == "S05":
        geo_effect = rng.normal(effect_scale, abs(effect_scale) * 1.2 + 0.01, n_geos)
    effect = untreated * geo_effect[:, None] * delivered

    if scenario_id in {"S06", "S13"}:
        # Deterministic ring-lattice adjacency: each geo has its two nearest
        # neighbors. Only exposure from assigned neighbors induces spillover.
        neighbors = np.roll(assigned, 1) | np.roll(assigned, -1)
        effect[neighbors & ~assigned, pre_days : pre_days + test_days] += (
            untreated[neighbors & ~assigned, pre_days : pre_days + test_days]
            * effect_scale
            * 0.25
        )
    if scenario_id in {"S07", "S13"}:
        contaminated = (~assigned) & (np.arange(n_geos) % 7 == 0)
        effect[contaminated, pre_days : pre_days + test_days] += (
            untreated[contaminated, pre_days : pre_days + test_days]
            * effect_scale
            * 0.4
        )
    if scenario_id == "S11":
        decay = np.exp(-np.arange(cooldown_days) / 3.0)
        effect[assigned, pre_days + test_days :] = (
            untreated[assigned, pre_days + test_days :]
            * geo_effect[assigned, None]
            * decay
        )
    if scenario_id == "S08":
        untreated[0] *= 12
        effect[0] *= 12
    observed = untreated + effect
    if scenario_id in {"S09", "S13"}:
        shock_days = rng.choice(
            total_days, size=max(2, total_days // 50), replace=False
        )
        observed[:, shock_days] *= rng.uniform(0.1, 3.0, (n_geos, len(shock_days)))
        missing = rng.random(observed.shape) < 0.015
        observed[missing] = np.nan

    analysis = slice(pre_days, total_days)
    direct_itt = float(effect[assigned, analysis].sum())
    delivered_effect = float(
        (untreated * geo_effect[:, None] * delivered)[assigned, analysis].sum()
    )
    return (
        ObservedWorld(
            world_id=world_id,
            scenario_id=scenario_id,
            outcomes=observed,
            spend=spend,
            assigned=assigned,
            delivered_dose=delivered,
            pre_days=pre_days,
            test_days=test_days,
            cooldown_days=cooldown_days,
        ),
        TruthRecord(
            world_id=world_id,
            scenario_id=scenario_id,
            itt_total=direct_itt,
            delivered_dose_effect=delivered_effect,
            no_treatment_analysis=untreated[:, analysis],
        ),
    )
