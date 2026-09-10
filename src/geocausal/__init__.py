"""Geo-Causal Measurement & Econometrics Benchmark."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("geo-causal-bench")
except PackageNotFoundError:
    __version__ = "0+uninstalled"

__all__ = ["__version__"]
