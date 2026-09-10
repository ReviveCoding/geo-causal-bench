"""Extract compact official GeoX external-case results from bundled provenance."""

from __future__ import annotations

import inspect
import json
from pathlib import Path

import meridian_geox as geox
import pandas as pd

root = Path(__file__).resolve().parents[1]
package_root = Path(inspect.getfile(geox)).resolve().parent
data_root = package_root / "data"
data = pd.read_csv(data_root / "example_analysis_data_single_cell_holdback.csv")
data["date"] = pd.to_datetime(data["date"])
data["location"] = data["location"].astype(str)
design = geox.Design.load_from_json(
    (data_root / "example_design_stratified_sampling_holdback.json").read_text()
)
result = geox.analyze(
    data,
    geox.AnalysisConfig(
        design=design,
        analysis_start_date=pd.Timestamp("2020-04-01"),
        analysis_end_date=pd.Timestamp("2020-04-30"),
    ),
    geox.QualityCheckConfig(exclude_outlier_dates=True),
).results["cell_1"]
last_lift = result.cumulative_lift.iloc[-1]
payload = {
    "dataset_id": "D4_ANALYSIS_SINGLE",
    "method_id": "R1_official_geox_tbr",
    "estimate": float(last_lift["lift"]),
    "ci_low": float(last_lift["lower_bound"]),
    "ci_high": float(last_lift["upper_bound"]),
    "percent_lift": float(result.percent_lift.point_estimate),
    "p_value": float(result.percent_lift.p_value),
    "analysis_days": len(result.cumulative_lift),
    "known_truth": False,
    "design_provenance_retained": True,
}
output = root / "evidence" / "external" / "geox_official_summary.json"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
print(json.dumps(payload, indent=2, sort_keys=True))
