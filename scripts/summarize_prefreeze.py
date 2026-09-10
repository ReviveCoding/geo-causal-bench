"""Create compact E07-E12 summaries from canonical pre-freeze Parquet."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


root = Path(__file__).resolve().parents[1]
development = pd.read_parquet(root / "evidence/development/fact_estimator_result.parquet")
null = pd.read_parquet(root / "evidence/qualification/fact_null_result.parquet")
ood = pd.read_parquet(root / "evidence/qualification/fact_ood_estimator_result.parquet")
qualification = json.loads(
    (root / "evidence/qualification/summary.json").read_text(encoding="utf-8")
)


def method_summary(frame: pd.DataFrame) -> list[dict[str, object]]:
    result = (
        frame.groupby("method_id")
        .agg(
            worlds=("world_id", "nunique"),
            rmse=("sq_error", lambda value: float(np.sqrt(value.mean()))),
            coverage=("covered_truth", "mean"),
            rejection=("reject_null", "mean"),
            failure_rate=("status", lambda value: float((value != "SUCCESS").mean())),
        )
        .reset_index()
    )
    return result.to_dict(orient="records")


payload = {
    "E07_clean": method_summary(development.loc[development.scenario_id == "S00"]),
    "E08_null": method_summary(null),
    "E09_single_stress": method_summary(
        development.loc[development.scenario_id.isin([f"S{i:02d}" for i in range(1, 13)])]
    ),
    "E10_compound_ood": method_summary(ood),
    "E11_development_rows": len(development),
    "E12_qualification": qualification,
}
output = root / "evidence" / "pre_freeze_summary.json"
output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
print(json.dumps(payload, indent=2, sort_keys=True))
