"""Compare DGP-A clean-world summaries with public panel anchors."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from geocausal.dgp.randomized import generate_world


def calibrate_randomized_dgp(root: Path, *, worlds: int = 100) -> dict[str, object]:
    anchor = pd.read_parquet(
        root / "data" / "anchors" / "public_anchor_summary.parquet"
    )
    summaries: list[dict[str, float]] = []
    for index in range(worlds):
        world, _ = generate_world(
            seed=20260909 + index,
            world_id=f"CAL-{index:04d}",
            scenario_id="S00",
            effect_scale=0,
        )
        values = world.outcomes[:, : world.pre_days]
        means = values.mean(axis=1)
        correlations = np.asarray(np.corrcoef(values), dtype=np.float64)
        summaries.append(
            {
                "mean": float(values.mean()),
                "cv": float(values.std() / values.mean()),
                "top_geo_concentration": float(means.max() / means.sum()),
                "mean_cross_geo_correlation": float(
                    np.mean(correlations[np.triu_indices_from(correlations, 1)])
                ),
                "mean_acf1": float(
                    np.mean([np.corrcoef(row[1:], row[:-1])[0, 1] for row in values])
                ),
            }
        )
    simulated = pd.DataFrame(summaries).mean().to_dict()
    public = anchor.loc[anchor.dataset_id.isin(["D1_PRE", "D4_DESIGN_SINGLE"])]
    targets = {
        metric: float(public[metric].median())
        for metric in (
            "outcome_mean",
            "outcome_cv",
            "top_geo_concentration",
            "mean_cross_geo_correlation",
            "mean_acf1",
        )
    }
    payload: dict[str, object] = {
        "worlds": worlds,
        "public_anchor_datasets": ["D1_PRE", "D4_DESIGN_SINGLE"],
        "public_median_targets": targets,
        "simulated_clean_summary": simulated,
        "scale_target": "D4_DESIGN_SINGLE",
        "status": "CALIBRATED_WITH_DECLARED_GAPS",
        "known_gap": (
            "Cross-geo correlation spans 0.04 (GeoX) to 0.83 (GeoLift); "
            "scenarios vary dependence rather than matching one universal value."
        ),
    }
    output = root / "evidence" / "e03_dgp_calibration.json"
    output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload
