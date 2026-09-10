#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$project_root/.codex-wsl-env.sh"

extension_root="${GEOCAUSAL_SCRATCH}/geolift-compat/pinned"
source_root="$extension_root/source"
library_root="$extension_root/library"
archive_root="$extension_root/archives"
dependency_library="$extension_root/dependencies"
core_library="$(Rscript -e 'cat(.libPaths()[1])')"

augsynth_commit="65c5a6f34f4e4a8b1011182fe12309ef022d992f"
geolift_commit="db34ea4299ff0e28515ebac502b78c076c93c905"
liblinear_archive="$archive_root/LiblineaR_2.10-24.tar.gz"
liblinear_sha256="3949a566f36e0c7578b9aa3584873b52c1b2058cdd7a1f7c87d5073f57f027c8"

mkdir -p "$source_root" "$library_root" "$archive_root" "$dependency_library"

if [[ ! -d "$source_root/augsynth/.git" ]]; then
  git clone https://github.com/ebenmichael/augsynth.git "$source_root/augsynth"
fi
if [[ ! -d "$source_root/GeoLift/.git" ]]; then
  git clone https://github.com/facebookincubator/GeoLift.git "$source_root/GeoLift"
fi

git -C "$source_root/augsynth" fetch origin "$augsynth_commit"
git -C "$source_root/augsynth" checkout --detach "$augsynth_commit"
git -C "$source_root/GeoLift" fetch origin "$geolift_commit"
git -C "$source_root/GeoLift" checkout --detach "$geolift_commit"

test "$(git -C "$source_root/augsynth" rev-parse HEAD)" = "$augsynth_commit"
test "$(git -C "$source_root/GeoLift" rev-parse HEAD)" = "$geolift_commit"

if [[ ! -f "$liblinear_archive" ]]; then
  curl -fsSL \
    https://cloud.r-project.org/src/contrib/LiblineaR_2.10-24.tar.gz \
    -o "$liblinear_archive"
fi
echo "$liblinear_sha256  $liblinear_archive" | sha256sum --check

if [[ ! -f "$dependency_library/LiblineaR/DESCRIPTION" ]]; then
  R_LIBS_USER="$dependency_library:$core_library" R CMD INSTALL \
    --no-multiarch --library="$dependency_library" "$liblinear_archive"
fi

R_LIBS_USER="$library_root:$dependency_library:$core_library" R CMD INSTALL \
  --no-multiarch --library="$library_root" "$source_root/augsynth"
R_LIBS_USER="$library_root:$dependency_library:$core_library" R CMD INSTALL \
  --no-multiarch --library="$library_root" "$source_root/GeoLift"

R_LIBS_USER="$library_root:$dependency_library:$core_library" Rscript -e \
  'stopifnot(packageVersion("GeoLift") == "2.7.5", packageVersion("augsynth") == "0.2.0"); cat(find.package("GeoLift"), "\n", find.package("augsynth"), "\n")'

echo "Installed UPSTREAM_PINNED compatibility overlay at $library_root"
