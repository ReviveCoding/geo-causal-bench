# Identification Assumptions

## Track A shared design assumptions

- Geographic assignment is implemented according to the recorded design and
  analyzed at the geographic randomization unit.
- Potential outcomes are well defined for the assignment contrast. Spillover,
  donor contamination, and cross-border interference violate no-interference
  and are explicit stress scenarios, not harmless noise.
- Missingness, aggregation, and measurement are not caused by treatment unless
  modeled as noncompliance/composition stress.
- ITT follows assignment even when delivered spend differs. Cooldown belongs to
  the estimand only when frozen in the analysis window.
- A design-optimized assignment does not justify iid regression inference.
  Randomization inference must reproduce its actual design support.

## Method-specific assumptions

| Method | Core identification/stability requirements | Principal diagnostics | Known failures |
|---|---|---|---|
| GeoX TBR | stable aggregate treated-control relationship; recorded GeoX design; valid placebo support | honest pre-R2, residual dependence, design-aware placebos | structural breaks, drift, weak placebos, provenance mismatch |
| Classical SC | treated counterfactual lies in donor convex hull; stable factor loadings; unaffected donors | pre-RMSE, max weight, HHI, effective donors, placebo gaps | extrapolation, concentrated donors, contamination, latent drift |
| SDID | weighted parallel trends after unit/time balancing; stable untreated structure | pre-fit, unit/time weight support, placebos | no overlap, anticipation, breaks, contamination |
| ASCM | outcome model plus usable donor support; tuning stability | pre-fit, extrapolation, model stability, donor sensitivity | model misspecification, weak support, high leverage |
| BSTS/CausalImpact | unaffected controls; stable relationship; correctly adequate state-space model | predictive checks, residual structure, placebo coverage | contaminated controls, regime change, prior/model sensitivity |
| GeoLift | package-specific SCM design/inference contract and unaffected donor pool | package balance/fit/placebos | poor donor pool, contamination, package/API failure |

## Track B assumptions

| Method | Required interpretation assumptions | Failure mode under stress |
|---|---|---|
| Naive/conventional TWFE | homogeneous or appropriately weighted effects plus parallel trends/no anticipation | negative/opaque weighting and lead/lag contamination |
| Callaway–Sant'Anna | group-time conditional/unconditional parallel trends, overlap, no anticipation, valid comparison group | latent confounding, anticipation, weak cohort support |
| Sun–Abraham | cohort-specific parallel trends, no anticipation, valid never/not-yet controls | latent confounding, composition, poor cohort support |
| SDID/ASCM panel | stable low-rank/weighted counterfactual structure and no anticipation | timing heterogeneity not aligned with adapter; latent drift |

Composition changes can alter the population estimand even when outcome models
fit. Anticipation changes treatment timing. Conditioning on post-treatment
covariates is prohibited. Pretrend tests have limited power and cannot certify
identification.
