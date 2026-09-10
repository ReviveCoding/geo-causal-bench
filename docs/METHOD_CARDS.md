# Method Cards

All statuses begin `PENDING_QUALIFICATION`. A card becomes eligible only after
its known-answer result and adapter estimand contract pass. Inference marked
native is never represented as GeoX design-aware inference.

| ID | Estimator / target | Unit and timing | Assumptions | Inference | Software / compute | Direct eligibility |
|---|---|---|---|---|---|---|
| R0 | naive pre/post; descriptive change, not canonical ITT absent counterfactual mapping | aggregate assigned treated series, pre vs analysis window | stable untreated level | naive analytic | Python reference; CPU | diagnostic only |
| R1 | official GeoX TBR; total assigned-geo lift mapped to Track A ITT | geo assignment, saved design, frozen window | stable TBR relation and valid design/placebos | official design-aware placebo | `meridian-geox==1.0.1`; JAX GPU where used | yes after official example |
| R2 | classical SCM; aggregate treated counterfactual ITT | aggregate treated vs donor geos | convex-hull support, stable loadings, no contamination | in-space/time placebo; native | independent Python/R; CPU | yes after fixture |
| R3 | SDID; aggregate treated-panel ITT | geo panel, common Track A treatment time | weighted parallel trends, support | placebo/bootstrap native | official `synthdid` R; CPU | yes after Prop 99 |
| R4 | ASCM; aggregate treated-panel ITT | geo panel | outcome model stability plus support | package jackknife/bootstrap where valid | official `augsynth` R; CPU | yes after reference |
| R5 | BSTS/CausalImpact; cumulative counterfactual difference | aggregate treated response with donor predictors | unaffected controls, stable relationship/model | Bayesian posterior credible interval | official `CausalImpact` R; CPU | yes after official example; coverage empirical |
| R6 | Meta GeoLift lift mapped to assigned-geo ITT where package permits | package-specific geo/date contract | GeoLift SCM assumptions and package design | package inference | official GeoLift R; CPU | conditional after example |
| B0 | naive TWFE; coefficient | unit-time panel | strong homogeneous-effect interpretation and parallel trends | clustered analytic | R `fixest`; CPU | comparator; mapping-qualified only |
| B1 | TWFE event study; lead/lag coefficients | unit-time relative event | homogeneous effects/no contamination | clustered analytic | R `fixest`; CPU | diagnostic, not canonical under heterogeneity |
| B2 | Callaway–Sant'Anna `ATT(g,t)` and aggregates | treatment cohort × time | conditional/unconditional PT, overlap, no anticipation | multiplier bootstrap simultaneous bands | R `did`; CPU | yes for Track B |
| B3 | Sun–Abraham dynamic ATT | cohort × event time | cohort PT, no anticipation | clustered analytic/simultaneous as configured | R `fixest::sunab`; CPU | yes for Track B dynamics |
| B4 | panel SDID ATT | block-compatible panel | weighted PT/low-rank structure | package placebo/bootstrap | R `synthdid`; CPU | only adapter-compatible cells |
| B5 | panel ASCM ATT | cohort adapter-specific panel | stable outcome model/support | package native | R `augsynth`; CPU | only adapter-compatible cells |

## Controller cards

P0 gates with predeclared method-specific thresholds. P1 selects the eligible
method with minimum predicted transparent reliability loss and is primary. P2
soft-weights eligible methods; its uncertainty is exploratory unless the whole
weighting procedure is rerun inside valid resamples. P3 compares rule, ridge,
and boosted risk models using world-family-grouped validation; complexity is
retained only if it beats simpler policies. O0/SO0 opens truth only in scoring
and is never an input to development or final selectors.

All cards record failures in denominators and expose package version, status,
failure class, runtime, diagnostics, and artifact hash per invocation.
