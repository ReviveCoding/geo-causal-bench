# E05 Phase and Adversarial Review

Status: **COMPLETE WITH GATED COMPONENT**.

Maintained upstream known answers passed for synthdid Prop 99 (-15.60383 vs
-15.604), did mpdta dynamic ATT (-0.0772398 vs -0.0772), Sun-Abraham's official
fixest `base_stagg` ATT, Augmented SCM Kansas (-0.0294347 vs -0.0294), and the
CausalImpact toy intervention (10.51 vs 10, tolerance 3). GeoX 1.0.1 passed its
retained-design official analysis and design comparison.

GeoLift 2.7.5 with augsynth 0.2.0 is GATED: the official Chicago/Portland
example fails inside maintained `augsynth::treated_table`, where 210 observed
rows cannot populate a 105-row tibble. The full initial and corrected adapter
runs are preserved. No local patch or homemade method inherits the GeoLift
label. Adversarial checks found and corrected two local adapter errors
(Sun-Abraham namespace use and augsynth summary extraction); the remaining
GeoLift failure is upstream compatibility, not evidence against its science.
