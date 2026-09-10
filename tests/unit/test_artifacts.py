from __future__ import annotations

import json

from geocausal.artifacts import atomic_write_json, canonical_hash, sha256_file


def test_atomic_json_and_hash_are_deterministic(tmp_path):
    path = tmp_path / "nested" / "artifact.json"
    atomic_write_json(path, {"b": 2, "a": 1})
    assert json.loads(path.read_text()) == {"a": 1, "b": 2}
    assert len(sha256_file(path)) == 64
    assert canonical_hash({"a": 1, "b": 2}) == canonical_hash({"b": 2, "a": 1})
