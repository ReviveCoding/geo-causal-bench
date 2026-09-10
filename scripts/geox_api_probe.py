"""Record the installed Meridian GeoX public API and key enum capabilities."""

from __future__ import annotations

import dataclasses
import inspect
import json
import sys
from enum import Enum
from importlib import metadata
from pathlib import Path
from typing import Any

import meridian_geox as geox


def describe(name: str, value: Any) -> dict[str, Any]:
    result: dict[str, Any] = {"name": name, "type": type(value).__name__}
    if inspect.isclass(value):
        try:
            result["signature"] = str(inspect.signature(value))
        except (TypeError, ValueError):
            pass
        if issubclass(value, Enum):
            result["enum_values"] = {member.name: member.value for member in value}
        if dataclasses.is_dataclass(value):
            result["fields"] = [field.name for field in dataclasses.fields(value)]
    elif callable(value):
        try:
            result["signature"] = str(inspect.signature(value))
        except (TypeError, ValueError):
            pass
    return result


def main() -> None:
    public_names = sorted(name for name in dir(geox) if not name.startswith("_"))
    payload = {
        "package": "meridian-geox",
        "version": metadata.version("meridian-geox"),
        "module_version": getattr(geox, "__version__", None),
        "module_file": str(Path(inspect.getfile(geox)).resolve()),
        "public_api": [describe(name, getattr(geox, name)) for name in public_names],
    }
    rendered = json.dumps(payload, indent=2, sort_keys=True, default=str)
    if len(sys.argv) > 1:
        output = Path(sys.argv[1])
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
