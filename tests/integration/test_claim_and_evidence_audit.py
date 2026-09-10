from pathlib import Path

from geocausal.governance import verify_claims, verify_evidence


def test_claim_ledger_regenerates():
    assert verify_claims(Path.cwd())["all_pass"] is True


def test_frozen_evidence_integrity():
    assert verify_evidence(Path.cwd())["all_pass"] is True
