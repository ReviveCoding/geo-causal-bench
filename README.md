# Geo-Causal Measurement & Econometrics Benchmark

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
found truth-derived decision materiality. It cannot support claims. GeoLift's
official example is gated by an upstream GeoLift/augsynth compatibility error.

## Runtime

The scientific runtime is WSL2 Ubuntu. Source `.codex-wsl-env.sh`; use the
isolated environment recorded by E00; then run:

```bash
python -m geocausal.cli pipeline --resume
```

The canonical results already exist. `pipeline --resume` reports the legal
resume state; reproduction and verification commands are in
`reports/REPRODUCTION_GUIDE.md`. Hosted CI is CPU-safe and does not require
GeoX, R, or a GPU.

See `EXECUTION_PLAN.md`, `docs/ESTIMAND_CONTRACT.md`, and
`docs/CLAIM_BOUNDARIES.md` before interpreting results.
