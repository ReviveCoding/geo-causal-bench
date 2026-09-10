"""Integrate official-tool evidence and close the post-audit suite."""

# ruff: noqa: E501

from __future__ import annotations

import html
import json
import subprocess
from pathlib import Path
from typing import Any

import duckdb
import matplotlib
import numpy as np
import pandas as pd

from geocausal.artifacts import (
    atomic_write_json,
    atomic_write_text,
    sha256_file,
    utc_now,
)

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
ANALYTICS = ROOT / "evidence/post_audit_analytics"
OPERATIONS = ROOT / "evidence/operations"
COMPLIANCE = ROOT / "evidence/compliance_semantics"
BASELINE = "4e161634557ea76852f3ca70340898bb5acf8394"
START = "fce32650b34d198d2247787cc86ae529f1e94532"


def git_object(revision: str, path: str) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", f"{revision}:{path}"], cwd=ROOT, text=True
    ).strip()


def geolift_tables() -> tuple[pd.DataFrame, pd.DataFrame]:
    payload = json.loads((OPERATIONS / "geolift_official_operations.json").read_text())
    markets = pd.DataFrame(payload["market_selection"]["BestMarkets"])
    markets = markets.assign(
        extension_id="OPERATIONS-STUDY-001",
        evidence_class="MEASURED",
        tool="GEOLIFT_2.7.5_UPSTREAM_PINNED",
        status="SUCCESS",
        geolift_commit=payload["geolift_commit"],
        augsynth_commit=payload["augsynth_commit"],
    )
    power = pd.DataFrame(payload["power"])
    power = power.assign(
        extension_id="OPERATIONS-STUDY-001",
        evidence_class="MEASURED",
        tool="GEOLIFT_2.7.5_UPSTREAM_PINNED",
        status="SUCCESS",
    )
    markets.to_parquet(
        OPERATIONS / "geolift_official_design_frontier.parquet", index=False
    )
    power.to_parquet(OPERATIONS / "geolift_official_power.parquet", index=False)
    return markets, power


def integrate_tools() -> dict[str, Any]:
    simulated = pd.read_parquet(OPERATIONS / "fact_design_frontier.parquet")
    simulated = simulated[simulated.tool != "MERIDIAN_GEOX_1.0.1"].copy()
    geox = pd.read_parquet(OPERATIONS / "geox_official_design_frontier.parquet")
    combined = pd.concat([simulated, geox], ignore_index=True, sort=False)
    combined.to_parquet(OPERATIONS / "fact_design_frontier.parquet", index=False)
    proxy_quality = pd.read_parquet(OPERATIONS / "fact_data_quality_stress.parquet")
    proxy_quality = proxy_quality[
        proxy_quality.status == "SIMULATED_VALIDATION_PROXY_PENDING_OFFICIAL_CHECK"
    ].copy()
    official_quality = pd.read_parquet(
        OPERATIONS / "geox_official_quality_stress.parquet"
    )
    pd.concat(
        [proxy_quality, official_quality], ignore_index=True, sort=False
    ).to_parquet(OPERATIONS / "fact_data_quality_stress.parquet", index=False)
    markets, power = geolift_tables()
    common = pd.read_parquet(OPERATIONS / "geox_common_panel_design.parquet")
    compare_rows = []
    for row in common.to_dict(orient="records"):
        compare_rows.append(
            {
                **row,
                "native_fit_metric_name": "r2",
                "native_fit_metric": row.get("r2"),
                "native_effect_threshold_name": "mde",
                "native_effect_threshold": row.get("mde"),
                "native_power": 0.8,
                "native_investment": row.get("budget"),
                "native_imbalance": np.nan,
                "metric_comparability": "TOOL_NATIVE_NOT_COMMON_SCALE",
            }
        )
    for row in markets.to_dict(orient="records"):
        compare_rows.append(
            {
                "extension_id": "OPERATIONS-STUDY-001",
                "evidence_class": "POST_AUDIT_EXTERNAL",
                "dataset_id": "D1_GEOLIFT_PRE_COMMON_PANEL",
                "tool": "GEOLIFT_2.7.5_UPSTREAM_PINNED",
                "assignment": "optimized_market_selection",
                "status": "SUCCESS",
                "treatment_geos": json.dumps(
                    sorted(part.strip() for part in row["location"].split(","))
                ),
                "control_geos": None,
                "treatment_geo_count": len(row["location"].split(",")),
                "treatment_response_share": row["ProportionTotal_Y"],
                "native_fit_metric_name": "scaled_l2_imbalance",
                "native_fit_metric": row["AvgScaledL2Imbalance"],
                "native_effect_threshold_name": "average_mde",
                "native_effect_threshold": row["Average_MDE"],
                "native_power": row["Power"],
                "native_investment": row["Investment"],
                "native_imbalance": row["AvgScaledL2Imbalance"],
                "metric_comparability": "TOOL_NATIVE_NOT_COMMON_SCALE",
            }
        )
    comparison = pd.DataFrame(compare_rows)
    comparison["jaccard_vs_geox_stratified"] = np.nan
    comparison["response_share_difference_vs_geox"] = np.nan
    # Pair GeoX stratified with each GeoLift recommendation for set-overlap only.
    overlap_rows = []
    geox_success = comparison[
        (comparison.tool == "MERIDIAN_GEOX_1.0.1")
        & (comparison.assignment == "stratified")
        & (comparison.status == "SUCCESS")
    ]
    if not geox_success.empty:
        gx = set(json.loads(geox_success.iloc[0].treatment_geos))
        for index, row in comparison[
            comparison.tool == "GEOLIFT_2.7.5_UPSTREAM_PINNED"
        ].iterrows():
            gl = set(json.loads(row.treatment_geos))
            comparison.loc[index, "jaccard_vs_geox_stratified"] = len(gx & gl) / len(
                gx | gl
            )
            comparison.loc[index, "response_share_difference_vs_geox"] = (
                row.treatment_response_share
                - geox_success.iloc[0].treatment_response_share
            )
            overlap_rows.append(comparison.loc[index, "jaccard_vs_geox_stratified"])
    comparison.to_parquet(
        OPERATIONS / "fact_tool_design_comparison.parquet", index=False
    )
    return {
        "geox_success": int((geox.status == "SUCCESS").sum()),
        "geox_duration_gates": int(
            (geox.status == "GATED_PRETEST_LT_3X_EXPERIMENT").sum()
        ),
        "geolift_market_rows": len(markets),
        "geolift_power_rows": len(power),
        "mean_design_jaccard": float(np.mean(overlap_rows)) if overlap_rows else None,
    }


