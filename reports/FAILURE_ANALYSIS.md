# Failure Analysis

- **PROTOCOL_INVALIDATION:** Protocol 001 used hidden truth to derive decision
  materiality in scoring. Its E14 outputs are archived and prohibited.
- **PACKAGE_INCOMPATIBILITY:** GeoLift 2.7.5 plus augsynth 0.2.0 fails the
  official two-market example with a 210/105-row tibble mismatch.
- **ENGINEERING_FAILURE:** Initial JAX-array ingestion into XGBoost required
  absent CuPy; host NumPy ingestion with CUDA training succeeded.
- **ENGINEERING_FAILURE:** Initial source R installs failed because an isolated
  PATH omitted compiler wrappers/system utilities; corrected PATH succeeded.
- **STATISTICAL_FAILURE:** Uncalibrated independent intervals rejected nulls at
  0.248--0.510. Pre-freeze empirical calibration corrected the final procedure.
- **SCIENTIFIC_GATE_FAILURE (scenario-level):** Final S04 coverage was 0.567 and
  S13 coverage 0.467 despite aggregate coverage passing.
- **STATISTICAL/DECISION FAILURE:** Soft and equal blends had 0.71 exploratory
  coverage and roughly 0.580 regret; boosted selection abstained 96.8%.
- **NEGATIVE COMPUTE RESULT:** XGBoost warned that CPU input caused DMatrix
  fallback during GPU prediction. Training still ran on `cuda:0`; this overhead
  is not hidden.

No package incompatibility is interpreted as evidence against a method's
scientific validity, and no failed invocation was removed from its denominator.
