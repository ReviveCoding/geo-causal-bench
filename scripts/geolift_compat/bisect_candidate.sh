#!/usr/bin/env bash
set -u

repo="${1:?usage: bisect_candidate.sh AUGSYNTH_REPO}"
project="/mnt/c/Users/bjw-0/Downloads/geo-causal-bench"
scratch="/home/bjw-0/.cache/geo-causal-bench/geolift-compat"
commit="$(git -C "$repo" rev-parse HEAD)"
candidate_lib="$scratch/candidate-libs/$commit"
dependency_lib="$scratch/dependencies"
core_lib="$(Rscript -e 'cat(.libPaths()[1])')"
mkdir -p "$candidate_lib" "$dependency_lib"

if [[ ! -f "$candidate_lib/augsynth/DESCRIPTION" ]]; then
  if ! R_LIBS_USER="$candidate_lib:$dependency_lib:$core_lib" R CMD INSTALL \
      --no-multiarch --no-test-load --library="$candidate_lib" "$repo"; then
    echo "CANDIDATE_SKIP install failure $commit" >&2
    exit 125
  fi
fi

R_LIBS_USER="$candidate_lib:$dependency_lib:$core_lib" Rscript \
  "$project/scripts/geolift_compat/candidate_smoke.R" "$candidate_lib"