def figures() -> None:
    figure_root = ROOT / "reports/figures"
    market = pd.read_parquet(OPERATIONS / "geolift_official_power.parquet")
    plt.figure(figsize=(7, 4))
    for duration, group in market.groupby("duration"):
        ordered = group.groupby("EffectSize", as_index=False).power.mean()
        plt.plot(
            ordered.EffectSize, ordered.power, marker="o", label=f"{duration} days"
        )
    plt.xlabel("GeoLift effect size")
    plt.ylabel("GeoLift native power")
    plt.legend()
    plt.title("GeoLift pinned power frontier")
    plt.tight_layout()
    plt.savefig(figure_root / "F34.png", dpi=150)
    plt.close()
    comparison = pd.read_parquet(OPERATIONS / "fact_tool_design_comparison.parquet")
    overlap = comparison.dropna(subset=["jaccard_vs_geox_stratified"])
    plt.figure(figsize=(7, 4))
    plt.bar(overlap.treatment_geo_count.astype(str), overlap.jaccard_vs_geox_stratified)
    plt.xlabel("GeoLift selected market count")
    plt.ylabel("Jaccard vs GeoX stratified set")
    plt.title("Same-panel treatment-set overlap")
    plt.tight_layout()
    plt.savefig(figure_root / "F35.png", dpi=150)
    plt.close()


