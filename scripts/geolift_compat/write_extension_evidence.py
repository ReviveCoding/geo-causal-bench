"""Validate compatibility outputs and write the extension summary and manifest."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "evidence" / "geolift_compatibility"


def load(relative: str) -> dict[str, object]:
    return json.loads((EVIDENCE / relative).read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


session_1 = load("qualification/session_1.json")
session_2 = load("qualification/session_2.json")
fresh = load("qualification/fresh_session_comparison.json")
source = load("source/source_analysis.json")
protected = load("protected_protocol_invariance.json")
lock = json.loads(
    (ROOT / "configs" / "geolift_compatibility.lock.json").read_text(encoding="utf-8")
)
traceback_text = (EVIDENCE / "baseline" / "complete_traceback.log").read_text(
    encoding="utf-8"
)
bisect_text = (EVIDENCE / "bisect" / "git_bisect_attempt2.log").read_text(
    encoding="utf-8"
)

checks = {
    "baseline_class_unmodified": "UPSTREAM_UNMODIFIED" in traceback_text,
    "baseline_exact_dimension_error": (
        "Size 105: Existing data." in traceback_text
        and "Size 210: Column `Yobs`." in traceback_text
    ),
    "baseline_active_stack": "=== ACTIVE CALL STACK ===" in traceback_text,
    "bisect_first_bad": source["history"]["first_bad_commit"] in bisect_text,
    "pin_is_first_bad_parent": (
        source["history"]["first_bad_parent"] == lock["augsynth"]["commit"]
    ),
    "session_1_pass": session_1["status"] == "PASS",
    "session_2_pass": session_2["status"] == "PASS",
    "fresh_session_pass": fresh["fresh_session_reproducible"] is True,
    "all_invariants_pass": all(
        value == "PASS" for value in session_1["invariants"].values()
    ),
    "official_two_location_effect": (
        abs(session_1["cases"]["two"]["incremental"] - 4667) <= 10
    ),
    "three_plus_locations": session_1["cases"]["three"]["treated_count"] >= 3,
    "protected_protocol_unchanged": protected["status"] == "PASS",
}
status = "PASS" if all(checks.values()) else "FAIL"
summary = {
    "extension_id": "GEOLIFT-COMPAT-001",
    "evidence_class": "UPSTREAM_PINNED",
    "status": status,
    "resolution": (
        "Pin unmodified augsynth commit "
        "65c5a6f34f4e4a8b1011182fe12309ef022d992f with unmodified GeoLift "
        "2.7.5 commit db34ea4299ff0e28515ebac502b78c076c93c905."
    ),
    "local_patch_used": False,
    "first_incompatible_commit": source["history"]["first_bad_commit"],
    "checks": checks,
    "case_results": session_1["cases"],
    "limitations": [
        (
            "Both tested augsynth revisions report package version 0.2.0; "
            "commit pinning is mandatory."
        ),
        (
            "Top-level GeoLift aggregate confidence bounds are NA in this "
            "dependency constellation, although summary$att contains the expected "
            "105-row conformal estimate/bound/p-value series."
        ),
        (
            "This compatibility result does not modify or reinterpret AWARE-GEO "
            "protocol 002."
        ),
    ],
}
summary_path = EVIDENCE / "qualification_summary.json"
summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

excluded = {"evidence_manifest.json", "extension_receipt.json"}
files = sorted(
    path for path in EVIDENCE.rglob("*") if path.is_file() and path.name not in excluded
)
manifest = {
    "extension_id": "GEOLIFT-COMPAT-001",
    "evidence_class": "UPSTREAM_PINNED",
    "status": status,
    "files": {
        path.relative_to(ROOT).as_posix(): {
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        }
        for path in files
    },
}
(EVIDENCE / "evidence_manifest.json").write_text(
    json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
)
if status != "PASS":
    raise SystemExit(f"compatibility evidence failed: {checks}")
print(f"GeoLift compatibility evidence PASS ({len(files)} files)")
