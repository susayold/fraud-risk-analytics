from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .io import REPORT_DIR, ROOT, git_metadata, public_manifest, utc_now, write_csv, write_json


def write_summary(status: str = "INPUT_BLOCKED", pass_count: int = 0, blocked_count: int = 72, fail_count: int = 0) -> dict:
    commit, _ = git_metadata()
    summary = {"block": "F", "part": 8, "name": "Monitoring, Drift & Governance", "status": status, "technical_status": "MONITORING_FRAMEWORK_READY" if fail_count == 0 else "TECHNICAL_REVIEW_REQUIRED", "validation": {"mandatory_gates": 72, "pass": pass_count, "blocked": blocked_count, "fail": fail_count, "status": status, "final_lock_eligible": pass_count == 72 and blocked_count == 0 and fail_count == 0}, "claim_boundary": {"offline_retrospective_monitoring": True, "not_production_monitoring": True, "synthetic_fixture_not_real_evidence": True, "raw_row_level_public_data": False, "label_latency_observed": False}, "two_clock": {"operational": "OPERATIONS_NOW", "matured": "OUTCOMES_MATURED"}, "lifecycle": {"status": status, "final_oot_threshold_tuning": False, "matured_outcomes_available": False}, "generated_at_utc": utc_now(), "source_commit": commit, "validator_version": "PART8_EVIDENCE_VALIDATOR_v1.0"}
    write_json(REPORT_DIR / "PART8_FINAL_SUMMARY.json", summary)
    write_json(ROOT / "assets" / "data" / "part8_summary.json", summary)
    return summary


def reconcile_summary(validation: pd.DataFrame, status: str | None = None) -> dict:
    current = json.loads((REPORT_DIR / "PART8_FINAL_SUMMARY.json").read_text(encoding="utf-8")) if (REPORT_DIR / "PART8_FINAL_SUMMARY.json").exists() else {}
    counts = validation.status.value_counts().to_dict()
    current["validation"] = {"mandatory_gates": 72, "pass": int(counts.get("PASS", 0)), "blocked": int(counts.get("BLOCKED", 0)), "fail": int(counts.get("FAIL", 0)), "status": status or current.get("status", "INPUT_BLOCKED"), "final_lock_eligible": int(counts.get("PASS", 0)) == 72 and int(counts.get("BLOCKED", 0)) == 0 and int(counts.get("FAIL", 0)) == 0}
    current["technical_status"] = "MONITORING_FRAMEWORK_READY" if int(counts.get("FAIL", 0)) == 0 else "TECHNICAL_REVIEW_REQUIRED"
    commit, _ = git_metadata()
    current["source_commit"] = commit
    write_json(REPORT_DIR / "PART8_FINAL_SUMMARY.json", current); write_json(ROOT / "assets" / "data" / "part8_summary.json", current)
    write_json(REPORT_DIR / "P8_PUBLIC_EVIDENCE_RECONCILIATION.json", {"source_commit": commit, "validation": current["validation"], "status": "PASS" if int(counts.get("FAIL", 0)) == 0 else "FAIL", "public_row_level_data": False})
    return current

