from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _load(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def validate() -> list[tuple[str, bool, str]]:
    summary = _load("assets/data/part8_summary.json")
    manifest = _load("reports/part8/public_source_manifest.json")
    snapshot = _load("reports/execution_closure/PRE_REAL_EXECUTION_SNAPSHOT.json")
    page = (ROOT / "part-8.html").read_text(encoding="utf-8")
    summary_text = json.dumps(summary, ensure_ascii=False)
    gates = summary["validation"]
    checks = [
        ("P8 public status is evidence-derived", summary["status"] == "INPUT_BLOCKED", "part8_summary.json"),
        ("P8 mandatory gate contract is preserved", gates == {"mandatory_gates": 72, "pass": 20, "blocked": 52, "fail": 0, "status": "INPUT_BLOCKED", "final_lock_eligible": False}, "part8_summary.json"),
        ("P8 label maturity is not claimed observed", summary["claim_boundary"]["label_latency_observed"] is False and summary["lifecycle"]["matured_outcomes_available"] is False, "part8_summary.json"),
        ("P8 target is not presented as current lock", manifest["status"] == "INPUT_BLOCKED" and "72/72 PASS" in manifest["lock_rule"] and snapshot["part8"]["target_status"] == "MONITORING_GOVERNANCE_LOCKED", "manifest and snapshot"),
        ("P8 private handoff is named", "private/part8/PART7_TO_PART8_DECISION_MART.parquet" in manifest["required_private_inputs"] and "reports/part8/PART8_MONITORING_BASELINE_FREEZE.json" in manifest["required_private_inputs"], "public_source_manifest.json"),
        ("P8 public page exposes all evidence slots", all(f"P8C{i}" in page for i in range(1, 11)), "part-8.html"),
        ("P8 page exposes two clocks and non-mutating boundary", all(token in page for token in ("INPUT_BLOCKED", "OPERATIONS_NOW", "OUTCOMES_MATURED", "NO AUTO-RETRAIN", "not live production monitoring")), "part-8.html"),
        ("P8 public summary has no row-level payload identifiers", all(token not in summary_text for token in ("source_row_id", "transaction_id", "risk_score", "decision_action", "fraud_label")), "part8_summary.json"),
    ]
    return checks


def main() -> int:
    checks = validate()
    passed = sum(ok for _, ok, _ in checks)
    for name, ok, evidence in checks:
        print(f"{'PASS' if ok else 'FAIL'} | {name} | {evidence}")
    print(f"Part 8 public validator: {passed} PASS / {len(checks) - passed} FAIL")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
