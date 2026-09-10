# Final Adversarial Audit

Protocol: `AWARE-GEO-e52a8660a97ef174`

Decision: **PASS WITH MATERIAL CLAIM LIMITS**.

## Integrity checks

- The assignment ITT estimand and Track A/Track B separation are preserved.
- Diagnostics and method commitment use only historical, design, and placebo
  evidence. Materiality is committed from pre-treatment response before truth
  access.
- All 500 final identity hashes match the freeze and truth ledger; each truth
  record was opened exactly once after method commitment.
- Frozen selector, scoring code, data identities, locks, hypotheses, margins,
  costs, multiplicity rules, and report schemas verify by SHA-256.
- Failed methods remain in denominators or carry an explicit failure category.
- Figures and headline numbers derive from canonical Parquet/DuckDB evidence.
- Protocol 001 and its apparent result remain preserved as `INVALID_PROTOCOL`.

## Falsification findings

No unresolved defect invalidates corrected protocol 002. The audit did find
scientifically important limitations: AWARE selected DiD in 483/500 worlds;
the regret gain is only 0.00190; conditional coverage was 0.567 in S04 and 0.467
in S13; soft/equal blends performed worse; the boosted selector abstained on
96.8%; Track B coverage was poor; and GeoLift did not pass executable package
qualification. External cases lack known truth and cannot establish accuracy.

These findings prohibit universal reliability, production, deployment, real
revenue, or general estimator-superiority claims. Subject to those limits, H1,
H2, every frozen aggregate critical gate, evidence verification, claim audit,
test/build gates, and reproducibility checks pass. E00--E20 therefore have
valid terminal states and E21 is omitted as optional.
