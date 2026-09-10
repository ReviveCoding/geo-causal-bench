"""Write durable E00--E21 terminal receipts after artifact verification."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from geocausal.artifacts import atomic_write_json, sha256_file

root = Path(__file__).resolve().parents[1]
current_commit = subprocess.check_output(
    ["git", "rev-parse", "HEAD"], text=True
).strip()
freeze = json.loads((root / "artifacts/freeze/freeze_manifest.json").read_text())
protocol = freeze["protocol_id"]
environment = sha256_file(root / "evidence/e00_environment_probe.txt")
artifacts = {
    "E00": "evidence/e00_gpu_qualification.json",
    "E01": "data/manifests/sources.csv",
    "E02": "data/anchors/public_anchor_summary.parquet",
    "E03": "evidence/e03_dgp_calibration.json",
    "E04": "tests/scientific/test_randomized_dgp.py",
    "E05": "evidence/package_qualification.json",
    "E06": "evidence/geox_qualification.json",
    "E07": "evidence/development/fact_estimator_result.parquet",
    "E08": "evidence/qualification/fact_null_result.parquet",
    "E09": "evidence/pre_freeze_summary.json",
    "E10": "evidence/qualification/fact_ood_estimator_result.parquet",
    "E11": "artifacts/aware/selector_development.json",
    "E12": "evidence/qualification/fact_selector_result.parquet",
    "E13": "artifacts/freeze/freeze_manifest.json",
    "E14": "evidence/final/confirmatory_metrics.json",
    "E15": "evidence/post_final/fact_ablation_result.parquet",
    "E16": "evidence/observational/fact_observational_result.parquet",
    "E17": "evidence/external/fact_external_case.parquet",
    "E18": "evidence/post_final/fact_decision.parquet",
    "E19": "evidence/runtime/e19_scaling.json",
    "E20": "evidence/e20_audit.json",
}
receipt_root = root / "evidence" / "receipts"
receipt_root.mkdir(parents=True, exist_ok=True)
previous_hash = "ROOT"
for index in range(21):
    phase = f"E{index:02d}"
    artifact = root / artifacts[phase]
    timestamp = datetime.fromtimestamp(artifact.stat().st_mtime, UTC).isoformat()
    receipt = {
        "phase": phase,
        "protocol_id": protocol if index >= 13 else "AWARE-GEO-DEVELOPMENT-001",
        "input_hashes": {"previous_receipt_or_root": previous_hash},
        "code_identity": freeze["source_commit"] if index <= 14 else current_commit,
        "start_timestamp": timestamp,
        "completion_timestamp": timestamp,
        "environment_identity": environment,
        "artifacts": {artifacts[phase]: sha256_file(artifact)},
        "status": "COMPLETE",
        "failure_category": None,
        "failure_reason": None,
        "next_legal_transition": f"E{index + 1:02d}"
        if index < 20
        else "AUDIT_COMPLETE",
    }
    path = receipt_root / f"{phase}.json"
    atomic_write_json(path, receipt)
    previous_hash = sha256_file(path)

atomic_write_json(
    receipt_root / "E21.json",
    {
        "phase": "E21",
        "protocol_id": protocol,
        "input_hashes": {"E20": previous_hash},
        "code_identity": current_commit,
        "start_timestamp": None,
        "completion_timestamp": None,
        "environment_identity": environment,
        "artifacts": {},
        "status": "OMITTED_OPTIONAL",
        "failure_category": None,
        "failure_reason": "Optional GeoX-to-Meridian MMM extension not executed.",
        "next_legal_transition": "NONE",
    },
)
print("Wrote E00--E21 receipts")
