# Publication Safety Audit

Audit identity: `GITHUB-PUBLICATION-SAFETY-001`.

The initial scan covered every reachable Git object and the current tracked
tree. It found no high-confidence GitHub, OpenAI, AWS, bearer-token, or private
key material and no tracked credential-like filenames. Scanner output records
only paths and secret categories, never matched values. Literal prefix mentions
were inspected as non-secret scientific/text or binary coincidences.

The repository contains 4.45 MiB of unpacked Git objects before publication.
The largest reachable blob is 438,843 bytes
(`evidence/qualification/initial/fact_null_result.parquet`), below GitHub's
100 MB enforcement threshold. No Git LFS migration or history rewrite is
needed.

No row-level files under `data/raw`, `data/staged`, `data/curated`, or
`data/external` are tracked. Downloaded GeoLift/augsynth source trees, Python/R
environments, JAX caches, archives, and temporary Monte Carlo worlds are also
absent. Data manifests retain the upstream MIT, GPL-3, and Apache-2.0 source
identities. The project already declared MIT in `pyproject.toml`; `LICENSE`
merely supplies the matching license text and does not relicense third-party
inputs or dependencies.

Machine-specific paths in protected/historical logs and host preflight evidence
are retained as provenance. Mutable README/reproduction instructions and active
helper scripts use portable repository and cache discovery, avoiding additional
local-identity disclosure.

Status: **PASS**, subject to a final scan of the committed publication tree
before push and a post-push GitHub inspection.
