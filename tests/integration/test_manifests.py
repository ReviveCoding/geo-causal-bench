from __future__ import annotations

import json
from pathlib import Path


def test_public_source_manifests_have_required_identity_fields():
    required = {
        "source_id",
        "source_name",
        "authoritative_origin",
        "version",
        "retrieval_timestamp_utc",
        "license",
        "sha256",
        "bytes",
        "row_count",
        "schema",
        "schema_hash",
        "redistribution_status",
        "scientific_role",
    }
    paths = sorted(Path("data/manifests").glob("*.json"))
    assert len(paths) >= 8
    for path in paths:
        manifest = json.loads(path.read_text(encoding="utf-8"))
        assert required <= set(manifest), path
        assert len(manifest["sha256"]) == 64
