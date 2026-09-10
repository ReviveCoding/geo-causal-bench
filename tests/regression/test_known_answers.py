from __future__ import annotations

import json
from pathlib import Path


def test_maintained_package_qualification_preserves_all_methods():
    evidence = json.loads(Path("evidence/package_qualification.json").read_text())
    statuses = {item["method_id"]: item["status"] for item in evidence["results"]}
    assert len(statuses) == 6
    assert statuses["synthdid_prop99"] == "PASS"
    assert statuses["did_mpdta_dynamic_att"] == "PASS"
    assert statuses["causalimpact_official_toy"] == "PASS"
    assert statuses["geolift_official_example"] == "GATED"


def test_official_geox_qualification_retains_design():
    evidence = json.loads(Path("evidence/geox_qualification.json").read_text())
    assert evidence["status"] == "PASS"
    assert evidence["official_design_artifact_retained"] is True
    assert (
        evidence["analysis_result"]["results"]["cell_1"]["cumulative_lift"]["rows"]
        == 30
    )
