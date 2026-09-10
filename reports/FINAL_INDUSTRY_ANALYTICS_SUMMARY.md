# Final Industry Analytics Summary

All findings are post-audit. Protocol 002 remains historically `PROMOTE_AWARE`.

## Reliability

- S04 coverage: 0.567; S13 coverage:
  0.467. These failures persist.
- Predicted-risk Spearman correlation with realized procedure loss was
  0.024; catastrophic-loss AUROC was
  0.362. The frozen risk score did not meaningfully
  rank studies for review in this completed sample.
- AWARE decision-regret CVaR95 was 0.475, versus
  0.473 for fixed DiD. Tail-risk superiority is not claimed.

## Operations

- Official GeoX: 12 successful new design cells;
  12 duration cells gated by insufficient
  history. All official warning/error text is retained.
- Pinned GeoLift: 80 selected-market rows and
  8 power rows completed. GeoLift/GeoX native
  metrics were not forced onto a common scale.
- Seasonal coverage by history was {"84": 0.725, "168": 0.8111111111111111, "365": 0.8694444444444445}.
- Mean rejection rates at 0/0.5/1/1.5 MDE were
  {"0.0": 0.049166666666666664, "0.5": 0.27416666666666667, "1.0": 0.8095833333333333, "1.5": 0.9879166666666667}. These analytic design simulations do
  not validate Protocol 002 power.

## Compliance semantics

The separate `DGP_A_v2_COMPLIANCE` holdout contains 500 new paired worlds.
Zero-compliance assignment ITT had maximum absolute truth 0;
full-compliance assignment-ITT RMSE was 1181.963. Dose-response and CACE
remain distinct estimands; CACE is limited to worlds whose synthetic assumptions
explicitly include random assignment, exclusion, monotonicity, and no
interference.