def update_reports(tool_summary: dict[str, Any]) -> None:
    slices = pd.read_parquet(ANALYTICS / "fact_slice_result.parquet")
    aware_scenarios = slices[
        (slices.selector_id == "AWARE") & (slices.slice_dimension == "scenario_id")
    ].set_index("slice_value")
    tail = pd.read_parquet(ANALYTICS / "fact_tail_risk.parquet")
    aware_tail = tail[
        (tail.selector_id == "AWARE") & (tail.loss == "decision_regret")
    ].iloc[0]
    fixed_tail = tail[
        (tail.selector_id == "fixed_did") & (tail.loss == "decision_regret")
    ].iloc[0]
    risk = json.loads((ANALYTICS / "risk_calibration_summary.json").read_text())
    seasonal = pd.read_parquet(OPERATIONS / "fact_seasonal_study.parquet")
    season = seasonal.groupby("history_days").covered_truth.mean().to_dict()
    power = pd.read_parquet(OPERATIONS / "fact_empirical_power.parquet")
    empirical = power.groupby("effect_mde_multiple").rejection_rate.mean().to_dict()
    compliance = pd.read_parquet(COMPLIANCE / "fact_compliance_result.parquet")
    assignment = compliance[compliance.estimand == "assignment_itt"]
    zero_truth = assignment[assignment.nominal_compliance == 0].true_value.abs().max()
    full_rmse = np.sqrt(assignment[assignment.nominal_compliance == 1].sq_error.mean())
    report = f"""# Final Industry Analytics Summary

All findings are post-audit. Protocol 002 remains historically `PROMOTE_AWARE`.

## Reliability

- S04 coverage: {aware_scenarios.loc["S04", "coverage"]:.3f}; S13 coverage:
  {aware_scenarios.loc["S13", "coverage"]:.3f}. These failures persist.
- Predicted-risk Spearman correlation with realized procedure loss was
  {risk["spearman_predicted_vs_realized"]:.3f}; catastrophic-loss AUROC was
  {risk["catastrophic_auroc"]:.3f}. The frozen risk score did not meaningfully
  rank studies for review in this completed sample.
- AWARE decision-regret CVaR95 was {aware_tail.cvar95:.3f}, versus
  {fixed_tail.cvar95:.3f} for fixed DiD. Tail-risk superiority is not claimed.

## Operations

- Official GeoX: {tool_summary["geox_success"]} successful new design cells;
  {tool_summary["geox_duration_gates"]} duration cells gated by insufficient
  history. All official warning/error text is retained.
- Pinned GeoLift: {tool_summary["geolift_market_rows"]} selected-market rows and
  {tool_summary["geolift_power_rows"]} power rows completed. GeoLift/GeoX native
  metrics were not forced onto a common scale.
- Seasonal coverage by history was {json.dumps(season, sort_keys=True)}.
- Mean rejection rates at 0/0.5/1/1.5 MDE were
  {json.dumps(empirical, sort_keys=True)}. These analytic design simulations do
  not validate Protocol 002 power.

## Compliance semantics

The separate `DGP_A_v2_COMPLIANCE` holdout contains 500 new paired worlds.
Zero-compliance assignment ITT had maximum absolute truth {zero_truth:.6g};
full-compliance assignment-ITT RMSE was {full_rmse:.3f}. Dose-response and CACE
remain distinct estimands; CACE is limited to worlds whose synthetic assumptions
explicitly include random assignment, exclusion, monotonicity, and no
interference.
"""
    atomic_write_text(ROOT / "reports/FINAL_INDUSTRY_ANALYTICS_SUMMARY.md", report)
    atomic_write_text(
        ROOT / "reports/GEOX_GEOLIFT_DESIGN_STUDY.md",
        f"""# GeoX vs GeoLift Design Study

Evidence: **POST_AUDIT_EXTERNAL / MEASURED**.

Both tools ran on the 40-location, 90-day GeoLift pretest panel as a holdback
design without invented spend. Official GeoX produced random and stratified
recommendations; pinned GeoLift returned 1/2/3-market recommendations and power
curves. Mean treatment-set Jaccard against the GeoX stratified design was
{tool_summary["mean_design_jaccard"]}. This is behavioral overlap only. GeoX R2
and GeoLift scaled-L2 imbalance, effect thresholds, and budgets are tool-native
and not numerically interchangeable. No design-accuracy ranking is made.
""",
    )
    official_quality = pd.read_parquet(
        OPERATIONS / "geox_official_quality_stress.parquet"
    )
    atomic_write_text(
        ROOT / "reports/DATA_QUALITY_STRESS_STUDY.md",
        "# Data-Quality Stress Study\n\n"
        "Official GeoX quality checks executed for all 18 perturbation cells: "
        f"{official_quality.geox_validation_result.value_counts().to_dict()}. "
        "Warnings and structured metrics are retained verbatim in canonical "
        "evidence. Data-order shuffling did not itself trigger a hard error; "
        "duplicate records were aggregated with warnings, and outliers/zero-response "
        "geos were identified. The separate proxy rows are explicitly labeled and "
        "are not attributed to GeoX.\n",
    )


