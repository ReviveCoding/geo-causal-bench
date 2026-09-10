# Repository Operating Instructions

This repository is governed by `EXECUTION_PLAN.md`. Read it together with
`_preflight/RUN_CONTEXT.md` and `.codex-wsl-env.sh` before changing code or
running scientific workloads.

## Execution discipline

- Keep `EXECUTION_PLAN.md` current with repository reality. Update Progress,
  Surprises & Discoveries, Decision Log, and Outcomes at every material phase
  transition, failure, or interruption.
- Treat E00--E20 as mandatory. E21 is optional and cannot block completion.
- Use WSL2 Ubuntu as the primary GeoX/JAX scientific runtime and source
  `.codex-wsl-env.sh` first. Use one GPU queue and never claim multi-GPU work.
- Keep randomized Track A and observational Track B estimands, evidence, and
  result families separate.
- Enforce the pre-treatment and hidden-truth boundaries in code, schemas,
  receipts, tests, and review evidence.
- Preserve failures, warnings, exclusions, null results, and negative compute
  results. Never silently remove failed methods from denominators.
- Do not inspect protected E14 outcomes until the E13 freeze is committed,
  tagged, hashed, and verified. E14 truth access is one-way and logged.
- Do not change frozen scientific semantics under the same protocol identity.
- Make local milestone commits and annotated scientific tags. Never push or
  create a public remote without explicit authorization.

## Engineering discipline

- Use an installable `src/geocausal` Python package, typed validated configs,
  deterministic seeds, atomic writes, hashes, durable receipts, and resumable
  commands.
- Canonical numeric scientific evidence is Parquet and is queried with DuckDB.
- Run Ruff, mypy, pytest, build, wheel-smoke, evidence verification, and claim
  verification in proportion to each phase and in full at E20.
- Hosted CI must remain CPU-safe. Heavy JAX/GeoX work belongs in WSL locally.
- Keep raw data out of Git unless redistribution is clearly permitted and
  useful; commit acquisition instructions and manifests instead.

## Plan standard

`.agent/PLANS.md` defines the required living-plan convention. A future agent
must be able to resume using only this repository, `AGENTS.md`,
`EXECUTION_PLAN.md`, and immutable evidence already recorded.
