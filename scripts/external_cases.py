"""Assemble claim-bounded external case-study evidence."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

root = Path(__file__).resolve().parents[1]
r_evidence = json.loads((root / "evidence/package_qualification.json").read_text())
r_results = {item["method_id"]: item for item in r_evidence["results"]}
geox = json.loads((root / "evidence/external/geox_official_summary.json").read_text())
rows = [
    {
        "dataset_id": "D2_PROP99",
        "method_id": "R3_official_synthdid",
        "estimate": r_results["synthdid_prop99"]["observed"],
        "status": r_results["synthdid_prop99"]["status"],
        "known_truth": False,
        "accuracy_ranking_allowed": False,
    },
    {
        "dataset_id": "D3_MPDTA",
        "method_id": "B2_official_did_dynamic",
        "estimate": r_results["did_mpdta_dynamic_att"]["observed"],
        "status": r_results["did_mpdta_dynamic_att"]["status"],
        "known_truth": False,
        "accuracy_ranking_allowed": False,
    },
    {
        "dataset_id": "D1_GEOLIFT_TEST",
        "method_id": "R6_official_geolift",
        "estimate": None,
        "status": r_results["geolift_official_example"]["status"],
        "failure_reason": r_results["geolift_official_example"]["failure_reason"],
        "known_truth": False,
        "accuracy_ranking_allowed": False,
    },
    {
        **geox,
        "status": "SUCCESS",
        "accuracy_ranking_allowed": False,
    },
]
frame = pd.DataFrame(rows)
output = root / "evidence" / "external" / "fact_external_case.parquet"
frame.to_parquet(output, index=False)
print(frame.to_json(orient="records", indent=2))
