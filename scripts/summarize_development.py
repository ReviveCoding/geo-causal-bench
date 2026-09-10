"""Summarize development-only diagnostics for pre-freeze threshold setting."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

root = Path(__file__).resolve().parents[1]
frame = pd.read_parquet(
    root / "evidence" / "development" / "fact_estimator_result.parquet"
)
metrics = [
    "pre_r2",
    "pre_rmse",
    "trend_gap",
    "acf_score",
    "placebo_fpr",
    "donor_hhi",
    "effective_donors",
    "missingness",
]
summary = {}
for method, group in frame.groupby("method_id"):
    summary[str(method)] = {
        metric: {
            "min": float(group[metric].min()),
            "p05": float(group[metric].quantile(0.05)),
            "median": float(group[metric].median()),
            "p95": float(group[metric].quantile(0.95)),
            "max": float(group[metric].max()),
        }
        for metric in metrics
    }
print(json.dumps(summary, indent=2, sort_keys=True))
