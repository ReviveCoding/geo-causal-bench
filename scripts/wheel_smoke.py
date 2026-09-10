"""Verify an installed wheel without importing from the repository source tree."""

from importlib.metadata import version

import geocausal
from geocausal.cli import app


def main() -> None:
    assert version("geo-causal-bench") == "0.1.0"
    assert geocausal.__version__ == "0.1.0"
    assert app.registered_commands is not None
    print("installed wheel smoke: geo-causal-bench 0.1.0")


if __name__ == "__main__":
    main()
