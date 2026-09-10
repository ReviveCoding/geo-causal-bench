# Claim Ledger

| claim_id | statement | evidence_class | protocol_id | source/query | status | qualifiers | prohibited stronger claim |
|---|---|---|---|---|---|---|---|
| C01 | H1 clean RMSE ratio is 1.00 and passes 1.05 | SIMULATED | AWARE-GEO-e52a8660a97ef174 | `evidence/final/confirmatory_metrics.json:h1` | VERIFIED | 500-world mixture, 96 clean | universal noninferiority |
| C02 | H2 paired regret difference is -0.00210, CI [-0.00347,-0.00111] | SIMULATED | AWARE-GEO-e52a8660a97ef174 | `confirmatory_metrics.json:h2` | VERIFIED | synthetic frozen costs | real revenue gain |
| C03 | selection-aware coverage is 0.9089 | SIMULATED | AWARE-GEO-e52a8660a97ef174 | `confirmatory_metrics.json` | VERIFIED | aggregate; S04/S13 fail | nominal 95% universal coverage |
| C04 | null Type-I is 0.0246 | SIMULATED | AWARE-GEO-e52a8660a97ef174 | `confirmatory_metrics.json` | VERIFIED | selected nonabstained nulls | all-scenario Type-I control |
| C05 | AWARE selects DiD in 483/500 worlds | SIMULATED | AWARE-GEO-e52a8660a97ef174 | `fact_selector_result.parquet GROUP BY selected_method` | VERIFIED | selection policy | broad estimator switching |
| C06 | AWARE regret is 0.46972 vs fixed 0.47162 | SIMULATED | AWARE-GEO-e52a8660a97ef174 | `fact_decision.parquet`, frozen_primary | VERIFIED | normalized synthetic loss | profit improvement |
| C07 | JAX large-batch steady speedup is 24.84x | MEASURED | AWARE-GEO-e52a8660a97ef174 | `e19_scaling.json batch=256` | VERIFIED | synthetic kernel, compile excluded | application-wide GPU speedup |
| C08 | GeoX official example lift is 31,559.99 | EXTERNAL | AWARE-GEO-e52a8660a97ef174 | `fact_external_case.parquet D4` | VERIFIED | no known truth | estimator accuracy |
| C09 | GeoLift is gated by 210/105 incompatibility | EXTERNAL | AWARE-GEO-e52a8660a97ef174 | `package_qualification.json` | VERIFIED | package incompatibility | scientific invalidity of GeoLift |
| C10 | protocol 001 is invalid | DERIVED | AWARE-GEO-c0b13ec88b725728 | `evidence/invalidated/.../invalidation.json` | VERIFIED | truth-derived threshold | reuse of its favorable results |

## Post-Audit Extension Claims

Post-audit claim rows are stored in `evidence/post_audit_claim_ledger.json`.
They are explicitly non-confirmatory and cannot revise Protocol 002.
