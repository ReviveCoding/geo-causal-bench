"""Run the installed official GeoX single-cell design and analysis examples."""

from __future__ import annotations

import dataclasses
import inspect
import json
import sys
import time
from importlib import metadata
from pathlib import Path
from typing import Any

import meridian_geox as geox
import pandas as pd


def jsonable(value: Any) -> Any:
    if dataclasses.is_dataclass(value):
        return {
            field.name: jsonable(getattr(value, field.name))
            for field in dataclasses.fields(value)
        }
    if isinstance(value, pd.DataFrame):
        return {
            "columns": list(value.columns),
            "rows": len(value),
            "head": jsonable(value.head(5).to_dict(orient="records")),
        }
    if isinstance(value, pd.Series):
        return value.head(20).tolist()
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    if hasattr(value, "item"):
        try:
            return value.item()
        except (TypeError, ValueError):
            pass
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (pd.Timestamp, pd.Timedelta)):
        return str(value)
    return repr(value)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    output = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else root / "evidence" / "geox_qualification.json"
    )
    package_root = Path(inspect.getfile(geox)).resolve().parent
    data_root = package_root / "data"

    analysis_data = pd.read_csv(
        data_root / "example_analysis_data_single_cell_holdback.csv"
    )
    analysis_data["date"] = pd.to_datetime(analysis_data["date"])
    analysis_data["location"] = analysis_data["location"].astype(str)
    design_text = (
        data_root / "example_design_stratified_sampling_holdback.json"
    ).read_text(encoding="utf-8")
    loaded_design = geox.Design.load_from_json(design_text)
    analysis_config = geox.AnalysisConfig(
        design=loaded_design,
        analysis_start_date=pd.to_datetime("2020-04-01"),
        analysis_end_date=pd.to_datetime("2020-04-30"),
    )
    started = time.perf_counter()
    analysis_result = geox.analyze(
        analysis_data,
        analysis_config,
        geox.QualityCheckConfig(exclude_outlier_dates=True),
    )
    analysis_sec = time.perf_counter() - started

    design_data = pd.read_csv(data_root / "example_design_data_single_cell.csv")
    design_data["date"] = pd.to_datetime(design_data["date"])
    design_data["location"] = design_data["location"].astype(str)
    comparison_started = time.perf_counter()
    comparison = geox.compare_designs(
        design_data,
        [
            (
                geox.DesignConfig(
                    experiment_duration=pd.Timedelta(days=30),
                    experiment_types=geox.ExperimentType.HOLDBACK,
                    methodology=geox.Methodology.TBR,
                    geo_assignment_rule=geox.GeoAssignmentRule.RANDOM,
                ),
                geox.Constraints(),
            ),
            (
                geox.DesignConfig(
                    experiment_duration=pd.Timedelta(days=30),
                    experiment_types=geox.ExperimentType.HOLDBACK,
                    methodology=geox.Methodology.TBR,
                    geo_assignment_rule=geox.GeoAssignmentRule.STRATIFIED_SAMPLING,
                ),
                geox.Constraints(),
            ),
        ],
    )
    comparison_sec = time.perf_counter() - comparison_started
    payload = {
        "package": "meridian-geox",
        "version": metadata.version("meridian-geox"),
        "official_design_artifact_retained": True,
        "design_artifact_source": str(
            data_root / "example_design_stratified_sampling_holdback.json"
        ),
        "analysis_runtime_sec": analysis_sec,
        "design_comparison_runtime_sec": comparison_sec,
        "analysis_result": jsonable(analysis_result),
        "design_comparison": jsonable(comparison),
        "status": "PASS",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
