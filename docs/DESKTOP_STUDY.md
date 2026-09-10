# Authoritative Desktop Study

Study date: 2026-09-09. Sources were restricted to official documentation,
official source repositories, package documentation, and primary literature.
Package behavior remains subject to executable qualification.

## Meridian GeoX

Google released the separate `meridian-geox` package in 2026. The official
[repository](https://github.com/google/meridian-geox), [API reference](https://developers.google.com/meridian/geox/api-reference),
[validation guide](https://developers.google.com/meridian/geox/data-validation-and-quality-checks),
and [robust-inference guide](https://developers.google.com/meridian/geox/robust-inference)
are the behavioral authorities. The [research publication](https://research.google/pubs/meridian-geox-an-open-source-framework-for-precision-and-efficiency-in-geo-experiments/)
motivates TBR, SC, SDID, and design-aware inference, but paper-level method
coverage does not establish released API support.

Resolved PyPI release 1.0.1 (2026-09-03) exposes TBR and SDID enum values,
random and stratified assignment, holdback/go-dark/heavy-up experiment types,
design provenance serialization, structured quality results, and analysis
outputs. Executable source inspection found that both design scoring branches
raise on non-TBR and analysis explicitly rejects non-TBR. Therefore official
GeoX 1.0.1 means TBR only in this benchmark; SC/SDID implementations are
independent references. Details are in `docs/GEOX_CAPABILITY_NOTES.md`.

GeoX inference samples placebo assignments from the design-compatible support,
not arbitrary label shuffles. It tests a sharp null and constructs empirical
uncertainty from valid placebo designs. The exact saved `Design` must be loaded
for analysis. Official validation failures halt; quality warnings and their
structured objects are evidence. Documented hard-coded warnings include high
missingness and more than 500 geos.

## Synthetic-control family

Classical SCM constructs a convex donor combination to reproduce pre-treatment
outcomes/covariates; reliability depends on donor support, pre-fit, absence of
treated donor contamination, and stable post-treatment relations. Abadie's
[JEL review](https://www.aeaweb.org/articles?id=10.1257%2Fjel.20191450)
emphasizes design and data requirements.

Synthetic DiD combines unit and time weighting to weaken the respective
extrapolation weaknesses of SCM and DiD. The official
[synthdid site and Prop 99 example](https://synth-inference.github.io/synthdid/)
and [paper-result reproduction](https://synth-inference.github.io/synthdid/articles/paper-results.html)
define the maintained implementation.

ASCM augments SCM with an outcome model to reduce bias from imperfect balance,
at the price of model dependence/extrapolation and tuning sensitivity. The
official [augsynth repository](https://github.com/ebenmichael/augsynth) and
[primary paper](https://arxiv.org/abs/1811.04170) define the candidate.

## BSTS / CausalImpact

Google's [CausalImpact repository](https://github.com/google/CausalImpact) and
[worked example](https://google.github.io/CausalImpact/CausalImpact.html)
require unaffected controls and stability of the treated-control relationship
after intervention. Posterior credible intervals express the fitted Bayesian
model's uncertainty; they are not randomization intervals and can miscover when
controls are contaminated or the relationship shifts.

## Meta GeoLift

The official [GeoLift repository](https://github.com/facebookincubator/GeoLift)
describes an end-to-end geo-experiment workflow based on synthetic controls,
with design/power, inference, and plotting. The official
[methodology page](https://facebookincubator.github.io/GeoLift/docs/Methodology/)
calls SCM-based geo work a quasi-experimental alternative. In this benchmark it
is included where its package contract and estimand map legitimately; package
failure is GATED rather than replaced under the GeoLift label.

## Staggered difference-in-differences

Callaway–Sant'Anna identifies `ATT(g,t)` under no anticipation, overlap, and
unconditional or covariate-conditional parallel trends, with disclosed control
groups and aggregation. The author's [official software page](https://psantanna.com/software/),
[primary paper](https://arxiv.org/abs/1803.09015), and maintained `did` package
govern B2.

Sun–Abraham shows conventional event-study coefficients can be contaminated by
effects from other relative periods under heterogeneous timing/effects and
proposes cohort-by-relative-time interactions. Sources are the
[primary paper](https://arxiv.org/abs/1804.05785) and maintained
[`fixest::sunab`](https://lrberge.github.io/fixest/reference/sunab.html).
Pretrend non-rejection is not proof of parallel trends; apparent leads can also
be artifacts of heterogeneous effects in conventional TWFE.

## Consequences for AWARE-Geo

Eligibility must be method-specific. Fit alone cannot prove causal validity.
Placebos diagnose observed historical stability but do not detect every future
violation. Randomized and observational evidence remain separate. External
panels without truth can show fit, sensitivity, agreement, and abstention, but
cannot rank estimator accuracy. AWARE itself is evaluated as a complete
selection procedure with empirical Monte Carlo coverage and may validly fail.
