"""Pinned public-data acquisition with byte and schema manifests."""

from __future__ import annotations

import csv
import subprocess
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from geocausal.artifacts import atomic_write_json, canonical_hash, sha256_file, utc_now


@dataclass(frozen=True)
class Source:
    source_id: str
    source_name: str
    commit: str
    relative_path: str
    origin: str
    license_name: str
    redistribution: str
    role: str

    @property
    def url(self) -> str:
        return f"{self.origin}/{self.commit}/{self.relative_path}"


GEOX_COMMIT = "0a1dd0f730ab8170e4e46646f3bf69400d57d021"
GEOLIFT_COMMIT = "db34ea4299ff0e28515ebac502b78c076c93c905"
SYNTHDID_COMMIT = "70c1ce3eac58e28c30b67435ca377bb48baa9b8a"
DID_COMMIT = "74b88eb07f1faa644df1271055a0f77848f6550c"

SOURCES = (
    Source(
        "D1_PRE",
        "GeoLift_PreTest",
        GEOLIFT_COMMIT,
        "data/GeoLift_PreTest.rda",
        "https://raw.githubusercontent.com/facebookincubator/GeoLift",
        "MIT",
        "permitted_with_attribution",
        "anchor_and_external_case",
    ),
    Source(
        "D1_TEST",
        "GeoLift_Test",
        GEOLIFT_COMMIT,
        "data/GeoLift_Test.rda",
        "https://raw.githubusercontent.com/facebookincubator/GeoLift",
        "MIT",
        "permitted_with_attribution",
        "external_case",
    ),
    Source(
        "D2",
        "California_Proposition_99",
        SYNTHDID_COMMIT,
        "data/california_prop99.csv",
        "https://raw.githubusercontent.com/synth-inference/synthdid",
        "MIT",
        "permitted_with_attribution",
        "known_answer_and_external_case",
    ),
    Source(
        "D3",
        "Callaway_SantAnna_mpdta",
        DID_COMMIT,
        "data/mpdta.rda",
        "https://raw.githubusercontent.com/bcallaway11/did",
        "GPL-3",
        "source_package_terms_apply",
        "known_answer_and_external_case",
    ),
    Source(
        "D4_DESIGN_SINGLE",
        "GeoX_design_single_cell",
        GEOX_COMMIT,
        "meridian_geox/data/example_design_data_single_cell.csv",
        "https://raw.githubusercontent.com/google/meridian-geox",
        "Apache-2.0",
        "permitted_with_attribution",
        "official_example",
    ),
    Source(
        "D4_ANALYSIS_SINGLE",
        "GeoX_analysis_single_cell_holdback",
        GEOX_COMMIT,
        "meridian_geox/data/example_analysis_data_single_cell_holdback.csv",
        "https://raw.githubusercontent.com/google/meridian-geox",
        "Apache-2.0",
        "permitted_with_attribution",
        "official_example",
    ),
    Source(
        "D4_DESIGN_MULTI",
        "GeoX_design_multi_cell",
        GEOX_COMMIT,
        "meridian_geox/data/example_design_data_multi_cell_go_dark_heavy_up.csv",
        "https://raw.githubusercontent.com/google/meridian-geox",
        "Apache-2.0",
        "permitted_with_attribution",
        "optional_official_example",
    ),
    Source(
        "D4_ANALYSIS_MULTI",
        "GeoX_analysis_multi_cell",
        GEOX_COMMIT,
        "meridian_geox/data/example_analysis_data_multi_cell_go_dark_heavy_up.csv",
        "https://raw.githubusercontent.com/google/meridian-geox",
        "Apache-2.0",
        "permitted_with_attribution",
        "optional_official_example",
    ),
)


def _download(source: Source, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        source.url, headers={"User-Agent": "geo-causal-bench/0.1"}
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        payload = response.read()
    temporary = destination.with_suffix(destination.suffix + ".part")
    temporary.write_bytes(payload)
    temporary.replace(destination)


def _convert_rdata(raw_path: Path, staged_path: Path, rscript: Path) -> None:
    staged_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [str(rscript), "scripts/convert_rdata.R", str(raw_path), str(staged_path)],
        check=True,
        text=True,
    )


def _schema(path: Path) -> tuple[int | None, list[dict[str, str]]]:
    try:
        with path.open("r", encoding="utf-8") as stream:
            first_line = stream.readline()
        delimiter = ";" if first_line.count(";") > first_line.count(",") else ","
        frame = pd.read_csv(path, sep=delimiter)
    except (pd.errors.ParserError, UnicodeDecodeError):
        return None, []
    return len(frame), [
        {"name": str(name), "dtype": str(dtype)} for name, dtype in frame.dtypes.items()
    ]


def acquire_public_sources(root: Path, *, rscript: Path) -> list[Path]:
    manifests: list[Path] = []
    for source in SOURCES:
        suffix = Path(source.relative_path).suffix
        raw_path = (
            root / "data" / "raw" / source.source_id / f"{source.source_name}{suffix}"
        )
        if not raw_path.exists():
            _download(source, raw_path)
        schema_path = raw_path
        if suffix.lower() in {".rda", ".rdata"}:
            schema_path = (
                root
                / "data"
                / "staged"
                / source.source_id
                / f"{source.source_name}.csv"
            )
            if not schema_path.exists():
                _convert_rdata(raw_path, schema_path, rscript)
        row_count, schema = _schema(schema_path)
        manifest = {
            "source_id": source.source_id,
            "source_name": source.source_name,
            "authoritative_origin": source.url,
            "package_or_commit": source.commit,
            "version": source.commit,
            "retrieval_timestamp_utc": utc_now(),
            "license": source.license_name,
            "sha256": sha256_file(raw_path),
            "bytes": raw_path.stat().st_size,
            "row_count": row_count,
            "schema": schema,
            "schema_hash": canonical_hash(schema),
            "redistribution_status": source.redistribution,
            "scientific_role": source.role,
            "staged_sha256": sha256_file(schema_path)
            if schema_path != raw_path
            else None,
        }
        manifest_path = root / "data" / "manifests" / f"{source.source_id}.json"
        atomic_write_json(manifest_path, manifest)
        manifests.append(manifest_path)

    index_path = root / "data" / "manifests" / "sources.csv"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    with index_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["source_id", "source_name", "commit", "license", "role"])
        writer.writerows(
            (s.source_id, s.source_name, s.commit, s.license_name, s.role)
            for s in SOURCES
        )
    return manifests
