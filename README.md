# Geo-Causal Measurement & Econometrics Benchmark

[![CI](https://github.com/ReviveCoding/geo-causal-bench/actions/workflows/ci.yml/badge.svg)](https://github.com/ReviveCoding/geo-causal-bench/actions/workflows/ci.yml)

**AWARE-Geo: Assumption-Aware Reliability Evaluation for Geographic Causal
Measurement**

This repository is an evidence-controlled research benchmark for deciding when
a geo-causal estimator should be selected, blended, or rejected using only
information available before final treatment outcomes are inspected. The
primary domain is randomized geographic incrementality; observational
staggered-panel evidence is separate. AWARE-Geo is a controller, not a new
universal treatment-effect estimator.

The corrected frozen protocol `AWARE-GEO-e52a8660a97ef174` completed 500 final
worlds. **SIMULATED:** H1 clean noninferiority passed (RMSE ratio 1.00 versus
fixed DiD); H2 passed with a small paired normalized-regret difference of
-0.00210 (bootstrap 95% CI -0.00347 to -0.00111). Frozen Type-I, coverage,
clean-abstention, and truth-ledger gates passed. AWARE chose DiD in 483/500
worlds, so the evidence supports a narrow promotion of the gated decision
procedure, not broad learned estimator-selection superiority.

Protocol 001 is preserved as invalid because a post-run adversarial review
found truth-derived decision materiality. It cannot support claims. Protocol
002's GeoLift result remains historically gated; the separate post-audit
`GEOLIFT-COMPAT-001` extension qualified unmodified GeoLift 2.7.5 against an
exact earlier unmodified augsynth commit, without changing the frozen result.

## Evidence domains and integrations

- **Randomized geo experiments:** the primary known-truth simulation track,
  including clean, null, single-stress, and compound-OOD worlds.
- **Observational staggered panels:** a separately governed secondary track for
  heterogeneous timing, dynamic effects, anticipation, and parallel-trends
  failures. It is not mixed into the randomized leaderboard.
- **Industry tools:** executable Meridian GeoX design/analysis qualification
  and an exact-commit GeoLift compatibility overlay. Tool-native design metrics
  are not treated as interchangeable or as an accuracy leaderboard.
- **Econometric baselines:** DiD, synthetic-control-family, staggered-DiD, and
  structural time-series implementations are qualified or transparently gated.

## Post-audit findings

The completed exploratory extensions intentionally preserve results that limit
the headline finding. S04 structural-break and S13 compound-OOD coverage was
0.567 and 0.467. Predicted AWARE risk weakly ranked realized failure (Spearman
0.024; catastrophic-loss AUROC 0.362), and fixed DiD had slightly lower CVaR95
decision regret than AWARE. Longer seasonal histories improved simulated
coverage but did not restore nominal coverage. Separate MDE/power and formal
assignment-versus-dose compliance studies provide operational evidence without
retroactively becoming Protocol 002 confirmation.

## Runtime

The original scientific runtime was WSL2 Ubuntu with one physical NVIDIA GPU.
GPU claims are limited to the measured JAX/GeoX/XGBoost workloads; this is not
multi-GPU or distributed evidence. Core verification is CPU-safe:

```bash
uv sync --locked --extra dev
uv run python scripts/verify_evidence.py --read-only
uv run python scripts/verify_post_audit_suite.py
```

The canonical results already exist. `python -m geocausal.cli pipeline
--resume` reports the legal resume state and refuses to rerun completed
protected evaluation. Hosted CI verifies software, package, claims, manifests,
and immutable evidence contracts; it does not rerun protected worlds, heavy
Monte Carlo, CUDA, or external R estimator stacks.

Start with `reports/FINAL_INDUSTRY_ANALYTICS_SUMMARY.md`, then see
`EXECUTION_PLAN.md`, `docs/ESTIMAND_CONTRACT.md`,
`docs/CLAIM_BOUNDARIES.md`, and `reports/REPRODUCTION_GUIDE.md`. Public
visibility does not make third-party data or dependencies part of this
project's MIT grant; their original licenses and source manifests continue to
govern them.
