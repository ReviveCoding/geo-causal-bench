#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$project_root/.codex-wsl-env.sh"
compatibility_library="${GEOCAUSAL_SCRATCH}/geolift-compat/pinned/library"
dependency_library="${GEOCAUSAL_SCRATCH}/geolift-compat/pinned/dependencies"
core_library="$(Rscript -e 'cat(.libPaths()[1])')"
export R_LIBS_USER="$compatibility_library:$dependency_library:$core_library"

bash "$project_root/scripts/geolift_compat/install_pinned.sh"
Rscript "$project_root/tests/geolift_compatibility/test_upstream_pin.R" \
  "$compatibility_library" \
  "$project_root/evidence/geolift_compatibility/qualification/session_1.json"
Rscript "$project_root/tests/geolift_compatibility/test_upstream_pin.R" \
  "$compatibility_library" \
  "$project_root/evidence/geolift_compatibility/qualification/session_2.json"
Rscript "$project_root/scripts/geolift_compat/compare_fresh_sessions.R" \
  "$project_root/evidence/geolift_compatibility/qualification/session_1.json" \
  "$project_root/evidence/geolift_compatibility/qualification/session_2.json" \
  "$project_root/evidence/geolift_compatibility/qualification/fresh_session_comparison.json"
python "$project_root/scripts/geolift_compat/collect_metadata.py"
python "$project_root/scripts/geolift_compat/write_extension_evidence.py"
