# GeoLift Compatibility Extension Review

Extension: `GEOLIFT-COMPAT-001`

Status: **PASS WITH LIMITATION / UPSTREAM_PINNED**

The review verified the public issue reproduction, full active call stack,
package/source identities, object shapes, authoritative call semantics, two
bisect attempts, direct last-good test, one-/two-/three-location qualification,
manual observed and synthetic aggregation, treatment-order invariance,
time-indexed inference dimensions, and fresh-session reproducibility.

No source patch was made. The solution is an isolated commit pin to unmodified
augsynth `65c5a6f34f4e4a8b1011182fe12309ef022d992f` with unmodified GeoLift
`db34ea4299ff0e28515ebac502b78c076c93c905`. Both compatible and incompatible
augsynth sources identify as version 0.2.0, so a version-only lock is rejected.

The top-level aggregate GeoLift confidence bounds are NA; only its 105-row
time-indexed conformal inference shape was qualified. This prevents an
aggregate-CI claim but does not invalidate the tested point and aggregation
semantics.

The protected-scope verifier confirms that `artifacts/freeze`,
`evidence/final`, `evidence/e20_audit.json`, and `evidence/receipts` are the
same Git objects as audited commit `4e16163` and have no working-tree changes.
Protocol 002 remains untouched and its historical GeoLift gate is not revised.
