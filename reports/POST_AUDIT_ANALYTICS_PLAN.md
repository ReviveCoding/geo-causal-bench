# Post-Audit Analytics Plan

Plan identity: `POST-AUDIT-ANALYTICS-001-PLAN-v1`  
Evidence: `POST_AUDIT_EXPLORATORY / POST_AUDIT_DERIVED`  
Confirmatory status: **none**

This plan and `configs/post_audit_analytics/slice_registry.yaml` were written
before any outcome-dependent slice query. Protocol 002 is an immutable
historical input. These analyses can characterize its completed evidence but
cannot retune it, revise its decision, or create retrospective confirmatory
claims.

The registered one-way slices cover pre-fit, residual dependence, trend gap,
donor support, leverage, baseline volume, missingness, predicted risk, and
scenario. The eight registered interactions are exactly those in the registry.
Historical effect-relative-to-MDE slicing is prohibited unless a legitimate
world-specific design MDE already exists; the slice is otherwise reserved for
new `OPERATIONS-STUDY-001` evidence.

Ordinary descriptive slices require `n >= 25`; `n < 30` is labeled
`LOW_PRECISION`. Proportions use Wilson 95% intervals. Headline continuous
contrasts use 2,000 world-cluster bootstrap resamples with fixed seed
`2026091001`. Any computed exploratory p-values belong to one declared family
and use BH-FDR. Effect sizes and intervals remain primary.

Catastrophic loss is predeclared as normalized decision regret at least 1.0,
one full normalized loss unit. Tail metrics include median, P75, P90, P95, P99,
maximum, CVaR90, and CVaR95. Risk-ranking comparators and retained-volume grids
are frozen in the machine-readable plan. The original risk threshold 1.25 is
marked but unchanged; the threshold sweep is post-hoc policy sensitivity only.

Unavailable fields are reported as `NOT_AVAILABLE` rather than reconstructed
from outcomes. Bad, null, sparse, and contradictory slices are retained.
