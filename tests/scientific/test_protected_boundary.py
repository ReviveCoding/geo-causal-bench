from __future__ import annotations

import inspect

from geocausal.simulation import protected


def test_truth_blind_evaluator_does_not_read_seed_or_truth_store():
    source = inspect.getsource(protected.evaluate_without_truth)
    assert "final_world_seeds" not in source
    assert "truth_root" not in source
    assert "itt_total" not in source


def test_scoring_uses_committed_materiality_not_true_effect_materiality():
    source = inspect.getsource(protected.score_committed_once)
    assert 'materiality = float(row["materiality"])' in source
    assert "max(abs(true_effect)" not in source
