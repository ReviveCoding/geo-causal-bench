"""Run historical evidence and claim verification."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from geocausal.artifacts import atomic_write_json
from geocausal.governance import verify_claims, verify_evidence

root = Path(__file__).resolve().parents[1]
payload = {"evidence": verify_evidence(root), "claims": verify_claims(root)}
payload["all_pass"] = payload["evidence"]["all_pass"] and payload["claims"]["all_pass"]
if "--read-only" not in sys.argv:
    atomic_write_json(root / "evidence" / "e20_audit.json", payload)
print(json.dumps(payload, indent=2, sort_keys=True))
if not payload["all_pass"]:
    raise SystemExit(1)
