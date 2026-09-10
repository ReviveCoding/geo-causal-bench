# GeoLift Compatibility Investigation

Extension: `GEOLIFT-COMPAT-001`

Evidence class: **UPSTREAM_PINNED**

Disposition: **QUALIFIED WITH LIMITATION**

This is a separately governed post-audit external-validation extension. It did
not modify, rerun, overwrite, or reinterpret AWARE-GEO protocol 002, E14, E20,
or their receipts. The original frozen study's GeoLift status remains GATED.

## Finding

Unmodified GeoLift 2.7.5 at commit
[`db34ea4`](https://github.com/facebookincubator/GeoLift/commit/db34ea4299ff0e28515ebac502b78c076c93c905)
works with unmodified augsynth 0.2.0 at commit
[`65c5a6f`](https://github.com/ebenmichael/augsynth/commit/65c5a6f34f4e4a8b1011182fe12309ef022d992f).
No local patch is required. Because both compatible and incompatible augsynth
revisions report version 0.2.0, the full commit pin—not the version string—is
the compatibility contract.

## Exact baseline reproduction

The installed baseline was GeoLift commit `db34ea4` plus augsynth commit
`7e70072`. The official Chicago/Portland call reproduced public
[issue #118](https://github.com/ebenmichael/augsynth/issues/118) exactly:

```text
Tibble columns must have compatible sizes.
Size 105: Existing data.
Size 210: Column `Yobs`.
```

The captured active stack is `GeoLift::GeoLift -> summary ->
summary.augsynth -> treated_table -> tibble`. Input data has 40 locations and
105 times. At `treated_table`, `X` is 40×90, post-treatment `y` is 40×15, and
there are two treated rows. Flattening that 2×105 matrix produces 210 values,
whereas time, synthetic prediction, donor average, and the treated-location
mean each have length 105. The complete traceback, `sessionInfo()`, installed
package commits and paths, DESCRIPTION hashes, input hashes, and shapes are in
`evidence/geolift_compatibility/baseline/complete_traceback.log`.

## Statistical semantics and root cause

The authoritative `predict.augsynth()` implementation calculates the observed
treated series as `colMeans(comb[trt == 1, ])`. Thus, with simultaneous treated
locations, its inferential series is the average treated outcome minus one
average synthetic counterfactual at each time. GeoLift reports average ATT/lift
on that scale and converts to total incremental outcome as:

```text
sum(all treated observed outcomes)
  - treated-location count × sum(average synthetic counterfactual)
```

The new `treated_table()` introduced a contradictory representation:
`as.numeric(t(df[trt_index, ]))` flattens every treated-location observation
instead of calculating the treated-location mean. Replacing 210 by 105 through
truncation or recycling would be statistically wrong. The semantically coherent
operation would be a treated-row mean, but an upstream pin makes a local patch
unnecessary for this extension.

Authoritative source excerpts and SHA-256 hashes are recorded in
`evidence/geolift_compatibility/source/source_analysis.json`.

## History and bisect

The first bisect attempt was inconclusive because older revisions require
LiblineaR, which current head removed; skipped commits and install failures are
preserved. LiblineaR 2.10-24 was then installed only in extension scratch from
a source archive with SHA-256
`3949a566f36e0c7578b9aa3584873b52c1b2058cdd7a1f7c87d5073f57f027c8`.

The completed bisect used successful execution of the unchanged official
two-location call as its criterion. It found
[`bdc0b80`](https://github.com/ebenmichael/augsynth/commit/bdc0b808103ffa7cf63ba0661f1ee2adb10eba3c),
the May 20, 2026 summary/plotting overhaul, as the first incompatible commit.
Its parent `65c5a6f` is the last-good candidate and also passed a direct test.
Some intermediate revisions fail earlier in the new placebo path rather than
at the final 210/105 tibble construction; they are still incompatible with the
unchanged GeoLift call.

## Qualification

All cases use the official `GeoLift_Test` panel, times 1–105, treatment times
91–105, and seed 20260909.

| Case | Locations | Average ATT | Percent lift | Total incremental | `Yobs` length | ATT/inference rows |
|---|---|---:|---:|---:|---:|---:|
| Single | Chicago | -209.004246 | -7.3% | -3135.063695 | 105 | 105 |
| Official two | Chicago, Portland | 155.555928 | 5.4% | 4666.677831 | 210 | 105 |
| Three | Chicago, Portland, Atlanta | 125.109612 | 3.8% | 5629.932525 | 315 | 105 |
| Reordered two | Portland, Chicago | 155.555928 | 5.4% | 4666.677831 | 210 | 105 |

The longer `Yobs` vector is GeoLift's unit-by-time storage, not the inferred
time series. Reshaping it to treated units × time and averaging columns exactly
matches the explicit source-data calculation. For every case, the synthetic
series equals `predict(..., att=FALSE)`, ATT equals treated mean minus synthetic
mean, and total incremental effect equals the explicit manual total. Forward
and reversed two-location calls match exactly for point series, aggregate
effect, p-value, and all time-indexed inference fields.

Two wholly new R sessions produced identical canonical outputs. The official
two-location result agrees with the documented rounded value 4667 within the
predeclared tolerance.

## Inference limitation

The pinned object provides 105 time-indexed estimates, conformal lower/upper
bounds, and p-values in `summary$att`, satisfying the required time dimension.
However, GeoLift's separate top-level aggregate `lower_bound` and `upper_bound`
fields are NA in this dependency constellation. Therefore this qualification
supports execution, point aggregation, per-time inference shape, and ordering
invariance; it does not qualify a top-level aggregate confidence interval.

## Installation and reproduction

The overlay installs into WSL scratch and never changes the audited project R
library or an installed upstream package in place:

```bash
cd /mnt/c/Users/bjw-0/Downloads/geo-causal-bench
source .codex-wsl-env.sh
bash scripts/geolift_compat/run_all.sh
```

The exact lock is `configs/geolift_compatibility.lock.json`. Package source,
the hashed LiblineaR archive, candidate libraries, and clones live under
`$GEOCAUSAL_SCRATCH/geolift-compat`; only tests, summaries, hashes, and logs are
committed.

## Governance conclusion

Use the `UPSTREAM_PINNED` label for this exact overlay. Do not call it current
upstream head, do not relabel it as a local patch, and do not retroactively add
it to protocol 002. Future use should either retain the full commit pin or wait
for an upstream fix that independently passes this regression suite.
