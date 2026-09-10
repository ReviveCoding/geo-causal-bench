from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


def test_post_audit_tables_and_identities() -> None:
    required = {
        "evidence/post_audit_analytics/fact_slice_result.parquet",
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
    }
    for relative in required:
        path = ROOT / relative
        assert path.exists(), relative
        assert not pd.read_parquet(path).empty, relative


def test_suite_audit_and_claim_boundaries() -> None:
    audit = json.loads((ROOT / "evidence/post_audit_suite_audit.json").read_text())
    assert audit["status"] == "PASS"
    assert all(item["unchanged"] for item in audit["protected_objects"].values())
    claims = json.loads((ROOT / "evidence/post_audit_claim_ledger.json").read_text())
    assert all(claim["evidence_class"].startswith("POST_AUDIT") for claim in claims)


def test_compliance_zero_and_full_regimes() -> None:
    frame = pd.read_parquet(
        ROOT / "evidence/compliance_semantics/fact_compliance_result.parquet"
    )
    assignment = frame[frame.estimand == "assignment_itt"]
    assert assignment[assignment.nominal_compliance == 0].true_value.abs().max() == 0
    assert assignment[assignment.nominal_compliance == 1].realized_compliance.min() == 1


def test_geox_quality_checks_are_separate_from_design_availability() -> None:
    frame = pd.read_parquet(
        ROOT / "evidence/operations/geox_official_quality_stress.parquet"
    )
    assert len(frame) == 18
    assert set(frame.geox_validation_result) == {"PASS"}
    assert frame.design_available.sum() == 10
    unavailable = frame[~frame.design_available]
    available = frame[frame.design_available]
    assert unavailable.design_failure_reason.notna().all()
    assert available[["r2", "mde", "budget"]].notna().all(axis=None)


def test_all_post_audit_figures_exist() -> None:
    for number in range(21, 42):
        assert (ROOT / f"reports/figures/F{number:02d}.png").exists()
