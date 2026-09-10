# Development Experiment Protocol

Status: DEVELOPMENT; not the E13 freeze.

Track A begins with 40 geos, 168 pre-days split chronologically into
P_FIT/P_DIAGNOSTIC/P_PLACEBO_VALIDATION near 60/20/20, 28 intervention days,
7 cooldown days, conversion KPI, single-cell heavy-up, stratified assignment
where appropriate, two-sided alpha 0.05, and target power 0.80. Sensitivities
use one-factor-at-a-time cells plus selected interactions; no full Cartesian
product.

Track A scenarios are S00--S13 exactly as specified by the master program. S06
uses a seeded deterministic spatial/network graph; S10 stores assignment and
delivered dose separately; S11 uses explicit decaying carryover; S13 combines
violations whose parameter clusters are excluded from AWARE development.
Track B scenarios O00--O09 use separate generators and evidence tables.

Development progresses smoke (10--20), pilot (~50), development (~200),
qualification (300--500), null calibration (target ≥1,000 where feasible), and
final (500--1,000 based on preregistered precision/runtime). A hard ceiling is
2,000 independent worlds per cell. Final budgets cannot be reduced after result
access. `reports/COMPUTE_BUDGET.md` must precede production.

AWARE features are pre-treatment only. Eligibility precedes ranking. Risk loss
keeps normalized error, miscoverage, false positive, sign error, method failure,
decision regret, and abstention visible. Cost ratios make harmful/null false
launches more costly than holds and are frozen before E14. Cross-validation
groups complete world families/parameter clusters.

H1 is clean-world noninferiority of AWARE-Select error versus the frozen
strongest fixed estimator. The candidate relative RMSE margin is 5% but remains
development-only until frozen. H2 is paired stress/OOD normalized decision
regret improvement over the strongest frozen fixed selector. H1 and H2 are a
conjunctive promotion rule; critical Type-I, coverage, failures, sign error,
false launch, clean abstention, and integrity gates are also conjunctive.
Secondary confirmatory contrasts use predefined Holm families; exploratory
scenario discovery uses declared BH-FDR families.

Each independent final world is hidden, exposes historical data, runs
diagnostics/eligibility/selection, commits method or abstention, exposes final
observations, estimates, and only then allows scoring to open truth with a
logged timestamp/protocol/world hash. Canonical scoring completes before
analysis. A scientific-semantic post-freeze change creates a new protocol.
