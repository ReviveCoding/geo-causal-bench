# Meridian GeoX Capability Notes

Audit target: official PyPI `meridian-geox==1.0.1`, module version 1.0.1,
installed in the isolated WSL Python 3.11 environment. Official repo main was
resolved to `0a1dd0f730ab8170e4e46646f3bf69400d57d021` on 2026-09-09;
the installed wheel/source identity will be hashed in E00/E05 evidence.

## Executable findings

- Public experiment types: HOLDBACK, GO_DARK, HEAVY_UP.
- Assignment rules: RANDOM and STRATIFIED_SAMPLING.
- Public methodology enum: TBR and SDID.
- Actual design implementation: only TBR. `design.py` dispatches TBR for R2 and
  MDE and otherwise raises `ValueError("Unsupported methodology")`.
- Actual analysis implementation: only TBR. `analysis.py::_prepare_design_config`
  rejects non-TBR with `Only TBR is supported.`
- Consequently, enum presence does not establish SDID capability. Independent
  SDID results will never be called official GeoX results.
- `Design` retains per-cell assignments, controls/exclusions, config,
  constraints, quality result, strata, and original data and supports JSON
  export/load. Official analysis must receive this provenance.
- `AnalysisConfig` binds design, dates, optional pretest end, excluded dates,
  alpha/test type, and placebo candidate/retention thresholds.
- `AnalysisResult` returns per-cell lift, percent lift, cumulative lift,
  counterfactual series, pointwise differences, optional iCPD, descriptive
  metrics, exclusions, configuration, and quality result.

## Validation and inference

Official docs distinguish fatal schema/consistency validation from nonfatal,
structured quality warnings. Analysis requires exact design geo consistency,
at least three experiment durations of pretest, and nonoverlapping pretest/test.
Duplicate keys are aggregated with warning. Hard-coded quality thresholds must
not be silently bypassed.

Official design-aware placebo inference recreates the design algorithm/support
and tests a sharp null. Generic iid regression p-values and unrestricted label
shuffles are not equivalent. Independent methods report native uncertainty and,
only where a defensible exact mechanism is implemented, a separate design-aware
result.

## GPU status

JAX 0.10.2/jaxlib 0.10.2 selected exactly one `cuda:0` device under WSL. A
synchronized 6144-square float32 JIT matrix workload used approximately 3.5 GiB
GPU memory and took 0.0304 seconds after compilation. This qualifies the actual
backend for heavy GPU-capable work; E19 will measure speedups rather than assume
them.

Sources: [official API](https://developers.google.com/meridian/geox/api-reference),
[analysis workflow](https://developers.google.com/meridian/geox/prepare-your-analysis-data),
[validation](https://developers.google.com/meridian/geox/data-validation-and-quality-checks),
[inference](https://developers.google.com/meridian/geox/robust-inference), and
[source](https://github.com/google/meridian-geox).
