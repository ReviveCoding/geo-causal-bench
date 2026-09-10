from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_ci_workflow_is_cpu_safe_and_immutable() -> None:
    path = ROOT / ".github/workflows/ci.yml"
    text = path.read_text(encoding="utf-8")
    assert yaml.safe_load(text) is not None
    assert "pull_request_target" not in text
    assert "permissions:\n  contents: read" in text
    assert "verify_evidence.py --read-only" in text
    assert "verify_post_audit_suite.py" in text
    assert "cuda" not in text.lower()
    references = re.findall(r"uses:\s+[^@\s]+@([0-9a-f]{40})", text)
    assert len(references) == 8


def test_readme_badge_targets_ci_workflow() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    expected = (
        "https://github.com/ReviveCoding/geo-causal-bench/actions/workflows/ci.yml"
    )
    assert expected in readme
