"""Execute official GeoX post-audit design and data-quality operations cells."""

from __future__ import annotations

import json
import time
from importlib import metadata
from pathlib import Path
from typing import Any

import jax
import meridian_geox as geox
import numpy as np
import pandas as pd

from geocausal.artifacts import atomic_write_json

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "evidence" / "operations"


def serializable(value: Any) -> Any:
    if isinstance(value, pd.DataFrame):
        return value.to_dict(orient="records")
    if isinstance(value, pd.Timestamp):
        return str(value)
    if isinstance(value, set):
        return sorted(map(str, value))
    if hasattr(value, "model_dump"):
        return serializable(value.model_dump())
    if hasattr(value, "__dict__"):
        return {key: serializable(item) for key, item in vars(value).items()}
    if isinstance(value, dict):
        return {str(key): serializable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [serializable(item) for item in value]
    if hasattr(value, "item"):
        return value.item()
    return value


def config(
    duration: int, assignment: str, seed: int, *, candidates: int = 2048
) -> geox.DesignConfig:
    rule = (
        geox.GeoAssignmentRule.RANDOM
        if assignment == "random"
        else geox.GeoAssignmentRule.STRATIFIED_SAMPLING
    )
    return geox.DesignConfig(
        experiment_duration=pd.Timedelta(days=duration),
        experiment_types=geox.ExperimentType.HOLDBACK,
        methodology=geox.Methodology.TBR,
        geo_assignment_rule=rule,
        design_output_count=1,
        n_candidates=candidates,
        n_ranked_candidates=100,
        seed=seed,
        min_r2=0.01,
    )


def perturb(data: pd.DataFrame, name: str, severity: float) -> pd.DataFrame:
    changed = data.copy()
    rng = np.random.default_rng(2026091300 + int(severity * 100))
    if name == "missing_conversion_days":
        rows = rng.choice(
            len(changed), max(1, round(len(changed) * severity)), replace=False
        )
        changed.loc[rows, "conversions"] = np.nan
    elif name == "duplicate_geo_date":
        extra = changed.sample(frac=severity, random_state=17)
        changed = pd.concat([changed, extra], ignore_index=True)
    elif name == "outlier_spike":
        rows = rng.choice(len(changed), max(1, len(changed) // 100), replace=False)
        changed.loc[rows, "conversions"] *= severity
    elif name == "zero_response_active_geo":
        geo = changed.groupby("location").conversions.sum().idxmax()
        changed.loc[changed.location == geo, "conversions"] = 0
    elif name == "stale_last_days":
        cutoff = changed.date.max() - pd.Timedelta(days=int(severity) - 1)
        changed = changed[changed.date < cutoff]
    elif name == "top_volume_removed":
        geo = changed.groupby("location").conversions.sum().idxmax()
        changed = changed[changed.location != geo]
    elif name == "top_volume_partial_missing":
        geo = changed.groupby("location").conversions.sum().idxmax()
        rows = changed.index[changed.location == geo]
        selected = rng.choice(rows, max(1, round(len(rows) * severity)), replace=False)
        changed.loc[selected, "conversions"] = np.nan
    elif name == "spend_positive_zero_conversions":
        rows = changed.index[changed.spend > 0][: max(1, len(changed) // 100)]
        changed.loc[rows, "conversions"] = 0
    elif name == "non_monotone_dates":
        changed = changed.sample(frac=1, random_state=23).reset_index(drop=True)
    return changed


def main() -> None:
    data = pd.read_csv(ROOT / "data/raw/D4_DESIGN_SINGLE/GeoX_design_single_cell.csv")
    data["date"] = pd.to_datetime(data["date"])
    data["location"] = data["location"].astype(str)
    totals = data.groupby("location").conversions.sum().sort_values(ascending=False)
    design_rows: list[dict[str, Any]] = []
    raw_designs: list[dict[str, Any]] = []
    started = time.perf_counter()
    for n_geos in (20, 40, 80):
        subset = data[data.location.isin(totals.head(n_geos).index)].copy()
        for duration in (14, 28, 42, 56):
            for assignment in ("random", "stratified"):
                identity = f"GEOX-{n_geos}-{duration}-{assignment}"
                if (subset.date.max() - subset.date.min()).days + 1 < 3 * duration:
                    design_rows.append(
                        {
                            "extension_id": "OPERATIONS-STUDY-001",
                            "evidence_class": "MEASURED",
                            "tool": "MERIDIAN_GEOX_1.0.1",
                            "design_id": identity,
                            "geo_count": n_geos,
                            "test_duration": duration,
                            "assignment": assignment,
                            "experiment_type": "HOLDBACK",
                            "status": "GATED_PRETEST_LT_3X_EXPERIMENT",
                        }
                    )
                    continue
                cfg = config(duration, assignment, 20260913 + n_geos + duration)
                try:
                    result = geox.compare_designs(
                        subset, [(cfg, geox.Constraints())], design_output_count=1
                    )
                    metric = result.design_metrics.iloc[0]
                    row = {
                        "extension_id": "OPERATIONS-STUDY-001",
                        "evidence_class": "MEASURED",
                        "tool": "MERIDIAN_GEOX_1.0.1",
                        "design_id": identity,
                        "geo_count": n_geos,
                        "test_duration": duration,
                        "assignment": assignment,
                        "experiment_type": "HOLDBACK",
                        "r2": metric["r2"],
                        "aa_p_value": metric["p_value (AA)"],
                        "mde": metric["mde"],
                        "mde_abs": metric["mde_abs"],
                        "budget": metric["budget"],
                        "design_cpic": metric["design_implied_cpic"],
                        "treatment_geo_count": metric["treatment_geo_count"],
                        "treatment_response_share": metric["treatment_conversions_pct"]
                        / 100,
                        "excluded_geos": n_geos - subset.location.nunique(),
                        "status": "SUCCESS",
                    }
                    design = next(iter(result.designs.values()))
                    per_cell = next(iter(design.designs.values()))
                    row["official_design_id"] = str(metric["design_id"])
                    row["treatment_geos"] = json.dumps(sorted(per_cell.treatment_geos))
                    row["control_geos"] = json.dumps(sorted(design.control_geos))
                    design_rows.append(row)
                    raw_designs.append(
                        {
                            "identity": identity,
                            "official_design_id": str(metric["design_id"]),
                            "treatment_geos": sorted(per_cell.treatment_geos),
                            "control_geos": sorted(design.control_geos),
                        }
                    )
                except Exception as error:  # official package error is evidence
                    design_rows.append(
                        {
                            "extension_id": "OPERATIONS-STUDY-001",
                            "evidence_class": "MEASURED",
                            "tool": "MERIDIAN_GEOX_1.0.1",
                            "design_id": identity,
                            "geo_count": n_geos,
                            "test_duration": duration,
                            "assignment": assignment,
                            "experiment_type": "HOLDBACK",
                            "status": "PACKAGE_FAILURE",
                            "failure_reason": f"{type(error).__name__}: {error}",
                        }
                    )
    quality_levels = {
        "missing_conversion_days": [0.01, 0.05, 0.1, 0.2, 0.3],
        "duplicate_geo_date": [0.01, 0.05, 0.1],
        "outlier_spike": [2, 5, 10],
        "zero_response_active_geo": [1],
        "stale_last_days": [7, 14],
        "top_volume_removed": [1],
        "top_volume_partial_missing": [0.1],
        "spend_positive_zero_conversions": [1],
        "non_monotone_dates": [1],
    }
    quality_rows = []
    cfg = config(28, "stratified", 20260913, candidates=512)
    for name, levels in quality_levels.items():
        for severity in levels:
            changed = perturb(data, name, float(severity))
            try:
                result = geox.check_design_data_quality(
                    changed, cfg, geox.QualityCheckConfig()
                )
                payload = serializable(result)
                design_available = False
                design_failure_reason = None
                design_metrics: dict[str, Any] = {}
                try:
                    design_result = geox.compare_designs(
                        changed,
                        [(cfg, geox.Constraints())],
                        design_output_count=1,
                    )
                    metric = design_result.design_metrics.iloc[0]
                    design_available = True
                    design_metrics = {
                        "r2": metric["r2"],
                        "mde": metric["mde"],
                        "mde_abs": metric["mde_abs"],
                        "budget": metric["budget"],
                        "aa_p_value": metric["p_value (AA)"],
                        "treatment_geo_count": metric["treatment_geo_count"],
                        "treatment_response_share": metric["treatment_conversions_pct"]
                        / 100,
                    }
                except Exception as design_error:
                    design_failure_reason = (
                        f"{type(design_error).__name__}: {design_error}"
                    )
                quality_rows.append(
                    {
                        "extension_id": "OPERATIONS-STUDY-001",
                        "evidence_class": "MEASURED",
                        "perturbation": name,
                        "severity": severity,
                        "geox_validation_result": "PASS",
                        "geox_quality_warning": json.dumps(
                            payload, sort_keys=True, default=str
                        ),
                        "excluded_geos": len(result.outlier_geos),
                        "excluded_dates": len(result.outlier_dates),
                        "design_available": design_available,
                        "design_failure_reason": design_failure_reason,
                        "status": "OFFICIAL_QUALITY_AND_DESIGN_EXECUTED",
                        **design_metrics,
                    }
                )
            except Exception as error:
                quality_rows.append(
                    {
                        "extension_id": "OPERATIONS-STUDY-001",
                        "evidence_class": "MEASURED",
                        "perturbation": name,
                        "severity": severity,
                        "geox_validation_result": "HARD_ERROR",
                        "geox_quality_warning": f"{type(error).__name__}: {error}",
                        "excluded_geos": 0,
                        "excluded_dates": 0,
                        "design_available": False,
                        "status": "OFFICIAL_QUALITY_CHECK_ERROR",
                    }
                )

    # Same-panel holdback comparison: GeoLift public history has no daily spend.
    common = pd.read_csv(ROOT / "data/staged/D1_PRE/GeoLift_PreTest.csv")
    common = common.rename(columns={"Y": "conversions"})
    common["conversions"] = common["conversions"].astype("float64")
    common["date"] = pd.to_datetime(common["date"])
    common["location"] = common["location"].astype(str)
    common_rows = []
    for assignment in ("random", "stratified"):
        cfg_common = config(10, assignment, 2026091401)
        try:
            result = geox.compare_designs(
                common,
                [(cfg_common, geox.Constraints())],
                design_output_count=1,
            )
            metric = result.design_metrics.iloc[0]
            design = next(iter(result.designs.values()))
            per_cell = next(iter(design.designs.values()))
            common_rows.append(
                {
                    "extension_id": "OPERATIONS-STUDY-001",
                    "evidence_class": "POST_AUDIT_EXTERNAL",
                    "dataset_id": "D1_GEOLIFT_PRE_COMMON_PANEL",
                    "tool": "MERIDIAN_GEOX_1.0.1",
                    "assignment": assignment,
                    "status": "SUCCESS",
                    "treatment_geos": json.dumps(sorted(per_cell.treatment_geos)),
                    "control_geos": json.dumps(sorted(design.control_geos)),
                    "treatment_geo_count": metric["treatment_geo_count"],
                    "treatment_response_share": metric["treatment_conversions_pct"]
                    / 100,
                    "r2": metric["r2"],
                    "aa_p_value": metric["p_value (AA)"],
                    "mde": metric["mde"],
                    "mde_abs": metric["mde_abs"],
                    "budget": metric["budget"],
                    "design_cpic": metric["design_implied_cpic"],
                }
            )
        except Exception as error:
            common_rows.append(
                {
                    "extension_id": "OPERATIONS-STUDY-001",
                    "evidence_class": "POST_AUDIT_EXTERNAL",
                    "dataset_id": "D1_GEOLIFT_PRE_COMMON_PANEL",
                    "tool": "MERIDIAN_GEOX_1.0.1",
                    "assignment": assignment,
                    "status": "PACKAGE_FAILURE",
                    "failure_reason": f"{type(error).__name__}: {error}",
                }
            )
    official_design = pd.DataFrame(design_rows)
    official_quality = pd.DataFrame(quality_rows)
    official_design.to_parquet(
        OUTPUT / "geox_official_design_frontier.parquet", index=False
    )
    official_quality.to_parquet(
        OUTPUT / "geox_official_quality_stress.parquet", index=False
    )
    pd.DataFrame(common_rows).to_parquet(
        OUTPUT / "geox_common_panel_design.parquet", index=False
    )
    atomic_write_json(
        OUTPUT / "geox_operations.json",
        {
            "extension_id": "OPERATIONS-STUDY-001",
            "package": "meridian-geox",
            "version": metadata.version("meridian-geox"),
            "jax_backend": jax.default_backend(),
            "jax_devices": [str(device) for device in jax.devices()],
            "runtime_sec": time.perf_counter() - started,
            "design_rows": len(official_design),
            "quality_rows": len(official_quality),
            "common_panel_rows": len(common_rows),
            "raw_designs": raw_designs,
        },
    )
    print(official_design.status.value_counts(dropna=False).to_dict())
    print(official_quality.geox_validation_result.value_counts().to_dict())


if __name__ == "__main__":
    main()
