# Meridian GeoX Capability Audit

Evidence class: **MEASURED**. Resolved package: `meridian-geox==1.0.1`, installed
from the release associated with Google repository commit
`0a1dd0f730ab8170e4e46646f3bf69400d57d021`. Full public signatures are in
`evidence/geox_capabilities.json`; official execution evidence is in
`evidence/geox_qualification.json`.

The public methodology enum exposes TBR and SDID. Executable source inspection
and behavior are narrower: current design scoring and analysis reject non-TBR
methodology, and analysis raises an explicit “Only TBR is supported” error.
Consequently this protocol calls only the official time-based-regression path
“GeoX analysis.” Independent SCM, SDID, and ASCM estimators retain independent
labels.

The bundled serialized stratified-sampling holdback design was loaded with
`Design.load_from_json` and retained as analysis provenance. Official analysis
on the bundled single-cell dataset completed on the 2020-04-01 through
2020-04-30 window in 20.59 seconds, returning 30 cumulative-lift rows and the
official pointwise/cumulative lift, iCPD, counterfactual, and descriptive result
tables. The design recorded MDE 0.0131405, budget 7085.92, 27 treatment geos,
and excluded geo 105. Quality checks returned no structured metric warnings for
the supplied example and no hard validations were disabled.

The official random-versus-stratified TBR comparison completed in 22.68 seconds
and returned ten ranked designs. It emitted warnings that Sobol balance is best
when sample count is a power of two and that holdback cells lacked budgets in
the unconstrained comparison. These warnings are preserved. The ranked frontier
includes R2, A/A p-value, relative and absolute MDE, projected budget, response
share, and treatment-geo count. High R2 is treated as fit evidence, not proof of
causal validity.

GeoX inference is reported as the official package procedure for its preserved
design. Conventional independent-estimator intervals are never described as
equivalent to GeoX design-aware/randomization-aware inference.
