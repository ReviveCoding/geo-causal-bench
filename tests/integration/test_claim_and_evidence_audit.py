import shutil
from pathlib import Path

from geocausal.governance import verify_claims, verify_evidence


def test_claim_ledger_regenerates():
    assert verify_claims(Path.cwd())["all_pass"] is True


def test_claim_ledger_is_independent_of_persisted_duckdb_paths(tmp_path: Path) -> None:
    root = Path.cwd()
    copies = [
        "evidence/claim_ledger.json",
        "evidence/final/confirmatory_metrics.json",
        "evidence/final/fact_selector_result.parquet",
        "evidence/runtime/e19_scaling.json",
    ]
    for relative in copies:
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / relative, destination)
    assert not (tmp_path / "artifacts/results.duckdb").exists()
    assert verify_claims(tmp_path)["all_pass"] is True


def test_frozen_evidence_integrity():
    assert verify_evidence(Path.cwd())["all_pass"] is True
