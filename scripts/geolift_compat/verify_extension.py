"""Read-only verification of the committed GeoLift compatibility extension."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "evidence" / "geolift_compatibility"


def load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


manifest = load(EVIDENCE / "evidence_manifest.json")
summary = load(EVIDENCE / "qualification_summary.json")
protected = load(EVIDENCE / "protected_protocol_invariance.json")
lock = load(ROOT / "configs" / "geolift_compatibility.lock.json")

checks: dict[str, bool] = {
    "manifest_pass": manifest["status"] == "PASS",
    "summary_pass": summary["status"] == "PASS",
    "classification": (
        manifest["evidence_class"]
        == summary["evidence_class"]
        == lock["evidence_class"]
        == "UPSTREAM_PINNED"
    ),
    "no_local_patch": summary["local_patch_used"] is False,
    "protected_record_pass": protected["status"] == "PASS",
}

for relative, identity in manifest["files"].items():
    path = ROOT / relative
    checks[f"artifact:{relative}"] = (
        path.is_file()
        and path.stat().st_size == identity["bytes"]
        and sha256_file(path) == identity["sha256"]
    )

for relative, identity in protected["paths"].items():
    current_object = subprocess.check_output(
        ["git", "rev-parse", f"HEAD:{relative}"], cwd=ROOT, text=True
    ).strip()
    worktree_clean = (
        subprocess.run(
            ["git", "diff", "--quiet", "--", relative],
            cwd=ROOT,
            check=False,
        ).returncode
        == 0
    )
    checks[f"protected:{relative}"] = (
        identity["head_matches_audited"] is True
        and identity["working_tree_unmodified"] is True
        and current_object == identity["audited_commit_object"]
        and worktree_clean
    )

payload = {
    "extension_id": manifest["extension_id"],
    "evidence_class": manifest["evidence_class"],
    "status": "PASS" if all(checks.values()) else "FAIL",
    "checks": checks,
}
print(json.dumps(payload, indent=2))
if payload["status"] != "PASS":
    raise SystemExit(1)
