"""Execute pinned public-source acquisition from the repository root."""

from pathlib import Path

from geocausal.acquisition import acquire_public_sources

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    rscript = Path("/home/bjw-0/.cache/geo-causal-bench/envs/core/bin/Rscript")
    for manifest in acquire_public_sources(root, rscript=rscript):
        print(manifest)
