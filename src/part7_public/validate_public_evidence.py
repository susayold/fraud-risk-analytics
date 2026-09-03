from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _load(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def validate() -> list[tuple[str, bool, str]]:
    summary = _load("assets/data/part7_summary.json")
    manifest = _load("reports/part7/public_source_manifest.json")
    snapshot = _load("reports/execution_closure/PRE_REAL_EXECUTION_SNAPSHOT.json")
    page = (ROOT / "part-7.html").read_text(encoding="utf-8")
    summary_text = json.dumps(summary, ensure_ascii=False)
    gates = summary["validation"]
    checks = [
        ("P7 public status is evidence-derived", summary["status"] == "INPUT_BLOCKED", "part7_summary.json"),
        ("P7 mandatory gate contract is preserved", gates == {"mandatory_gates": 64, "pass": 30, "blocked": 34, "fail": 0, "status": "INPUT_BLOCKED", "final_lock_eligible": False}, "part7_summary.json"),
        ("P7 policy and final evidence remain null", all(summary["policy"][key] is None for key in ("review_threshold", "block_threshold", "review_capacity")) and all(value is None for value in summary["final_evidence"].values()), "part7_summary.json"),
        ("P7 target is not presented as current lock", bool(manifest["status"] == "INPUT_BLOCKED" and "64/64 PASS" in manifest["lock_rule"] and snapshot["part7"]["target_status"] == "DECISION_POLICY_LOCKED" and snapshot["snapshot_of_commit"] and snapshot["published_in_commit"]), "manifest and snapshot"),
        ("P7 snapshot reconciles canonical counts", all(snapshot["part7"][key] == gates[key] for key in ("mandatory_gates", "pass", "blocked", "fail", "final_lock_eligible")), "PRE_REAL_EXECUTION_SNAPSHOT.json"),
        ("P7 private handoff is named", "private/part7/PART5_TO_PART7_FROZEN_SCORE_MART.parquet" in manifest["required_private_inputs"] and "private/part7/PART5_TO_PART7_LINEAGE.json" in manifest["required_private_inputs"], "public_source_manifest.json"),
        ("P7 public page exposes all evidence slots", all(f"P7C{i}" in page for i in range(1, 9)), "part-7.html"),
        ("P7 page exposes blocked and safety boundary", all(token in page for token in ("INPUT_BLOCKED", "SIMULATED", "private")) and "graph-only auto-block is forbidden" in page.lower(), "part-7.html"),
        ("P7 public summary has no row-level payload identifiers", all(token not in summary_text for token in ("source_row_id", "transaction_id", "risk_score", "decision_action", "fraud_label")), "part7_summary.json"),
    ]
    return checks


def main() -> int:
    checks = validate()
    passed = sum(ok for _, ok, _ in checks)
    for name, ok, evidence in checks:
        print(f"{'PASS' if ok else 'FAIL'} | {name} | {evidence}")
    print(f"Part 7 public validator: {passed} PASS / {len(checks) - passed} FAIL")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
