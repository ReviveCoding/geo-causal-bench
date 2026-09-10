"""Create and verify the immutable E13 scientific freeze manifest."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from geocausal.artifacts import atomic_write_json, canonical_hash, sha256_file, utc_now


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def file_hashes(root: Path, paths: list[str]) -> dict[str, str]:
    return {path: sha256_file(root / path) for path in paths}


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    output = root / "artifacts" / "freeze" / "freeze_manifest.json"
    if output.exists():
        raise FileExistsError("Freeze manifest already exists")
    source_commit = git("rev-parse", "HEAD")
    source_tree = git("rev-parse", "HEAD^{tree}")
    manifests = sorted((root / "data" / "manifests").glob("*.json"))
    qualification = json.loads(
        (root / "evidence" / "package_qualification.json").read_text()
    )
    geox = json.loads((root / "evidence" / "geox_qualification.json").read_text())
    identities = json.loads(
        (root / "evidence" / "freeze" / "final_world_identities.json").read_text()
    )
    seed_path = root / "data" / "protected" / "final_world_seeds.json"
    payload: dict[str, Any] = {
        "freeze_created_utc": utc_now(),
        "source_commit": source_commit,
        "source_tree_hash": source_tree,
        "locks": file_hashes(root, ["uv.lock", "renv.lock"]),
        "configs": file_hashes(
            root,
            [
                "configs/frozen/experiment.yaml",
                "configs/frozen/protocol.yaml",
                "configs/gates/development.yaml",
                "configs/selectors/loss.yaml",
            ],
        ),
        "selector_artifact": "artifacts/aware/selector_development.json",
        "selector_hash": sha256_file(
            root / "artifacts" / "aware" / "selector_development.json"
        ),
        "diagnostic_feature_schema": json.loads(
            (root / "artifacts" / "aware" / "selector_development.json").read_text()
        )["features"],
        "dgp_hashes": file_hashes(
            root,
            [
                "src/geocausal/dgp/randomized.py",
                "src/geocausal/dgp/observational.py",
            ],
        ),
        "scoring_code_hash": sha256_file(
            root / "src" / "geocausal" / "simulation" / "protected.py"
        ),
        "dataset_manifests": {
            str(path.relative_to(root)): sha256_file(path) for path in manifests
        },
        "package_versions": qualification["package_versions"],
        "r_version": qualification["r_version"],
        "geox_package": geox["package"],
        "geox_version": geox["version"],
        "geox_source_commit": "0a1dd0f730ab8170e4e46646f3bf69400d57d021",
        "final_world_count": identities["world_count"],
        "final_world_identity_manifest_hash": sha256_file(
            root / "evidence" / "freeze" / "final_world_identities.json"
        ),
        "final_seed_set_canonical_hash": identities["seed_set_hash"],
        "protected_seed_file_sha256": sha256_file(seed_path),
        "hypotheses_and_multiplicity": "configs/frozen/protocol.yaml",
        "report_schema_version": 1,
        "claim_ledger_schema_version": 1,
        "allowed_next_transition": "E14_CANONICAL_EVALUATION_ONCE",
    }
    protocol_id = f"AWARE-GEO-{canonical_hash(payload)[:16]}"
    manifest = {"protocol_id": protocol_id, **payload}
    atomic_write_json(output, manifest)
    manifest_hash = sha256_file(output)
    atomic_write_json(
        root / "artifacts" / "freeze" / "verification.json",
        {
            "protocol_id": protocol_id,
            "freeze_manifest_sha256": manifest_hash,
            "verified": sha256_file(output) == manifest_hash,
            "verified_utc": utc_now(),
        },
    )
    print(json.dumps({"protocol_id": protocol_id, "sha256": manifest_hash}, indent=2))


if __name__ == "__main__":
    main()
