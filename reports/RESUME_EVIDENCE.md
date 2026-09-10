# Resume Evidence

Conservative description: Built an auditable, assumption-aware simulation
benchmark for randomized geo incrementality and separate staggered-panel causal
inference, with protected confirmatory evaluation and measured GPU execution.

Resume bullets:

- Engineered a leakage-controlled geo-causal benchmark spanning 1,000-world
  null calibration and a 500-world frozen confirmatory test, with estimand
  contracts, hash-addressed evidence, one-way truth access, and adversarial
  protocol review.
- Qualified official GeoX/JAX CUDA and six R causal packages, implemented an
  AWARE gate/select/abstain policy, and measured decision regret, coverage,
  Type-I error, ablations, public transfer cases, and CPU/GPU scaling.

ATS mapping: causal inference, geo experiments, incrementality, DiD, synthetic
control, JAX, CUDA, XGBoost, Python, R, DuckDB, Parquet, experiment design,
power/MDE, placebo tests, reproducibility, model governance.

60-second explanation: The project asks whether information available before
outcomes can tell us when a geo estimator is trustworthy. I separated randomized
and observational estimands, qualified upstream implementations, calibrated a
known-truth simulator to public anchors, froze a selector and business-loss
protocol, then scored fresh protected worlds. The narrow policy passed its
predeclared gates mostly by occasionally abstaining; it did not learn broad
estimator switching. An adversarial review invalidated and transparently reran
an earlier protocol that leaked truth into a decision threshold.

Three-minute explanation: AWARE first computes chronological prefit, diagnostic,
and placebo features, applies method-specific eligibility, predicts reliability
loss, and either selects or redesigns. Empirical procedure coverage evaluates
the whole selection path. Official GeoX analysis retains design provenance;
independent estimators never inherit official labels. H1 compared clean RMSE to
fixed DiD; H2 used paired stress decision regret with a synthetic cost model.
H1/H2 and all aggregate gates passed, but selection was 96.6% DiD and compound
OOD coverage was poor. This supports a limited decision-policy result, not
universal estimator or production-lift claims.

Limitations: public anchors are examples, economic values are synthetic,
independent high-throughput adapters are approximations, GeoLift was gated,
scenario-specific coverage can fail, and there is no prospective deployment.

Prohibited claims: production deployment, proprietary data, real revenue,
distributed GPU, universal causal validity, or an invented improvement percent.

## Post-Audit Industry Analytics Extensions

- Google Ads Insights & Measurement: built post-audit geo-experiment slicing,
  conditional coverage, tail-risk, MDE/power, seasonality, data-quality, and
  GeoX/GeoLift design-behavior evidence with immutable protocol governance.
- Google GCS Applied ML / Business Data Science: evaluated risk calibration,
  selective prediction, decision frontiers, grouped failure attribution, and a
  truth-isolated compliance DGP for stakeholder-facing measurement decisions.

These are post-audit simulated, derived, and external results—not production
validation or new Protocol 002 confirmation.
