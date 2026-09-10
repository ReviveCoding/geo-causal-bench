#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$project_root/.codex-wsl-env.sh"
cd "$project_root"

python scripts/post_audit_suite.py
python scripts/post_audit_geox_operations.py

export R_LIBS_USER="${GEOCAUSAL_SCRATCH}/geolift-compat/pinned/library:${GEOCAUSAL_SCRATCH}/geolift-compat/pinned/dependencies:${GEOCAUSAL_SCRATCH}/envs/core/lib/R/library"
Rscript scripts/post_audit_geolift_operations.R "$project_root"

python scripts/post_audit_gpu_probe.py
python scripts/finalize_post_audit_suite.py
python scripts/verify_post_audit_suite.py
