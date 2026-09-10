from __future__ import annotations

import numpy as np

from geocausal.aware import AwareSelector
from geocausal.dgp import generate_world
from geocausal.diagnostics import diagnostic_features
from geocausal.estimators import estimate_all


def test_estimators_and_diagnostics_are_finite_on_clean_world():
    world, _ = generate_world(seed=42, world_id="clean", scenario_id="S00")
    estimates = estimate_all(world)
    assert estimates
    for method, estimate in estimates.items():
        assert estimate.status == "SUCCESS"
        assert np.isfinite(estimate.estimate)
        assert 0 <= estimate.p_value <= 1
        features = diagnostic_features(world, method)
        assert set(features) >= {"pre_r2", "placebo_fpr", "donor_hhi"}
        assert all(np.isfinite(value) for value in features.values())


def test_selector_round_trip_preserves_selection():
    world, _ = generate_world(seed=7, world_id="selector", scenario_id="S00")
    feature_map = {
        method: diagnostic_features(world, method) for method in estimate_all(world)
    }
    rows = list(feature_map.values()) * 3
    selector = AwareSelector(risk_limit=100)
    selector.fit(rows, np.linspace(0.1, 1.2, len(rows)))
    expected = selector.select(feature_map)
    restored = AwareSelector.restore(selector.export())
    assert restored.select(feature_map) == expected