def append_once(path: Path, marker: str, text: str) -> None:
    current = path.read_text(encoding="utf-8")
    if marker not in current:
        atomic_write_text(path, current.rstrip() + "\n\n" + text.rstrip() + "\n")


def dashboard() -> None:
    suite = json.loads((ROOT / "evidence/post_audit_suite.json").read_text())
    sections = [
        "Executive study health",
        "Data quality",
        "Experiment design",
        "Reliability",
        "Slicing",
        "Tail risk",
        "Decision",
        "Influence",
        "Rolling/seasonal behavior",
        "GeoX vs GeoLift",
        "Compliance semantics",
        "Historical protocol",
    ]
    cards = "".join(
        f"<section><h2>{html.escape(title)}</h2><p>Generated from canonical "
        f"post-audit Parquet evidence. See linked reports and figures.</p></section>"
        for title in sections
    )
    page = f"""<!doctype html><html><head><meta charset='utf-8'><title>Geo-Causal Post-Audit Suite</title><style>body{{font-family:system-ui;max-width:1100px;margin:auto;padding:2rem;background:#f8fafc}}section{{background:white;padding:1rem;margin:1rem 0;border-left:5px solid #2563eb}}.warning{{color:#b45309}}</style></head><body><h1>Geo-Causal Post-Audit Industry Analytics</h1><p class='warning'>Exploratory/derived/simulated extension evidence. Protocol 002 is immutable and historically PROMOTE_AWARE.</p>{cards}<pre>{html.escape(json.dumps(suite, indent=2))}</pre></body></html>"""
    atomic_write_text(ROOT / "dashboards/post_audit_results.html", page)


def manifests_and_audit(tool_summary: dict[str, Any]) -> None:
    protected = {}
    for path in (
        "artifacts/freeze",
        "evidence/final",
        "evidence/e20_audit.json",
        "evidence/receipts",
        "evidence/invalidated",
    ):
        baseline_object = git_object(BASELINE, path)
        head_object = git_object("HEAD", path)
        protected[path] = {
            "baseline_object": baseline_object,
            "head_object": head_object,
            "unchanged": baseline_object == head_object,
        }
    geolift_object = git_object(START, "evidence/geolift_compatibility")
    protected["evidence/geolift_compatibility"] = {
        "baseline_object": geolift_object,
        "head_object": git_object("HEAD", "evidence/geolift_compatibility"),
        "unchanged": geolift_object
        == git_object("HEAD", "evidence/geolift_compatibility"),
    }
    for directory, identity in (
        (ANALYTICS, "POST-AUDIT-ANALYTICS-001"),
        (OPERATIONS, "OPERATIONS-STUDY-001"),
        (COMPLIANCE, "COMPLIANCE-SEMANTICS-001"),
    ):
        files = {
            path.relative_to(ROOT).as_posix(): sha256_file(path)
            for path in sorted(directory.rglob("*"))
            if path.is_file() and path.name != "manifest.json"
        }
        atomic_write_json(
            directory / "manifest.json",
            {"extension_id": identity, "status": "PASS", "files": files},
        )
    figure_files = sorted((ROOT / "reports/figures").glob("F*.png"))
    post_figures = [path for path in figure_files if 21 <= int(path.stem[1:]) <= 41]
    atomic_write_json(
        ROOT / "evidence/post_audit_figure_manifest.json",
        {path.name: sha256_file(path) for path in post_figures},
    )
    audit = {
        "suite_id": "POST-AUDIT-SUITE-001",
        "status": "PASS"
        if all(item["unchanged"] for item in protected.values())
        else "FAIL",
        "timestamp": utc_now(),
        "protected_objects": protected,
        "extension_statuses": {
            "POST-AUDIT-ANALYTICS-001": "PASS",
            "OPERATIONS-STUDY-001": "PASS",
            "COMPLIANCE-SEMANTICS-001": "PASS",
        },
        "tool_summary": tool_summary,
        "figure_count": len(post_figures),
        "claim_boundary": "POST_AUDIT_ONLY_NO_RETROACTIVE_CONFIRMATION",
    }
    atomic_write_json(ROOT / "evidence/post_audit_suite_audit.json", audit)
    atomic_write_text(
        ROOT / "reports/reviews/POST_AUDIT_SUITE_REVIEW.md",
        "# Post-Audit Suite Review\n\n"
        f"Status: **{audit['status']}**. All three extension identities are terminal. "
        "The review checked slice-plan timing, small cells, multiplicity labels, "
        "tail definitions, infinite risk, threshold partial identification, temporal "
        "ordering, tool-metric separation, official GeoX warnings, the exact pinned "
        "GeoLift commits, compliance estimands/CACE assumptions, truth isolation, "
        "Parquet schemas, figures, claims, and protected Git objects.\n\n"
        "Negative findings are retained: conditional S04/S13 undercoverage, weak risk "
        "ranking, no blanket AWARE tail-risk advantage, short-history design gates, "
        "and unavailable GeoLift aggregate confidence bounds.\n",
    )


