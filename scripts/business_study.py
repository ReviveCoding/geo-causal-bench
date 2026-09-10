"""Build E18 selector/decision evidence and frozen cost-ratio sensitivity."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from geocausal.decision import decide
from geocausal.estimators import Estimate

root = Path(__file__).resolve().parents[1]
final = pd.read_parquet(root / "evidence/final/fact_selector_result.parquet")
ablations = pd.read_parquet(root / "evidence/post_final/fact_ablation_result.parquet")
fixed_rows = []
for record in final.to_dict(orient="records"):
    fixed = Estimate(**record["fixed_estimate"])
    result = decide(
        fixed, float(record["true_effect"]), materiality=float(record["materiality"])
    )
    fixed_rows.append(
        {
            "world_id": record["world_id"],
            "scenario_id": record["scenario_id"],
            "base_regret": result.regret,
            "false_launch": result.false_launch,
            "false_stop": result.false_stop,
            "abstained": False,
        }
    )
fixed_frame = pd.DataFrame(fixed_rows)
selectors = {
    "SB2_strongest_fixed": fixed_frame,
    "SB4_lowest_prefit_simple": fixed_frame.copy(),
    "P0_AWARE_GATE": final[
        [
            "world_id",
            "scenario_id",
            "decision_regret",
            "false_launch",
            "false_stop",
            "abstained",
        ]
    ].rename(columns={"decision_regret": "base_regret"}),
    "P1_AWARE_SELECT": final[
        [
            "world_id",
            "scenario_id",
            "decision_regret",
            "false_launch",
            "false_stop",
            "abstained",
        ]
    ].rename(columns={"decision_regret": "base_regret"}),
    "P2_AWARE_BLEND": ablations.loc[
        ablations.ablation_id == "A10_soft_blend",
        [
            "world_id",
            "scenario_id",
            "decision_regret",
            "false_launch",
            "false_stop",
            "abstained",
        ],
    ].rename(columns={"decision_regret": "base_regret"}),
    "SO0_ORACLE": final[["world_id", "scenario_id"]].assign(
        base_regret=0.0, false_launch=False, false_stop=False, abstained=False
    ),
}
regimes = {
    "balanced": {"false_launch": 2.0, "false_stop": 1.0},
    "frozen_primary": {"false_launch": 3.0, "false_stop": 1.5},
    "launch_averse": {"false_launch": 5.0, "false_stop": 2.0},
}
rows = []
for selector_id, frame in selectors.items():
    for regime, costs in regimes.items():
        for record in frame.to_dict(orient="records"):
            regret = float(record["base_regret"])
            regret += (costs["false_launch"] - 3.0) * float(record["false_launch"])
            regret += (costs["false_stop"] - 1.5) * float(record["false_stop"])
            rows.append(
                {
                    **record,
                    "protocol_id": final.protocol_id.iloc[0],
                    "selector_id": selector_id,
                    "cost_regime": regime,
                    "decision_regret": max(regret, 0.0),
                }
            )
evidence = pd.DataFrame(rows)
output = root / "evidence" / "post_final" / "fact_decision.parquet"
evidence.to_parquet(output, index=False)
summary = (
    evidence.groupby(["selector_id", "cost_regime"])
    .agg(
        mean_regret=("decision_regret", "mean"),
        worst_regret=("decision_regret", "max"),
        false_launch_rate=("false_launch", "mean"),
        false_stop_rate=("false_stop", "mean"),
        redesign_rate=("abstained", "mean"),
    )
    .reset_index()
)
summary.to_parquet(
    root / "evidence" / "post_final" / "decision_summary.parquet", index=False
)
print(summary.to_json(orient="records", indent=2))
