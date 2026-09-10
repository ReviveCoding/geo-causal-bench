# GitHub Publication Audit

Audit identity: `GITHUB-PUBLICATION-001`  
Audit timestamp: `2026-09-10T16:19:28.5811170Z`

## Publication state

- Repository: <https://github.com/ReviveCoding/geo-causal-bench>
- Visibility: **PUBLIC**
- Default and only branch: `main`
- Publication-audit commit: `8a641b18479ef2a37d933c4c59610bcb61d344e2`
- Local and remote `main` matched at audit generation.
- No force push, secret bypass, Git LFS migration, Pages deployment, or
  unexpected branch occurred.

The README, CI badge, MIT project license, source tree, Actions run, and ten
accurate repository topics were inspected through GitHub. Public visibility
does not relicense the separately identified third-party data or dependencies.

## CI result

Workflow `CI` at `.github/workflows/ci.yml` uses `contents: read`, has no
`pull_request_target`, and pins every third-party action to a full commit SHA.
It installs the CPU environment from `uv.lock` under Python 3.11 and does not
run CUDA, protected simulation, heavy Monte Carlo, or the external R stack.

Run [34501118043](https://github.com/ReviveCoding/geo-causal-bench/actions/runs/34501118043)
completed successfully for exact SHA `8a641b18479ef2a37d933c4c59610bcb61d344e2`:

- Evidence and claim contracts: **SUCCESS** (`102951856071`)
- Python quality, tests, and package: **SUCCESS** (`102951855499`)
- R syntax and compatibility-pin integrity: **SUCCESS** (`102951856137`)

The Python job passed Ruff, strict mypy, 53 pytest tests, 95% branch coverage,
sdist/wheel build, and a wheel/CLI smoke test outside the source tree. The R job
parsed 13 scripts and checked the exact GeoLift/augsynth commits.

The preceding run `34499991813` failed because the persisted DuckDB views
contained the original WSL path. This was classified as a clean-clone
hermeticity defect. Claim verification now creates an in-memory read-only view
from clone-local immutable Parquet, with a regression test. No claim query,
expected value, or scientific evidence changed.

## Security, size, and licensing

The final pre-push scan covered every reachable Git object, found no
high-confidence secret or credential-like tracked filename, and did not bypass
GitHub push protection. The largest reachable blob was 438,843 bytes
(`evidence/qualification/initial/fact_null_result.parquet`), well below
GitHub's 100 MB enforcement threshold. No raw/staged/curated/external row data,
downloaded package source, environment, cache, or archive is tracked.

Historical execution paths remain only where required for provenance. Mutable
general reproduction instructions use portable paths; audited GeoLift and
Protocol 002 history was not rewritten.

## Scientific identities

- Protocol 002 freeze, final evidence, E20 audit, receipts, and invalidated
  archive match audited commit `4e161634557ea76852f3ca70340898bb5acf8394`.
- `GEOLIFT-COMPAT-001` object remains
  `69a24885dce989ce403fc355546761d76e09291f`.
- `POST-AUDIT-SUITE-001` audit object remains
  `0ba561c138bcd5b4b2ca1f445bd0f18d8cb685e3` and status `PASS`.
- Published annotated tags:
  `aware-geo-freeze-c0b13ec88b725728` and
  `aware-geo-freeze-e52a8660a97ef174`.

This terminal update is introduced by a metadata-only closure commit. That
containing commit must itself pass the same remote CI workflow; the external
result is verified after push without another file mutation.
