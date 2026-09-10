# E13 Scientific Freeze Review

Status: **COMPLETE**. Protocol `AWARE-GEO-c0b13ec88b725728`; freeze-manifest
SHA-256 `967a425d22b68d954405be102a6cecc57db95267027da7dd853d479731810330`.

The manifest binds source commit `5ff8225`, its Git tree, Python/R locks, GeoX
1.0.1 and R package versions, eight dataset manifests, DGP code, selector model
and diagnostic schema, gates, abstention threshold, business costs, H1/H2,
multiplicity, scenario mixture, 500 protected world identities and seed-set
hash, scoring code, and report/claim schemas. Raw protected seeds are not exposed
to selector code. Verification rehashed the manifest successfully.

The only legal next transition is process-separated E14: generate observed and
truth stores, estimate and commit through an interface with no truth path, then
open truth once in canonical scoring.
