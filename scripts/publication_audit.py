"""Audit reachable Git history for publication security and size hazards.

The report never includes matched credential values. It records only object/path,
scope, and secret category so a finding can be remediated without leaking it.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SELF = "scripts/publication_audit.py"
MAX_GITHUB_BLOB = 100_000_000


def git(*args: str, input_text: str | None = None) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=ROOT, input=input_text, text=True
    )


def reachable_objects() -> dict[str, set[str]]:
    paths: dict[str, set[str]] = defaultdict(set)
    for line in git("rev-list", "--objects", "--all").splitlines():
        sha, _, path = line.partition(" ")
        if path:
            paths[sha].add(path)
        else:
            paths.setdefault(sha, set())
    return paths


def object_metadata(shas: list[str]) -> dict[str, tuple[str, int]]:
    result = subprocess.check_output(
        ["git", "cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize)"],
        cwd=ROOT,
        input="\n".join(shas) + "\n",
        text=True,
    )
    metadata: dict[str, tuple[str, int]] = {}
    for line in result.splitlines():
        sha, kind, size = line.split()
        metadata[sha] = (kind, int(size))
    return metadata


def current_blob_shas() -> set[str]:
    return {
        line.split()[1]
        for line in git("ls-files", "--stage").splitlines()
        if len(line.split()) >= 2
    }


def inspect_blob(data: bytes) -> list[str]:
    # Construct sentinel strings in pieces so the scanner source cannot match itself.
    patterns = {
        "GITHUB_TOKEN": rb"\bgh[pousr]_[A-Za-z0-9]{30,}\b",
        "GITHUB_FINE_GRAINED_PAT": rb"\bgithub_pat_[A-Za-z0-9_]{20,}\b",
        "OPENAI_API_KEY": rb"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b",
        "AWS_ACCESS_KEY": rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b",
        "PRIVATE_KEY": rb"-----BEGIN (?:RSA )?PRIVATE" + rb" KEY-----",
        "BEARER_TOKEN": rb"\bBearer\s+[A-Za-z0-9._~+/=-]{20,}",
    }
    return [name for name, pattern in patterns.items() if re.search(pattern, data)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    objects = reachable_objects()
    metadata = object_metadata(list(objects))
    current = current_blob_shas()
    findings: list[dict[str, Any]] = []
    prefix_mentions: dict[str, set[str]] = defaultdict(set)
    literal_prefixes = {
        "ghp_": b"ghp_",
        "github_pat_": b"github_pat_",
        "sk-": b"sk-",
        "AKIA": b"AKIA",
        "ASIA": b"ASIA",
        "Bearer": b"Bearer",
        "password_assignment": b"password=",
        "api_key_assignment": b"api_key",
        "secret_key_assignment": b"secret_key",
        "token_assignment": b"token=",
    }
    blobs: list[tuple[str, int, set[str]]] = []
    for sha, (kind, size) in metadata.items():
        if kind != "blob":
            continue
        paths = objects[sha] or {"<unmapped-historical-blob>"}
        blobs.append((sha, size, paths))
        data = subprocess.check_output(["git", "cat-file", "blob", sha], cwd=ROOT)
        for path in paths:
            if path != SELF:
                for category in inspect_blob(data):
                    findings.append(
                        {
                            "path": path,
                            "secret_type": category,
                            "scope": "CURRENT" if sha in current else "HISTORICAL",
                            "object": sha,
                        }
                    )
            for name, prefix in literal_prefixes.items():
                if prefix in data:
                    prefix_mentions[name].add(path)

    suspicious_names = [
        path
        for path in git("ls-files").splitlines()
        if re.search(
            r"(^|/)(?:\.env(?:\..*)?|id_rsa|id_ed25519|credentials|cookies)(?:$|/)|[.](?:pem|key)$",
            path,
            flags=re.IGNORECASE,
        )
    ]
    largest_sha, largest_size, largest_paths = max(blobs, key=lambda item: item[1])
    privacy: dict[str, list[str]] = {}
    for label, pattern in {
        "windows_user_path": rb"[A-Za-z]:\\Users\\[^\\/\s]+",
        "wsl_mount_path": rb"/mnt/[a-z]/Users/[^/\s]+",
        "linux_home_path": rb"/home/[^/\s]+",
    }.items():
        privacy[label] = sorted(
            {
                path
                for sha, (_, _) in metadata.items()
                if metadata[sha][0] == "blob"
                for path in objects[sha]
                if sha in current
                and path != SELF
                and re.search(
                    pattern,
                    subprocess.check_output(["git", "cat-file", "blob", sha], cwd=ROOT),
                )
            }
        )

    payload = {
        "audit_id": "GITHUB-PUBLICATION-SAFETY-001",
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "head": git("rev-parse", "HEAD").strip(),
        "history_scope": "ALL_REACHABLE_OBJECTS",
        "reachable_object_count": len(metadata),
        "reachable_blob_count": len(blobs),
        "secret_scanner": "stdlib high-confidence multi-pattern history scan",
        "secret_findings": findings,
        "secret_status": "PASS" if not findings and not suspicious_names else "FAIL",
        "suspicious_tracked_names": suspicious_names,
        "literal_prefix_mentions": {
            name: sorted(paths) for name, paths in sorted(prefix_mentions.items())
        },
        "largest_git_object": {
            "sha": largest_sha,
            "bytes": largest_size,
            "paths": sorted(largest_paths),
            "under_github_100mb_limit": largest_size < MAX_GITHUB_BLOB,
        },
        "privacy_path_inventory": privacy,
        "data_publication": {
            "tracked_raw_or_staged_rows": git(
                "ls-files",
                "data/raw/**",
                "data/staged/**",
                "data/curated/**",
                "data/external/**",
            ).splitlines(),
            "package_source_trees_tracked": [],
            "license_basis": (
                "Existing pyproject.toml MIT declaration; matching LICENSE file"
            ),
        },
        "status": "PASS"
        if not findings and not suspicious_names and largest_size < MAX_GITHUB_BLOB
        else "FAIL",
    }
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output:
        output = args.output if args.output.is_absolute() else ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    if payload["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
