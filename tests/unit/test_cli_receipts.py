from __future__ import annotations

import json
from pathlib import Path

from geocausal.artifacts import sha256_file
from geocausal.cli import _receipt_summary


def _write_receipt(
    root: Path, phase: str, previous_hash: str, next_transition: str
) -> Path:
    path = root / "evidence" / "receipts" / f"{phase}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "phase": phase,
                "input_hashes": {"previous_receipt_or_root": previous_hash},
                "artifacts": {},
                "status": "COMPLETE",
                "next_legal_transition": next_transition,
            }
        ),
        encoding="utf-8",
    )
    return path


def test_receipt_summary_finds_first_incomplete_phase(tmp_path: Path) -> None:
    e00 = _write_receipt(tmp_path, "E00", "ROOT", "E01")
    result = _receipt_summary(tmp_path)
    assert result["receipt_chain_valid"] is True
    assert result["phases"] == {"E00": "COMPLETE"}
    assert result["next"] == "E01"
    assert sha256_file(e00)


def test_receipt_summary_rejects_broken_chain(tmp_path: Path) -> None:
    _write_receipt(tmp_path, "E00", "WRONG", "E01")
    try:
        _receipt_summary(tmp_path)
    except ValueError as error:
        assert "chain mismatch" in str(error)
    else:
        raise AssertionError("broken receipt chain was accepted")