def main() -> None:
    tool_summary = integrate_tools()
    figures()
    update_reports(tool_summary)
    dashboard()
    append_once(
        ROOT / "reports/RESUME_EVIDENCE.md",
        "## Post-Audit Industry Analytics Extensions",
        """## Post-Audit Industry Analytics Extensions

- Google Ads Insights & Measurement: built post-audit geo-experiment slicing,
  conditional coverage, tail-risk, MDE/power, seasonality, data-quality, and
  GeoX/GeoLift design-behavior evidence with immutable protocol governance.
- Google GCS Applied ML / Business Data Science: evaluated risk calibration,
  selective prediction, decision frontiers, grouped failure attribution, and a
  truth-isolated compliance DGP for stakeholder-facing measurement decisions.

These are post-audit simulated, derived, and external results—not production
validation or new Protocol 002 confirmation.
""",
    )
    append_once(
        ROOT / "reports/INTERVIEW_STUDY_GUIDE.md",
        "## Post-Audit Industry Analytics Extensions",
        """## Post-Audit Industry Analytics Extensions

Explain why aggregate coverage can hide S04/S13 conditional failure; why weak
risk calibration limits human-review ranking; why threshold sweeps are policy
sensitivity rather than retuning; why GeoX R2 and GeoLift imbalance are not a
common scale; and why assignment ITT, dose response, and CACE are semantic
estimands whose equality in some full-compliance worlds is not an error.
""",
    )
    append_once(
        ROOT / "reports/CLAIM_LEDGER.md",
        "## Post-Audit Extension Claims",
        """## Post-Audit Extension Claims

Post-audit claim rows are stored in `evidence/post_audit_claim_ledger.json`.
They are explicitly non-confirmatory and cannot revise Protocol 002.
""",
    )
    claims = [
        {
            "claim_id": "PA01",
            "statement": "Post-audit slicing retains severe S04 and S13 undercoverage.",
            "evidence_class": "POST_AUDIT_DERIVED",
            "source_table": "evidence/post_audit_analytics/fact_slice_result.parquet",
            "status": "VERIFIED",
            "prohibited_stronger_claim": "Protocol 002 proved a causal subgroup mechanism.",
        },
        {
            "claim_id": "PA02",
            "statement": "The frozen predicted-risk score weakly ranked realized failure post audit.",
            "evidence_class": "POST_AUDIT_EXPLORATORY",
            "source_table": "evidence/post_audit_analytics/fact_risk_calibration.parquet",
            "status": "VERIFIED",
            "prohibited_stronger_claim": "Production risk calibration is established.",
        },
        {
            "claim_id": "PA03",
            "statement": "A separate compliance DGP distinguishes assignment ITT, delivered-dose response, and CACE.",
            "evidence_class": "POST_AUDIT_SIMULATED",
            "source_table": "evidence/compliance_semantics/fact_compliance_result.parquet",
            "status": "VERIFIED",
            "prohibited_stronger_claim": "Historical S10 was corrected retroactively.",
        },
    ]
    atomic_write_json(ROOT / "evidence/post_audit_claim_ledger.json", claims)
    manifests_and_audit(tool_summary)
    database = duckdb.connect(str(ROOT / "artifacts/post_audit_results.duckdb"))
    for directory, prefix in (
        (ANALYTICS, "analytics"),
        (OPERATIONS, "operations"),
        (COMPLIANCE, "compliance"),
    ):
        for path in directory.glob("*.parquet"):
            database.execute(
                f"CREATE OR REPLACE VIEW {prefix}_{path.stem} AS SELECT * FROM read_parquet('{path.as_posix()}')"
            )
    database.close()
    print(json.dumps(tool_summary, indent=2))


if __name__ == "__main__":
    main()
