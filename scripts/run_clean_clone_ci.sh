#!/usr/bin/env bash
set -euo pipefail

source_root="$(git rev-parse --show-toplevel)"
source "$source_root/.codex-wsl-env.sh"
clean_parent="$GEOCAUSAL_SCRATCH/publication-clean-clones"
mkdir -p "$clean_parent"
clean_root="$(mktemp -d "$clean_parent/run-XXXXXX")"
clone_root="$clean_root/repo"
log_path="$source_root/evidence/clean_clone_ci.log"

{
  echo "source_head=$(git -C "$source_root" rev-parse HEAD)"
  echo "clean_root=$clean_root"
  git clone --no-local "$source_root" "$clone_root"
  cd "$clone_root"
  test -z "$(git status --porcelain=v1)"
  test ! -e .venv

  uv sync --locked --python 3.11 --extra dev
  uv run ruff format --check src tests scripts
  uv run ruff check src tests scripts
  uv run mypy src
  uv run coverage erase
  PYTHONHASHSEED=0 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
    uv run coverage run --branch -m pytest -q
  uv run coverage report --fail-under=80 --show-missing
  uv run python -m build

  uv export --quiet --locked --no-dev --no-emit-project \
    --output-file build/runtime-requirements.txt
  uv venv --python 3.11 .wheel-smoke
  uv pip sync --python .wheel-smoke/bin/python build/runtime-requirements.txt
  uv pip install --python .wheel-smoke/bin/python --no-deps dist/*.whl
  smoke_dir="$(mktemp -d "$clean_root/smoke-XXXXXX")"
  cd "$smoke_dir"
  "$clone_root/.wheel-smoke/bin/python" "$clone_root/scripts/wheel_smoke.py"
  "$clone_root/.wheel-smoke/bin/geocausal" --help
  cd "$clone_root"

  uv run python scripts/verify_evidence.py --read-only
  uv run python scripts/verify_post_audit_suite.py
  Rscript scripts/verify_r_integrity.R
  test -z "$(git status --porcelain=v1)"
  git fsck --full
  git diff --check
  echo "CLEAN_CLONE_CI=PASS"
} 2>&1 | tee "$log_path"
