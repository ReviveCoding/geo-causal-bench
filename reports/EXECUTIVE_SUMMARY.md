# Executive Summary

## Decision

**PROMOTE_AWARE** under the narrow frozen simulated benchmark for corrected
protocol `AWARE-GEO-e52a8660a97ef174`.

**SIMULATED:** On 500 protected randomized-geo worlds, AWARE-Select passed H1
clean noninferiority exactly (RMSE ratio 1.00; allowed <=1.05) and H2 stress
decision regret (paired AWARE-minus-fixed mean -0.00210; bootstrap 95% CI
-0.00347 to -0.00111). Selection-aware empirical coverage was 0.9089, null
Type-I 0.0246, clean abstention 0.0208, overall abstention 0.034, false launch
0.022, and false stop 0. AWARE selected the fixed DiD method in 483/500 worlds.

The practical interpretation is modest: AWARE's advantage came mainly from 17
redesign decisions, not broad estimator switching. No-abstention regret was
0.47162 versus full AWARE 0.46972. Soft/equal blends were worse (about 0.580
regret, 0.71 exploratory coverage). A GPU-boosted selector abstained on 96.8%
and is rejected as impractical.

The final aggregate coverage gate passed, but S04 structural-break coverage was
0.567 and S13 compound-OOD coverage 0.467. These material negative results
prohibit a universal reliability claim. **EXTERNAL:** Prop 99, mpdta, GeoLift,
and GeoX cases have no known counterfactual truth and do not rank accuracy.

Protocol 001's apparent success is invalid: adversarial review found hidden
truth affected its decision threshold. It was archived, fixed under a new
identity, and rerun with fresh worlds. That recovery is part of the result.
