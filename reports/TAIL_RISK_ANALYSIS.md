# Tail-Risk Analysis

| selector_id | loss | n | median | p75 | p90 | p95 | p99 | maximum | cvar90 | cvar95 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A10_soft_blend | abs_error | 500 | 6720.58 | 13124.8 | 20541 | 26862.6 | 43508.7 | 81326.3 | 30731.2 | 38097.6 |
| A10_soft_blend | decision_regret | 500 | 0.4 | 0.4 | 0.5 | 3.48518 | 3.82907 | 3.86987 | 1.82395 | 3.65251 |
| A11_equal_weight_blend | abs_error | 500 | 7001.87 | 13219.7 | 20888.5 | 27269.1 | 43667.7 | 83829.4 | 31102.7 | 38510.8 |
| A11_equal_weight_blend | decision_regret | 500 | 0.4 | 0.4 | 0.5 | 3.48518 | 3.83906 | 3.94413 | 1.82574 | 3.65711 |
| A1_no_placebo | abs_error | 500 | 6572.9 | 11084.7 | 17613.1 | 23630.4 | 41275.9 | 87154.6 | 27845.9 | 35267.6 |
| A1_no_placebo | decision_regret | 500 | 0.4 | 0.4 | 0.4 | 0.4 | 3.56807 | 3.82897 | 0.474914 | 0.474914 |
| AWARE | abs_error | 500 | 6572.9 | 11084.7 | 17613.1 | 23630.4 | 41275.9 | 87154.6 | 27845.9 | 35267.6 |
| AWARE | decision_regret | 500 | 0.4 | 0.4 | 0.4 | 0.4 | 3.56807 | 3.82897 | 0.474914 | 0.474914 |
| fixed_did | abs_error | 500 | 6522.59 | 11082.9 | 17630.4 | 23724.7 | 41263.8 | 87154.6 | 28040.2 | 35579.7 |
| fixed_did | decision_regret | 500 | 0.4 | 0.4 | 0.4 | 0.4 | 3.56807 | 3.82897 | 0.472562 | 0.472562 |

The answer to whether AWARE reduced catastrophic loss is determined separately for mean and CVaR; modest mean performance cannot substitute for tail behavior.
