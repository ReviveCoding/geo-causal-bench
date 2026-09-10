"""Machine-verifiable evidence and claim audits."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import duckdb

from geocausal.artifacts import sha256_file


def _json_value(root: Path, source: str, dotted: str) -> Any:
    value: Any = json.loads((root / source).read_text(encoding="utf-8"))
    for key in dotted.split("."):
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def verify_claims(root: Path) -> dict[str, Any]:
    ledger = json.loads((root / "evidence" / "claim_ledger.json").read_text())
    # Persisted DuckDB views record the filesystem path used when reports were
    # built. Recreate the claim view from immutable local Parquet so verification
    # remains read-only and works in a fresh clone at any path.
    database = duckdb.connect(":memory:")
    database.from_parquet(
        str(root / "evidence" / "final" / "fact_selector_result.parquet")
    ).create_view("final_selectors")
    results = []
    for claim in ledger["claims"]:
        if "query" in claim:
            row = database.execute(claim["query"]).fetchone()
            if row is None:
                raise ValueError(f"Claim query returned no row: {claim['claim_id']}")
            actual = row[0]
        else:
            actual = _json_value(root, claim["source"], claim["json_path"])
        passed = abs(float(actual) - float(claim["expected"])) <= float(
            claim["tolerance"]
        )
        results.append(
            {"claim_id": claim["claim_id"], "actual": actual, "passed": passed}
        )
    database.close()
    return {"claims": results, "all_pass": all(item["passed"] for item in results)}


def verify_evidence(root: Path) -> dict[str, Any]:
    freeze_path = root / "artifacts" / "freeze" / "freeze_manifest.json"
    freeze = json.loads(freeze_path.read_text())
    verification = json.loads(
        (root / "artifacts" / "freeze" / "verification.json").read_text()
    )
    final = json.loads(
        (root / "evidence" / "final" / "confirmatory_metrics.json").read_text()
    )
    identities = json.loads(
        (root / "evidence" / "freeze" / "final_world_identities.json").read_text()
    )
    ledger = json.loads(
        (root / "evidence" / "final" / "truth_access_ledger.json").read_text()
    )
    expected_identity = {
        item["world_id"]: item["identity_hash"]
        for item in identities["world_identities"]
    }
    checks = {
        "freeze_hash": sha256_file(freeze_path)
        == verification["freeze_manifest_sha256"],
        "protocol_match": final["protocol_id"] == freeze["protocol_id"],
        "truth_ledger_count": len(ledger) == freeze["final_world_count"] == 500,
        "truth_ledger_unique": len({item["world_id"] for item in ledger})
        == len(ledger),
        "truth_identity_match": all(
            item["world_identity_hash"] == expected_identity[item["world_id"]]
            for item in ledger
        ),
        "selector_hash": sha256_file(root / freeze["selector_artifact"])
        == freeze["selector_hash"],
        "scoring_code_hash": sha256_file(root / "src/geocausal/simulation/protected.py")
        == freeze["scoring_code_hash"],
        "locks": all(
            sha256_file(root / path) == digest
            for path, digest in freeze["locks"].items()
        ),
        "dataset_manifests": all(
            sha256_file(root / path) == digest
            for path, digest in freeze["dataset_manifests"].items()
        ),
        # Protocol 002 owns F01--F20. Separately labeled post-audit figures may
        # coexist without invalidating the historical figure gate.
        "figures": all(
            (root / "reports" / "figures" / f"F{number:02d}.png").is_file()
            for number in range(1, 21)
        ),
        "invalid_protocol_preserved": (
            root / "evidence/invalidated/AWARE-GEO-c0b13ec88b725728/invalidation.json"
        ).exists(),
    }
    return {
        "protocol_id": freeze["protocol_id"],
        "checks": checks,
        "all_pass": all(checks.values()),
    }
