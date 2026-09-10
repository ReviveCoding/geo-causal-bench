#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_dir"
source .codex-wsl-env.sh

printf 'distro=%s\n' "$(. /etc/os-release && printf '%s' "$PRETTY_NAME")"
printf 'kernel=%s\n' "$(uname -r)"
printf 'arch=%s\n' "$(uname -m)"
printf 'python=%s\n' "$(python3 --version 2>&1)"
printf 'r=%s\n' "$(R --version 2>/dev/null | head -n 1 || true)"
printf 'rscript=%s\n' "$(Rscript --version 2>&1 || true)"
printf 'git=%s\n' "$(git --version)"
printf 'uv=%s\n' "$(uv --version 2>&1 || true)"
printf 'cpu_logical=%s\n' "$(nproc)"
printf 'mem_total_kib=%s\n' "$(awk '/^MemTotal:/ {print $2}' /proc/meminfo)"
printf 'disk_free_kib=%s\n' "$(df -k /mnt/c | awk 'NR==2 {print $4}')"
printf 'nvidia_smi=%s\n' "$(command -v nvidia-smi || true)"
nvidia-smi \
  --query-gpu=name,driver_version,memory.total,memory.free,utilization.gpu \
  --format=csv,noheader

python3 - <<'PY'
import importlib.util

for name in ("jax", "jaxlib", "xgboost", "meridian_geox"):
    print(f"module_{name}={importlib.util.find_spec(name) is not None}")
PY
