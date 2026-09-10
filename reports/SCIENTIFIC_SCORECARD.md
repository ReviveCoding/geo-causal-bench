# Scientific Scorecard

Protocol: `AWARE-GEO-e52a8660a97ef174`. Evidence: **SIMULATED** unless noted.

| Gate | Frozen rule | Result | Status |
|---|---:|---:|---|
| H1 clean RMSE ratio | <= 1.05 | 1.0000 | PASS |
| H2 paired regret CI upper | < 0 | -0.00111 | PASS |
| Selection-aware coverage | >= 0.90 | 0.9089 | PASS |
| Null Type-I | <= 0.075 | 0.0246 | PASS |
| Clean abstention | <= 0.10 | 0.0208 | PASS |
| Truth ledger | 500/500 | 500/500 | PASS |

Final decision: **PROMOTE_AWARE**. This conjunctive outcome cannot be converted
into a claim that the learned selector generally outperforms DiD: it chose DiD
96.6% of the time and the absolute regret improvement was 0.00190 overall.
