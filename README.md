# Geo-Causal Measurement & Econometrics Benchmark

**AWARE-Geo: Assumption-Aware Reliability Evaluation for Geographic Causal
Measurement**

This repository is an evidence-controlled research benchmark for deciding when
a geo-causal estimator should be selected, blended, or rejected using only
information available before final treatment outcomes are inspected. The
primary domain is randomized geographic incrementality; observational
staggered-panel evidence is separate. AWARE-Geo is a controller, not a new
universal treatment-effect estimator.

Scientific results are pending until the frozen E14 evaluation and E20 audit.
No preliminary number in development artifacts is a headline claim.

## Runtime

The scientific runtime is WSL2 Ubuntu. Source `.codex-wsl-env.sh`; use the
isolated environment recorded by E00; then run:

```bash
python -m geocausal.cli pipeline --resume
```

The pipeline writes hash-verified phase receipts, canonical Parquet evidence,
and reports. Hosted CI is CPU-safe and does not require GeoX, R, or a GPU.

See `EXECUTION_PLAN.md`, `docs/ESTIMAND_CONTRACT.md`, and
`docs/CLAIM_BOUNDARIES.md` before interpreting results.
