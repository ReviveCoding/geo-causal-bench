from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load(path: str) -> dict[str, object]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_pinned_compatibility_evidence_passes() -> None:
    summary = _load("evidence/geolift_compatibility/qualification_summary.json")
    assert summary["evidence_class"] == "UPSTREAM_PINNED"
    assert summary["status"] == "PASS"
    assert summary["local_patch_used"] is False
    assert all(summary["checks"].values())


def test_protocol_002_evidence_remains_unchanged() -> None:
    protected = _load(
        "evidence/geolift_compatibility/protected_protocol_invariance.json"
    )
    assert protected["status"] == "PASS"
    assert all(
        entry["head_matches_audited"] and entry["working_tree_unmodified"]
        for entry in protected["paths"].values()
    )
