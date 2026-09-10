"""Generate F01--F20 from canonical evidence and register them in DuckDB."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

root = Path(__file__).resolve().parents[1]
figure_root = root / "reports" / "figures"
figure_root.mkdir(parents=True, exist_ok=True)
database = duckdb.connect(str(root / "artifacts" / "results.duckdb"))
views = {
    "final_estimators": "evidence/final/fact_estimator_result.parquet",
    "final_selectors": "evidence/final/fact_selector_result.parquet",
    "development": "evidence/development/fact_estimator_result.parquet",
    "null_results": "evidence/qualification/fact_null_result.parquet",
    "observational": "evidence/observational/fact_observational_result.parquet",
    "ablations": "evidence/post_final/fact_ablation_result.parquet",
    "decisions": "evidence/post_final/fact_decision.parquet",
}
for name, relative in views.items():
    absolute = (root / relative).as_posix()
    database.execute(
        f"CREATE OR REPLACE VIEW {name} AS SELECT * FROM read_parquet('{absolute}')"
    )


def save(number: int, title: str) -> None:
    plt.title(title)
    plt.tight_layout()
    plt.savefig(figure_root / f"F{number:02d}.png", dpi=150)
    plt.close()


plt.figure(figsize=(10, 2.4))
stages = [
    "DATA",
    "DESIGN",
    "DIAGNOSTICS",
    "GATE/SELECT",
    "ESTIMATE",
    "INFER",
    "DECIDE",
    "AUDIT",
]
for index, stage in enumerate(stages):
    plt.text(
        index,
        0,
        stage,
        ha="center",
        va="center",
        bbox={"boxstyle": "round", "facecolor": "#dbeafe"},
    )
    if index < len(stages) - 1:
        plt.arrow(index + 0.18, 0, 0.62, 0, head_width=0.08, length_includes_head=True)
plt.xlim(-0.6, 7.6)
plt.ylim(-0.5, 0.5)
plt.axis("off")
save(1, "AWARE-Geo evidence-controlled architecture")

anchor = pd.read_parquet(root / "data/anchors/public_anchor_summary.parquet")
anchor.set_index("dataset_id")[["outcome_cv", "mean_acf1"]].plot(
    kind="bar", figsize=(8, 4)
)
save(2, "Public anchors: coefficient of variation and ACF1")

geox = json.loads((root / "evidence/geox_qualification.json").read_text())
frontier = pd.DataFrame(geox["design_comparison"]["design_metrics"]["head"])
plt.figure(figsize=(6, 4))
plt.scatter(frontier["r2"], frontier["mde"], c=frontier["budget"], cmap="viridis")
plt.colorbar(label="Projected budget")
plt.xlabel("Pretest R2")
plt.ylabel("MDE")
save(3, "GeoX ranked-design frontier (stored head)")

clean = database.execute(
    "SELECT method_id, sqrt(avg(sq_error)) rmse FROM development "
    "WHERE scenario_id='S00' GROUP BY 1"
).df()
clean.plot.bar(x="method_id", y="rmse", legend=False, figsize=(7, 4))
save(4, "Clean estimator RMSE (development evidence)")

null = database.execute(
    "SELECT method_id, avg(reject_null::INT) rate FROM null_results GROUP BY 1"
).df()
null.plot.bar(x="method_id", y="rate", legend=False, figsize=(7, 4))
plt.axhline(0.05, color="black", linestyle="--")
save(5, "Null Type-I rejection rate")

coverage = database.execute(
    "SELECT method_id, avg(covered_truth::INT) coverage "
    "FROM final_estimators GROUP BY 1"
).df()
coverage.plot.bar(x="method_id", y="coverage", legend=False, figsize=(7, 4))
plt.axhline(0.95, color="black", linestyle="--")
save(6, "Final estimator interval coverage")

for number, value, title in [
    (7, "sqrt(avg(sq_error))", "Scenario x estimator RMSE"),
    (8, "avg(covered_truth::INT)", "Scenario x estimator coverage"),
    (9, "avg((p_value < 0.05)::INT)", "Scenario x estimator rejection rate"),
]:
    table = database.execute(
        f"SELECT scenario_id, method_id, {value} metric "
        "FROM final_estimators GROUP BY 1,2"
    ).df()
    pivot = table.pivot(index="scenario_id", columns="method_id", values="metric")
    plt.figure(figsize=(8, 5))
    plt.imshow(pivot, aspect="auto", cmap="magma")
    plt.xticks(range(len(pivot.columns)), pivot.columns, rotation=35, ha="right")
    plt.yticks(range(len(pivot.index)), pivot.index)
    plt.colorbar()
    save(number, title)

decision = database.execute(
    "SELECT selector_id, max(decision_regret) worst FROM decisions "
    "WHERE cost_regime='frozen_primary' GROUP BY 1"
).df()
decision.plot.bar(x="selector_id", y="worst", legend=False, figsize=(8, 4))
save(10, "Worst-case normalized decision regret")

selected = database.execute(
    "SELECT selected_method, count(*) n FROM final_selectors "
    "WHERE selected_method IS NOT NULL GROUP BY 1"
).df()
selected.plot.bar(x="selected_method", y="n", legend=False, figsize=(6, 4))
save(11, "AWARE final selection frequency")

abstain = database.execute(
    "SELECT scenario_id, avg(abstained::INT) rate FROM final_selectors GROUP BY 1"
).df()
abstain.plot.bar(x="scenario_id", y="rate", legend=False, figsize=(8, 4))
save(12, "AWARE abstention by scenario")

metrics = json.loads((root / "evidence/final/confirmatory_metrics.json").read_text())
plt.figure(figsize=(5, 4))
plt.bar(
    ["AWARE", "Fixed", "Oracle"],
    [metrics["aware_mean_regret"], metrics["fixed_mean_regret"], 0],
)
save(13, "Oracle opportunity gap")

plt.figure(figsize=(5, 4))
plt.bar(
    ["False launch", "False stop"],
    [metrics["false_launch_rate"], metrics["false_stop_rate"]],
)
save(14, "Final false-launch and false-stop rates")

ablation = database.execute(
    "SELECT ablation_id, avg(decision_regret) regret "
    "FROM ablations GROUP BY 1 ORDER BY 1"
).df()
ablation.plot.bar(x="ablation_id", y="regret", legend=False, figsize=(11, 4))
save(15, "AWARE ablation decision regret")

prop = pd.read_csv(root / "data/raw/D2/California_Proposition_99.csv", sep=";")
plt.figure(figsize=(7, 4))
for state, label in [(3, "California"), (prop.State.unique()[1], "Example donor")]:
    subset = prop.loc[prop.State == state]
    plt.plot(subset.Year, subset.PacksPerCapita, label=label)
plt.axvline(1988, color="black", linestyle="--")
plt.legend()
save(16, "Proposition 99 observed trajectories (no known counterfactual truth)")

obs = database.execute(
    "SELECT method_id, avg(dynamic_event_time_rmse) rmse FROM observational GROUP BY 1"
).df()
obs.plot.bar(x="method_id", y="rmse", legend=False, figsize=(9, 4))
save(17, "Staggered-panel dynamic-effect error")

final_perf = database.execute(
    "SELECT method_id, sqrt(avg(sq_error)) rmse, "
    "avg(covered_truth::INT) coverage FROM final_estimators GROUP BY 1"
).df()
plt.figure(figsize=(6, 4))
plt.scatter(final_perf.rmse, final_perf.coverage)
for row in final_perf.itertuples():
    plt.annotate(row.method_id, (row.rmse, row.coverage), fontsize=7)
plt.xlabel("RMSE")
plt.ylabel("Coverage")
save(18, "Estimator error/reliability Pareto")

scaling = json.loads((root / "evidence/runtime/e19_scaling.json").read_text())
scale = pd.DataFrame(scaling["gpu_batch_scaling"])
plt.figure(figsize=(6, 4))
plt.plot(scale.batch, scale.gpu_worlds_per_sec, marker="o", label="JAX GPU")
plt.plot(scale.batch, scale.cpu_worlds_per_sec, marker="o", label="NumPy CPU")
plt.legend()
plt.xlabel("Batch")
plt.ylabel("World-equivalents/sec")
save(19, "JAX GPU vs NumPy CPU batch scaling")

score = {
    "H1": metrics["h1"]["pass"],
    "H2": metrics["h2"]["pass"],
    **metrics["critical_gates"],
}
plt.figure(figsize=(7, 3))
plt.bar(
    score.keys(),
    [1 if value else 0 for value in score.values()],
    color=["#16a34a" if value else "#dc2626" for value in score.values()],
)
plt.ylim(0, 1.15)
plt.xticks(rotation=30, ha="right")
save(20, "Frozen promotion scorecard")

database.close()
manifest = {}
for path in sorted(figure_root.glob("F*.png")):
    manifest[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
(root / "evidence" / "figure_manifest.json").write_text(
    json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
)
print(
    json.dumps(
        {"figures": len(manifest), "duckdb": "artifacts/results.duckdb"}, indent=2
    )
)
