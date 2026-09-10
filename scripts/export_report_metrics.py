"""Export compact report-ready metrics from canonical evidence."""

from __future__ import annotations

import json
from pathlib import Path

import duckdb

root = Path(__file__).resolve().parents[1]
connection = duckdb.connect(str(root / "artifacts/results.duckdb"), read_only=True)


def rows(query: str) -> list[dict[str, object]]:
    return connection.execute(query).df().to_dict(orient="records")


payload = {
    "final_method": rows(
        "SELECT method_id, sqrt(avg(sq_error)) rmse, avg(bias) bias, "
        "avg(covered_truth::INT) coverage, avg((p_value<0.05)::INT) rejection, "
        "avg((status!='SUCCESS')::INT) failure_rate "
        "FROM final_estimators GROUP BY 1 ORDER BY 1"
    ),
    "final_scenario": rows(
        "SELECT scenario_id, count(*) worlds, avg(abstained::INT) abstention, "
        "avg(covered_truth::INT) coverage, avg(decision_regret) regret, "
        "avg(fixed_decision_regret) fixed_regret "
        "FROM final_selectors GROUP BY 1 ORDER BY 1"
    ),
    "observational": rows(
        "SELECT method_id, avg(bias) bias, sqrt(avg(sq_error)) rmse, "
        "avg(covered_truth::INT) coverage, avg(dynamic_event_time_rmse) dynamic_rmse, "
        "avg(pretrend_abs_mean) pretrend_abs "
        "FROM observational GROUP BY 1 ORDER BY 1"
    ),
    "ablations": rows(
        "SELECT ablation_id, avg(abstained::INT) abstention, "
        "avg(decision_regret) regret, avg(false_launch::INT) false_launch, "
        "avg(covered_truth::INT) coverage FROM ablations GROUP BY 1 ORDER BY 1"
    ),
    "decision": rows(
        "SELECT selector_id, cost_regime, avg(decision_regret) regret, "
        "max(decision_regret) worst_regret, avg(false_launch::INT) false_launch, "
        "avg(false_stop::INT) false_stop, avg(abstained::INT) redesign "
        "FROM decisions GROUP BY 1,2 ORDER BY 1,2"
    ),
}
connection.close()
output = root / "evidence" / "report_metrics.json"
output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
print(json.dumps(payload, indent=2, sort_keys=True))
