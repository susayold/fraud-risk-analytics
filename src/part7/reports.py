from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .io import REPORT_DIR, public_manifest, utc_now, write_csv, write_json


def write_summary(status: str, score_version: str = "", policy_version: str = "", profile: str = "", policy: dict | None = None, evidence: dict | None = None, gates_pass: int = 0, gates_fail: int = 0, score_status: str | None = None) -> None:
    summary = {"block": "E", "part": 7, "name": "Fraud Risk Decision Engine", "status": status, "score_version": score_version, "score_status": score_status, "policy_version": policy_version, "policy_profile": profile, "claim_boundary": {"synthetic_data": True, "simulated_costs": True, "not_production_deployment": True, "oot_not_globally_unseen": True}, "policy": policy or {"review_threshold": None, "block_threshold": None, "review_capacity": None}, "final_evidence": evidence or {"allow_rate": None, "review_rate": None, "block_rate": None, "fraud_capture": None, "fraud_exposure_capture": None, "legitimate_block_rate": None, "simulated_total_cost": None}, "validation": {"mandatory_gates": 64, "pass": gates_pass, "fail": gates_fail, "status": "PASS" if gates_fail == 0 and gates_pass == 64 else "REVIEW"}, "generated_at_utc": utc_now()}
    write_json(REPORT_DIR / "PART7_FINAL_SUMMARY.json", summary)
    write_json(Path(__file__).resolve().parents[2] / "assets" / "data" / "part7_summary.json", summary)


def write_input_audit(status: str, notes: str, checks: list[dict]) -> None:
    write_json(REPORT_DIR / "part7_input_audit.json", {"status": status, "notes": notes, "checks": checks, "generated_at_utc": utc_now()})
    write_csv(REPORT_DIR / "decision_input_reconciliation.csv", pd.DataFrame(checks))
