"""Measure a small Track A pilot before setting the production compute budget."""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

from geocausal.dgp import generate_world
from geocausal.diagnostics import diagnostic_features
from geocausal.estimators import estimate_all


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    rows = []
    for index in range(16):
        scenario = f"S{index % 14:02d}"
        started = time.perf_counter()
        world, _ = generate_world(
            seed=20260909 + index,
            world_id=f"PILOT-{index:03d}",
            scenario_id=scenario,
        )
        generated = time.perf_counter()
        estimates = estimate_all(world)
        for method in estimates:
            diagnostic_features(world, method)
        ended = time.perf_counter()
        rows.append(
            {
                "world": index,
                "scenario": scenario,
                "generation_sec": generated - started,
                "estimation_and_diagnostics_sec": ended - generated,
                "total_sec": ended - started,
            }
        )
    totals = np.asarray([row["total_sec"] for row in rows])
    payload = {
        "worlds": len(rows),
        "mean_world_sec": float(totals.mean()),
        "p95_world_sec": float(np.quantile(totals, 0.95)),
        "projected_track_a_worlds": 200 + 300 + 1000 + 500 + 250,
        "projected_track_a_wall_sec_single_process": float(totals.mean() * 2250),
        "rows": rows,
    }
    output = root / "evidence" / "runtime" / "pilot_runtime.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
