"""Validate acquired panels and create compact public-data anchor evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from geocausal.artifacts import canonical_hash


def _read_source(root: Path, source_id: str) -> pd.DataFrame:
    staged = sorted((root / "data" / "staged" / source_id).glob("*.csv"))
    raw = sorted((root / "data" / "raw" / source_id).glob("*.csv"))
    path = (staged or raw)[0]
    first = path.read_text(encoding="utf-8", errors="ignore").splitlines()[0]
    separator = ";" if first.count(";") > first.count(",") else ","
    return pd.read_csv(path, sep=separator)


def _panel_summary(source_id: str, frame: pd.DataFrame) -> dict[str, Any]:
    columns = {str(column).lower(): str(column) for column in frame.columns}
    geo_column = next(
        (
            columns[name]
            for name in ("location", "state", "countyreal")
            if name in columns
        ),
        None,
    )
    date_column = next(
        (columns[name] for name in ("date", "year") if name in columns), None
    )
    outcome_column = next(
        (
            columns[name]
            for name in ("y", "conversions", "packspercapita", "lemp")
            if name in columns
        ),
        None,
    )
    duplicate_keys = 0
    if geo_column and date_column:
        duplicate_keys = int(frame.duplicated([geo_column, date_column]).sum())
    summary: dict[str, Any] = {
        "dataset_id": source_id,
        "rows": len(frame),
        "columns": len(frame.columns),
        "geos": int(frame[geo_column].nunique()) if geo_column else None,
        "dates": int(frame[date_column].nunique()) if date_column else None,
        "duplicate_rows": int(frame.duplicated().sum()),
        "duplicate_geo_date_keys": duplicate_keys,
        "missing_cells": int(frame.isna().sum().sum()),
        "schema_hash": canonical_hash(
            [{"name": str(k), "dtype": str(v)} for k, v in frame.dtypes.items()]
        ),
    }
    if outcome_column:
        outcome = pd.to_numeric(frame[outcome_column], errors="coerce")
        positive_mean = max(abs(float(outcome.mean())), 1e-12)
        q1, q3 = outcome.quantile([0.25, 0.75])
        iqr = max(float(q3 - q1), 1e-12)
        summary |= {
            "outcome": outcome_column,
            "outcome_mean": float(outcome.mean()),
            "outcome_variance": float(outcome.var()),
            "outcome_cv": float(outcome.std() / positive_mean),
            "zero_fraction": float((outcome == 0).mean()),
            "negative_outcomes": int((outcome < 0).sum()),
            "outlier_fraction_iqr": float(
                ((outcome < q1 - 3 * iqr) | (outcome > q3 + 3 * iqr)).mean()
            ),
        }
        if geo_column:
            geo_means = (
                outcome.groupby(frame[geo_column]).mean().sort_values(ascending=False)
            )
            summary["top_geo_concentration"] = float(
                geo_means.iloc[0] / max(float(geo_means.sum()), 1e-12)
            )
        if geo_column and date_column:
            pivot = frame.assign(_outcome=outcome).pivot(
                index=date_column, columns=geo_column, values="_outcome"
            )
            corr_values: list[float] = []
            if pivot.shape[1] > 1:
                corr = pivot.corr().to_numpy()
                corr_values = corr[np.triu_indices_from(corr, 1)].tolist()
            acfs = [
                float(pivot[column].dropna().autocorr(1))
                for column in pivot
                if len(pivot[column].dropna()) > 2
            ]
            summary["mean_cross_geo_correlation"] = float(np.nanmean(corr_values))
            summary["mean_acf1"] = float(np.nanmean(acfs))
    spend_column = columns.get("spend")
    if spend_column:
        spend = pd.to_numeric(frame[spend_column], errors="coerce")
        summary["negative_spend"] = int((spend < 0).sum())
        summary["zero_spend_fraction"] = float((spend == 0).mean())
    return summary


def characterize_public_data(root: Path) -> dict[str, Any]:
    summaries = [
        _panel_summary(source_id, _read_source(root, source_id))
        for source_id in ("D1_PRE", "D1_TEST", "D2", "D3", "D4_DESIGN_SINGLE")
    ]
    anchor = pd.DataFrame(summaries)
    anchor_path = root / "data" / "anchors" / "public_anchor_summary.parquet"
    anchor_path.parent.mkdir(parents=True, exist_ok=True)
    anchor.to_parquet(anchor_path, index=False)
    checks = {
        "datasets": len(summaries),
        "all_no_duplicate_keys": all(
            item["duplicate_geo_date_keys"] == 0 for item in summaries
        ),
        "all_nonnegative_primary_outcomes": all(
            item.get("negative_outcomes", 0) == 0 for item in summaries
        ),
        "summaries": summaries,
    }
    output = root / "evidence" / "e02_public_validation.json"
    output.write_text(json.dumps(checks, indent=2, sort_keys=True), encoding="utf-8")
    return checks
