from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .io import REPORT_DIR, ROOT, git_metadata, public_manifest, utc_now, write_csv, write_json


def write_summary(status: str, score_version: str = "", policy_version: str = "", profile: str = "", policy: dict | None = None, evidence: dict | None = None, gates_pass: int = 0, gates_fail: int = 0, score_status: str | None = None) -> None:
    summary = {"block": "E", "part": 7, "name": "Fraud Risk Decision Engine", "status": status, "score_version": score_version, "score_status": score_status, "policy_version": policy_version, "policy_profile": profile, "claim_boundary": {"synthetic_data": True, "simulated_costs": True, "not_production_deployment": True, "oot_not_globally_unseen": True}, "policy": policy or {"review_threshold": None, "block_threshold": None, "review_capacity": None}, "final_evidence": evidence or {"allow_rate": None, "review_rate": None, "block_rate": None, "fraud_capture": None, "fraud_exposure_capture": None, "legitimate_block_rate": None, "simulated_total_cost": None}, "validation": {"mandatory_gates": 64, "pass": gates_pass, "fail": gates_fail, "status": "PASS" if gates_fail == 0 and gates_pass == 64 else "REVIEW"}, "generated_at_utc": utc_now()}
    write_json(REPORT_DIR / "PART7_FINAL_SUMMARY.json", summary)
    write_json(Path(__file__).resolve().parents[2] / "assets" / "data" / "part7_summary.json", summary)


def write_input_audit(status: str, notes: str, checks: list[dict]) -> None:
    write_json(REPORT_DIR / "part7_input_audit.json", {"status": status, "notes": notes, "checks": checks, "generated_at_utc": utc_now()})
    write_csv(REPORT_DIR / "decision_input_reconciliation.csv", pd.DataFrame(checks))


def refresh_public_summary(validation: pd.DataFrame) -> None:
    """Make summary, asset mirror and reconciliation report one snapshot."""
    summary_path = REPORT_DIR / "PART7_FINAL_SUMMARY.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
    pass_count = int((validation.status == "PASS").sum())
    blocked_count = int((validation.status == "BLOCKED").sum())
    fail_count = int((validation.status == "FAIL").sum())
    summary["validation"] = {"mandatory_gates": 64, "pass": pass_count, "blocked": blocked_count, "fail": fail_count,
                              "status": summary.get("status", "INPUT_BLOCKED"), "final_lock_eligible": pass_count == 64 and blocked_count == 0 and fail_count == 0}
    pointer_path = REPORT_DIR / "part7_stage_pointer.json"
    pointer = json.loads(pointer_path.read_text(encoding="utf-8")) if pointer_path.exists() else {}
    lifecycle_status = "INPUT_BLOCKED" if summary.get("status") == "INPUT_BLOCKED" else pointer.get("status", summary.get("status", "INPUT_BLOCKED"))
    summary["lifecycle"] = {"status": lifecycle_status, "final_replay_required_before_lock": True,
                             "final_evidence_available": lifecycle_status in {"FINAL_REPLAY_COMPLETE", "DECISION_POLICY_LOCKED"}}
    commit, _ = git_metadata()
    summary["source_commit"] = commit
    summary["validator_version"] = "PART7_EVIDENCE_VALIDATOR_v2.0"
    write_json(summary_path, summary)
    asset_path = ROOT / "assets" / "data" / "part7_summary.json"
    write_json(asset_path, summary)
    reconciliation = {"generated_at_utc": utc_now(), "source_commit": commit, "validator_version": summary["validator_version"],
                      "validation_csv": {"pass": pass_count, "blocked": blocked_count, "fail": fail_count},
                      "summary_json": summary["validation"], "assets_summary_json": json.loads(asset_path.read_text(encoding="utf-8"))["validation"],
                      "status": "PASS" if summary["validation"]["pass"] == pass_count and summary["validation"]["blocked"] == blocked_count and summary["validation"]["fail"] == fail_count else "FAIL"}
    write_json(REPORT_DIR / "P7_PUBLIC_EVIDENCE_RECONCILIATION.json", reconciliation)
