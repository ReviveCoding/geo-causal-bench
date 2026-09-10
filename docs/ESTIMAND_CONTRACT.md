# Estimand Contract

Version: development-1.0. No quantitative comparison is valid until its
adapter declares all fields in this contract and maps its target to the relevant
canonical estimand.

## Track A — randomized geographic incrementality

The primary estimand is assignment intent-to-treat (ITT) incremental response
among assigned treatment geographies over the frozen analysis window,
including the prespecified cooldown when applicable, relative to the
no-treatment potential outcome:

\[
\tau_{ITT}=\sum_{i:Z_i=1}\sum_{t\in W}
\{Y_{it}(Z_i=1)-Y_{it}(Z_i=0)\}.
\]

The randomization unit is the geography. `Z_i` is assignment, not observed
delivery. In heavy-up experiments the intervention is incremental spend among
assigned geographies. Holdback and go-dark use their own assignment contrasts
but retain assignment-based ITT.

Required reports, when meaningful, are total incremental conversions, percent
lift against the no-treatment counterfactual, incremental conversions per
incremental spend, and effect per treated geo. Delivered-dose effects are
secondary, explicitly labeled, and never substituted for ITT. S10 stores
assignment, delivered dose, ITT truth, and dose-response truth separately.

For an estimator to enter direct Track A accuracy comparisons, its estimate
must aggregate the assigned treated geographies and the exact frozen analysis
window against their no-treatment counterfactual. A single-treated-unit SCM may
enter only after prespecified aggregation of assigned treated geographies into
one treated series. GeoX official outputs map `lift` to total ITT only when the
saved design, assignment, dates, and experiment type match the world contract.

## Track B — observational staggered panels

Track B uses separate evidence and never shares a numeric leaderboard with
Track A. Canonical targets are group-time `ATT(g,t)`, event-time dynamic ATT,
cohort-specific ATT, and an overall ATT aggregated with disclosed cohort/time
weights. Conventional TWFE coefficients that mix already-treated comparisons
or heterogeneous cohort effects are not silently relabeled as canonical ATT.

## Mandatory adapter declaration

Every adapter emits:

```yaml
estimator_name: string
target_estimand: string
canonical_mapping: string
unit_of_analysis: string
treatment_definition: string
treatment_timing: string
required_assumptions: [string]
inference_method: string
```

It also declares `direct_comparison_eligible`, its evidence domain, package and
version, randomization unit, clustering unit, and failure status. A method that
cannot legitimately map to the canonical target is retained for descriptive or
diagnostic evidence but excluded from the relevant direct accuracy contrast.

## Inference contract

Estimator-native uncertainty and design/randomization-aware uncertainty are
different fields. GeoX official design-aware results preserve the loaded design
provenance. Independent estimators under optimized assignments may report their
native interval plus a separately identified design-aware interval only when
the actual assignment support/mechanism is reproduced. Selected nominal
intervals are not called post-selection 95% intervals; empirical end-to-end
coverage is scored across independent worlds after the whole procedure runs.
