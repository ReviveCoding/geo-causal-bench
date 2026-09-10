# Geo-Causal Measurement & Econometrics Benchmark

## 1. Executive Summary

Corrected protocol `AWARE-GEO-e52a8660a97ef174` is narrowly promoted: frozen
H1/H2 and aggregate reliability gates passed. AWARE selected fixed DiD in
483/500 worlds, so abstention—not broad switching—explains the small advantage.

## 2. Motivation

Estimator choice is a pre-outcome decision under uncertain assumptions. The
benchmark tests whether diagnostic evidence can reduce invalid/economically
harmful choices without post-treatment leakage.

## 3. Desktop Study / Related Work

Official GeoX, GeoLift, did, fixest, synthdid, augsynth, and CausalImpact source
and primary papers govern adapters. See `docs/DESKTOP_STUDY.md`.

## 4. Research Questions

Can pre-treatment information gate, select, blend, or reject methods while
preserving clean performance and reducing stress-world regret?

## 5. Estimand Contract

Track A targets assignment ITT total incremental response across the frozen
window. Delivered-dose effects are secondary. Track B targets group-time,
event-time, cohort, and overall ATT separately.

## 6. Identification Assumptions

Randomization, no interference, timing, stable controls, donor support,
parallel trends, and inference assumptions are method-specific; see
`docs/IDENTIFICATION_ASSUMPTIONS.md`.

## 7. Public Data Sources

**EXTERNAL:** Eight exact-commit manifests cover GeoLift, Prop 99, mpdta, and
GeoX examples. Raw rows are ignored; hashes and acquisition code are retained.

## 8. EDA

GeoLift and GeoX differ sharply in cross-geo dependence. No duplicate keys,
missing cells, or negative primary outcomes were found in five characterized
panels.

## 9. Public-Data-Calibrated DGP

**SIMULATED:** Clean DGP mean 534 and CV 0.662 match the GeoX scale/dispersion
anchor. Dependence gaps are varied by scenarios rather than erased.

## 10. Randomized Geo Experiment Design

GeoX official random/stratified TBR designs return R2, A/A p-values, MDE,
budget, response share, and treatment counts. Fit is not treated as validity.

## 11. Observational DGP

A separately governed staggered generator varies conditional trends, timing,
heterogeneity, dynamics, anticipation, composition, latent confounding, cohort
imbalance, and unseen compounds.

## 12. Baseline Estimators

Official methods are known-answer qualified or gated. Fast Python estimators
are explicitly independent TBR, DiD, ridge SC, and simplex SC adapters.

## 13. Design-Aware Inference

GeoX results retain the original design and official inference. Independent
empirical intervals are not called GeoX or equated with randomization inference.

## 14. AWARE-Geo

Chronological prefit/diagnostic/placebo features feed method gates and a ridge
risk model. All-ineligible or excessive-risk worlds return REDESIGN.

## 15. Selection-Aware Inference

The protected estimator process receives observed arrays only, commits method,
interval, action threshold, and hash, then scoring opens truth once. Empirical
coverage evaluates the entire procedure.

## 16. Business Decision Model

Synthetic normalized costs are false launch 3, false stop 1.5, hold 0.4, and
redesign 0.35, with balanced and launch-averse sensitivities. No currency is
claimed real.

## 17. Experimental Governance

Protocol 001 was invalidated for truth-derived decision materiality. Protocol
002 fixed the boundary, used new seeds, froze, committed, tagged, and reran.

## 18. Clean Benchmark

Final clean AWARE and fixed DiD RMSE are both 7,667; H1 ratio 1.00 passes the
1.05 noninferiority margin.

## 19. Null Calibration

Final selection-aware null Type-I is 0.0246. The 1,000-world pre-freeze fixed
rates were 0.026--0.061 after initial 0.248--0.510 failure and calibration.

## 20. Single-Stress Results

Development S01--S12 coverage was 0.902--0.935 by method; final S04 coverage
fell to 0.567, showing structural breaks evade historical diagnostics.

## 21. Compound OOD Results

Estimator-only E10 S13 coverage was 0.577--0.643. Final selected coverage in
S13 was 0.467; the aggregate gate must not hide this scenario failure.

## 22. Final AWARE Confirmatory Test

H2 paired regret difference is -0.00210 (bootstrap 95% CI -0.00347 to
-0.00111). Aggregate coverage 0.9089, null Type-I 0.0246, clean abstention
0.0208, truth ledger 500/500: all frozen gates pass.

## 23. Ablations

No-abstention regret is 0.47162 versus 0.46972 full. Most feature removals are
identical; prefit affects abstention. Blends worsen regret/coverage; boosted
selection abstains 96.8%.

## 24. Observational DiD Benchmark

**SIMULATED, SEPARATE:** ASCM-adjusted approximation has lowest RMSE 0.369;
coverage across all independent adapters is only 0.30--0.513. No Track A score
is combined with these results.

## 25. External Case Studies

**EXTERNAL:** Prop 99, mpdta, GeoLift, and GeoX show behavior only. GeoLift is
gated; GeoX retained-design lift is 31,559.99 with interval
30,309.73--32,406.30. Truth is unknown.

## 26. Compute and GPU Analysis

**MEASURED:** Exactly one RTX GPU was used. Large batch JAX steady-state speedup
reached 24.84x, while compilation makes tiny one-off workloads less attractive.

## 27. Threats to Validity

Independent adapters are approximations, diagnostics are overly shared, final
scenario cells are ~31, OOD coverage fails, public examples are not a target
population, and synthetic decision costs govern H2.

## 28. Production Translation

Production would require prospective validation, business-owned loss ratios,
interference mapping, monitored delivery/carryover, and design-aware inference.

## 29. Limitations

No proprietary data, live market, real revenue, deployment, multi-GPU run,
universal validity, or GeoLift execution result is claimed.

## 30. Future Work

Multi-cell GeoX, MMM prior calibration, graph interference, matrix completion,
adaptive design, prospective panels, and distributed Monte Carlo remain future
work and cannot rewrite current claims.

## 31. Claim Boundaries

Every headline claim is linked to protocol/table/query in `CLAIM_LEDGER.md`.
Evidence classes are MEASURED, DERIVED, SIMULATED, EXTERNAL, PROJECTED, PENDING.

## 32. Conclusion

AWARE passes its narrow frozen promotion rule, but the result is an abstention
policy gain with fragile OOD coverage—not a new universally superior estimator.

## 33. Reproducibility Appendix

Locks, manifests, freeze hashes, protected identity ledger, canonical Parquet,
DuckDB views, figure hashes, tests, and commands are described in
`REPRODUCTION_GUIDE.md`.
