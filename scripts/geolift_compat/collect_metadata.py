"""Collect authoritative issue, source-history, and protected-scope evidence."""

from __future__ import annotations

import hashlib
import json
import subprocess
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
OUTPUT = PROJECT / "evidence" / "geolift_compatibility" / "source"
AUGSYNTH = Path("/home/bjw-0/.cache/geo-causal-bench/geolift-compat/upstream/augsynth")
GEOLIFT = Path("/home/bjw-0/.cache/geo-causal-bench/geolift-compat/upstream/GeoLift")
CURRENT = "7e70072232fe75057aa8b5d7af08c7e1aef53ae8"
PINNED = "65c5a6f34f4e4a8b1011182fe12309ef022d992f"
FIRST_BAD = "bdc0b808103ffa7cf63ba0661f1ee2adb10eba3c"
GEOLIFT_COMMIT = "db34ea4299ff0e28515ebac502b78c076c93c905"
AUDITED_COMMIT = "4e161634557ea76852f3ca70340898bb5acf8394"


def run(*args: str, cwd: Path | None = None) -> str:
    return subprocess.check_output(args, cwd=cwd, text=True).strip()


def git(repo: Path, *args: str) -> str:
    return run("git", "-C", str(repo), *args)


def git_blob(repo: Path, commit: str, path: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(repo), "show", f"{commit}:{path}"])


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def excerpt(text: str, start: str, end: str) -> str:
    left = text.index(start)
    right = text.index(end, left) + len(end)
    return text[left:right]


def atomic_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


OUTPUT.mkdir(parents=True, exist_ok=True)
request = urllib.request.Request(
    "https://api.github.com/repos/ebenmichael/augsynth/issues/118",
    headers={"Accept": "application/vnd.github+json", "User-Agent": "geo-causal-bench"},
)
with urllib.request.urlopen(request, timeout=30) as response:
    issue = json.load(response)
atomic_json(OUTPUT / "issue_118.json", issue)

current_permutation = git_blob(AUGSYNTH, CURRENT, "R/permutation.R")
current_augsynth = git_blob(AUGSYNTH, CURRENT, "R/augsynth.R")
pinned_augsynth = git_blob(AUGSYNTH, PINNED, "R/augsynth.R")
geolift_analysis = git_blob(GEOLIFT, GEOLIFT_COMMIT, "R/post_test_analysis.R")

permutation_text = current_permutation.decode()
augsynth_text = current_augsynth.decode()
geolift_text = geolift_analysis.decode()
source_payload = {
    "evidence_class": "UPSTREAM_PINNED",
    "retrieval_timestamp_utc": datetime.now(UTC).isoformat(),
    "issue": {
        "number": issue["number"],
        "state": issue["state"],
        "comments": issue["comments"],
        "url": issue["html_url"],
        "updated_at": issue["updated_at"],
        "body_sha256": sha256(issue["body"].encode()),
    },
    "history": {
        "tested_bad_head": CURRENT,
        "last_good_pin": PINNED,
        "first_bad_commit": FIRST_BAD,
        "first_bad_parent": git(AUGSYNTH, "rev-parse", f"{FIRST_BAD}^"),
        "first_bad_metadata": git(
            AUGSYNTH, "show", "-s", "--format=%H%n%T%n%aI%n%s", FIRST_BAD
        ).splitlines(),
    },
    "source_hashes": {
        f"augsynth:{CURRENT}:R/permutation.R": sha256(current_permutation),
        f"augsynth:{CURRENT}:R/augsynth.R": sha256(current_augsynth),
        f"augsynth:{PINNED}:R/augsynth.R": sha256(pinned_augsynth),
        f"GeoLift:{GEOLIFT_COMMIT}:R/post_test_analysis.R": sha256(geolift_analysis),
    },
    "call_chain": [
        "GeoLift::GeoLift",
        "base::summary",
        "augsynth:::summary.augsynth",
        "augsynth::treated_table",
        "tibble::tibble",
    ],
    "statistical_semantics": {
        "augsynth_prediction": (
            "colMeans of observed treated outcomes minus one treated-average "
            "synthetic counterfactual per time"
        ),
        "geolift_average_att": "average effect per treated location and time",
        "geolift_incremental": (
            "sum of observed treated outcomes minus treated count times the average "
            "synthetic counterfactual"
        ),
        "fault": (
            "treated_table flattens treated_count by time observations instead of "
            "using the treated-location mean required by predict.augsynth"
        ),
    },
    "source_excerpts": {
        "treated_table": excerpt(
            permutation_text,
            "treated_table <- function(augsynth)",
            "return( lvls )\n}",
        ),
        "predict_augsynth": excerpt(
            augsynth_text,
            "predict.augsynth <- function(object, att = F, ...)",
            "}\n\n\n\n\n#' Add inference",
        ),
        "geolift_summary_and_aggregation": excerpt(
            geolift_text,
            "sum_augsyn <- summary(augsyn",
            '"stat_test" = stat_test\n  )',
        ),
    },
}
atomic_json(OUTPUT / "source_analysis.json", source_payload)

protected_paths = [
    "artifacts/freeze",
    "evidence/final",
    "evidence/e20_audit.json",
    "evidence/receipts",
]
protected = {}
for relative in protected_paths:
    baseline_tree = run("git", "rev-parse", f"{AUDITED_COMMIT}:{relative}", cwd=PROJECT)
    current_tree = run("git", "rev-parse", f"HEAD:{relative}", cwd=PROJECT)
    working_tree_clean = (
        subprocess.run(
            ["git", "diff", "--quiet", "--", relative], cwd=PROJECT, check=False
        ).returncode
        == 0
    )
    protected[relative] = {
        "audited_commit_object": baseline_tree,
        "current_head_object": current_tree,
        "head_matches_audited": current_tree == baseline_tree,
        "working_tree_unmodified": working_tree_clean,
    }
atomic_json(
    OUTPUT.parent / "protected_protocol_invariance.json",
    {
        "audited_commit": AUDITED_COMMIT,
        "status": "PASS"
        if all(
            item["head_matches_audited"] and item["working_tree_unmodified"]
            for item in protected.values()
        )
        else "FAIL",
        "paths": protected,
    },
)
print("Collected authoritative source and protected-scope metadata")
