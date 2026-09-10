"""Print executable GeoX notebook cells relevant to design and analysis."""

from __future__ import annotations

import inspect
import json
from pathlib import Path

import meridian_geox

package_root = Path(inspect.getfile(meridian_geox)).resolve().parent
notebook = package_root / "colab" / "meridian_geox_single_cell_colab.ipynb"
payload = json.loads(notebook.read_text(encoding="utf-8"))
needles = (
    "DesignConfig",
    "run_design",
    "AnalysisConfig",
    "run_analysis",
    "design_path",
    "example_design_stratified",
    "single_cell_design_data",
    "single_cell_analysis_data",
    "load_design",
    "DataQualityCheckConfig",
)
for index, cell in enumerate(payload["cells"]):
    source = "".join(cell.get("source", []))
    if cell.get("cell_type") == "code" and (
        any(needle in source for needle in needles) or 37 <= index <= 40
    ):
        print(f"--- CELL {index} ---")
        print(source)
        if index in {14, 41, 53}:
            print("--- OUTPUTS ---")
            print(json.dumps(cell.get("outputs", []), indent=2)[:20000])
