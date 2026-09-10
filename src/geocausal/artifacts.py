"""Atomic, hash-addressed evidence and phase receipts."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

from geocausal.types import FailureCategory, PhaseStatus


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def atomic_write_json(path: Path, value: Any) -> None:
    atomic_write_text(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


class PhaseReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phase: str
    protocol_id: str
    input_hashes: dict[str, str]
    code_identity: str
    start_timestamp: str
    completion_timestamp: str
    environment_identity: str
    artifacts: dict[str, str]
    status: PhaseStatus
    failure_category: FailureCategory | None = None
    failure_reason: str | None = None
    next_legal_transition: str

    def write(self, root: Path) -> Path:
        path = root / "evidence" / "receipts" / f"{self.phase}.json"
        atomic_write_json(path, self.model_dump(mode="json"))
        return path
