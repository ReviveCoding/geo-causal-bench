# Interview Study Guide

## Core identification

DiD needs a defensible untreated trend counterfactual; a nonsignificant pretrend
does not prove it. Conventional TWFE mixes comparisons under staggered timing
and can misweight heterogeneous dynamic effects. Callaway-Sant'Anna estimates
group-time ATT against never/not-yet treated controls. Sun-Abraham estimates
cohort-by-relative-time effects before aggregation. ATT describes treated units;
assignment ITT includes noncompliance and must not be replaced by dose response.

SCM builds a convex donor counterfactual; donor support, fit, concentration, and
placebos matter. SDID combines unit/time weighting with DiD. ASCM augments SCM
with an outcome model but can extrapolate. BSTS/CausalImpact produces posterior
counterfactual uncertainty conditional on stable controls/model assumptions.

## Geo experiments

GeoX design balances geos and reports R2, A/A behavior, MDE, budget, treatment
share, and exclusions. High R2 is not causal proof. MDE is the effect size a
design can detect at chosen alpha/power, not the smallest economically useful
effect. Optimized assignments need design-aware/randomization-aware inference;
a generic regression p-value is not equivalent. Spillover violates no
interference, contamination erodes contrast, noncompliance separates ITT from
dose effects, and carryover demands an adequate cooldown.

## Diagnostics, selection, and decisions

Placebos test whether the full pre-period procedure invents effects; they do not
guarantee future validity. AWARE orders diagnostics -> eligibility -> risk ->
select/blend/abstain. Selection-aware coverage is measured by repeating the
whole procedure on independent worlds, not quoting the selected method's nominal
95% interval. H1/H2 are conjunctive; Holm governs declared secondary families
and BH-FDR is reserved for exploration. False launches cost more than holds in
the synthetic decision model; oracle decisions are scoring-only.

## What happened and why

Null intervals initially failed because serial/cross-geo error made naive
standard errors too small; pre-freeze empirical calibration fixed the procedure.
Initial gates abstained almost everywhere because public-shaped clean prefit R2
was below an arbitrary 0.50 cutoff; development quantiles replaced it. Final
AWARE mostly chose DiD, so its small H2 gain came from redesign decisions.
Blends increased false launches and had invalid exploratory uncertainty. The
boosted selector learned high predicted risk and abstained almost everywhere,
showing complexity without usable calibration. Structural-break and compound
OOD coverage failed because pre-period fit could not anticipate abrupt outcome
regime changes. Track B coverage was poor because approximate intervals and
heterogeneous timing/confounding stressed identification.

Most importantly, protocol 001 was invalidated: truth-derived materiality leaked
into the action. A new identity, new worlds, and a pre-treatment committed
threshold were required. This demonstrates why causal governance is part of the
scientific method, not paperwork after modeling.
