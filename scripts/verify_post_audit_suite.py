"""Read-only verifier for POST-AUDIT-SUITE-001."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "4e161634557ea76852f3ca70340898bb5acf8394"
GEOLIFT_BASELINE = "fce32650b34d198d2247787cc86ae529f1e94532"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_object(revision: str, path: str) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", f"{revision}:{path}"], cwd=ROOT, text=True
    ).strip()


def main() -> None:
    checks: dict[str, bool] = {}
    roots = {
        "POST-AUDIT-ANALYTICS-001": ROOT / "evidence/post_audit_analytics",
        "OPERATIONS-STUDY-001": ROOT / "evidence/operations",
        "COMPLIANCE-SEMANTICS-001": ROOT / "evidence/compliance_semantics",
    }
    for identity, directory in roots.items():
        manifest = json.loads((directory / "manifest.json").read_text())
        checks[f"manifest_identity:{identity}"] = manifest["extension_id"] == identity
        for relative, expected in manifest["files"].items():
            checks[f"hash:{relative}"] = sha256(ROOT / relative) == expected
    required_tables = [
        "evidence/post_audit_analytics/fact_slice_result.parquet",
        "evidence/post_audit_analytics/slice_summary.parquet",
        "evidence/post_audit_analytics/fact_tail_risk.parquet",
        "evidence/post_audit_analytics/fact_risk_calibration.parquet",
        "evidence/post_audit_analytics/fact_threshold_frontier.parquet",
        "evidence/operations/fact_influence.parquet",
        "evidence/operations/fact_rolling_backtest.parquet",
        "evidence/operations/fact_seasonal_study.parquet",
        "evidence/operations/fact_design_frontier.parquet",
        "evidence/operations/fact_empirical_power.parquet",
        "evidence/operations/fact_tool_design_comparison.parquet",
        "evidence/operations/fact_data_quality_stress.parquet",
        "evidence/post_audit_analytics/fact_failure_attribution.parquet",
        "evidence/compliance_semantics/fact_compliance_result.parquet",
    ]
    for relative in required_tables:
        frame = pd.read_parquet(ROOT / relative)
        checks[f"table_nonempty:{relative}"] = not frame.empty
    for number in range(21, 42):
        checks[f"figure:F{number:02d}"] = (
            ROOT / f"reports/figures/F{number:02d}.png"
        ).is_file()
    protected = [
        "artifacts/freeze",
        "evidence/final",
        "evidence/e20_audit.json",
        "evidence/receipts",
        "evidence/invalidated",
    ]
    for path in protected:
        checks[f"protected_object:{path}"] = git_object(BASELINE, path) == git_object(
            "HEAD", path
        )
        checks[f"protected_worktree:{path}"] = (
            subprocess.run(
                ["git", "diff", "--quiet", "--", path], cwd=ROOT, check=False
            ).returncode
            == 0
        )
    compatibility = "evidence/geolift_compatibility"
    checks["geolift_object"] = git_object(
        GEOLIFT_BASELINE, compatibility
    ) == git_object("HEAD", compatibility)
    checks["geolift_worktree"] = (
        subprocess.run(
            ["git", "diff", "--quiet", "--", compatibility],
            cwd=ROOT,
            check=False,
        ).returncode
        == 0
    )
    geolift = json.loads(
        (ROOT / "evidence/operations/geolift_official_operations.json").read_text()
    )
    checks["geolift_pin"] = (
        geolift["geolift_commit"] == "db34ea4299ff0e28515ebac502b78c076c93c905"
        and geolift["augsynth_commit"] == "65c5a6f34f4e4a8b1011182fe12309ef022d992f"
        and geolift["local_patch"] is False
    )
    compliance = pd.read_parquet(
        ROOT / "evidence/compliance_semantics/fact_compliance_result.parquet"
    )
    zero = compliance[compliance.nominal_compliance == 0]
    checks["zero_compliance_itt_truth"] = (
        zero[zero.estimand == "assignment_itt"].true_value.abs().max() == 0
    )
    checks["zero_compliance_dose_unidentified"] = (
        zero[zero.estimand == "dose_response"].status
        == "NOT_IDENTIFIED_ZERO_COMPLIANCE"
    ).all()
    checks["truth_not_in_observed_contract"] = not {
        "assignment_itt",
        "dose_response",
        "cace",
    } & {
        "world_id",
        "assignment",
        "delivered_dose",
        "pre_outcome",
        "post_outcome",
    }
    dashboard = (ROOT / "dashboards/post_audit_results.html").read_text()
    for label in (
        "Data quality",
        "Experiment design",
        "Reliability",
        "Compliance semantics",
        "Historical protocol",
    ):
        checks[f"dashboard:{label}"] = label in dashboard
    checks = {key: bool(value) for key, value in checks.items()}
    result: dict[str, Any] = {
        "suite_id": "POST-AUDIT-SUITE-001",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
