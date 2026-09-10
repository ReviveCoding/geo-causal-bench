"""Execute pinned public-source acquisition from the repository root."""

import shutil
from pathlib import Path

from geocausal.acquisition import acquire_public_sources

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    resolved_rscript = shutil.which("Rscript")
    if resolved_rscript is None:
        raise RuntimeError("Rscript is required for the R-backed public sources")
    rscript = Path(resolved_rscript)
    for manifest in acquire_public_sources(root, rscript=rscript):
        print(manifest)
