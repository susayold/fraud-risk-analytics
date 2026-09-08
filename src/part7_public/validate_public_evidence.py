from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]


def _load(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def validate() -> list[tuple[str, bool, str]]:
    summary = _load("assets/data/part7_summary.json")
    report_path = ROOT / "reports/part7/part7_validation_report.csv"
    report = pd.read_csv(report_path)
    page = (ROOT / "part-7.html").read_text(encoding="utf-8")
    summary_text = json.dumps(summary, ensure_ascii=False)
    gates = summary.get("validation", {})
    policy = summary.get("policy", {})
    evidence = summary.get("final_evidence", {})
    boundary = summary.get("claim_boundary", {})

    checks = [
        (
            "P7 public status is final evidence-derived",
            summary.get("status") == "DECISION_POLICY_LOCKED",
            "assets/data/part7_summary.json",
        ),
        (
            "P7 mandatory gate contract is final locked",
            gates.get("mandatory_gates") == 64
            and gates.get("pass") == 64
            and gates.get("blocked") == 0
            and gates.get("fail") == 0
            and gates.get("final_lock_eligible") is True,
            "assets/data/part7_summary.json",
        ),
        (
            "P7 published validator snapshot is 64/64 PASS",
            len(report) == 64 and "status" in report and report["status"].astype(str).eq("PASS").all(),
            "reports/part7/part7_validation_report.csv",
        ),
        (
            "P7 frozen policy is published",
            all(policy.get(key) is not None for key in ("review_threshold", "block_threshold", "review_capacity"))
            and float(policy["review_threshold"]) < float(policy["block_threshold"]),
            "assets/data/part7_summary.json",
        ),
        (
            "P7 aggregate final OOT evidence is published",
            all(evidence.get(key) is not None for key in ("allow_rate", "review_rate", "block_rate", "fraud_capture", "fraud_exposure_capture", "legitimate_block_rate", "simulated_total_cost")),
            "assets/data/part7_summary.json",
        ),
        (
            "P7 claim boundary remains explicit",
            boundary.get("synthetic_data") is True
            and boundary.get("simulated_costs") is True
            and boundary.get("not_production_deployment") is True,
            "assets/data/part7_summary.json",
        ),
        (
            "P7 page exposes governed decision semantics",
            all(token in page for token in ("ALLOW", "REVIEW", "BLOCK", "FINAL OOT", "SIMULATED ECONOMICS"))
            and "graph-only auto-block" in page.lower(),
            "part-7.html",
        ),
        (
            "P7 public summary stays aggregate-only",
            all(token not in summary_text for token in ("source_row_id", "transaction_id", "risk_score", "fraud_label")),
            "assets/data/part7_summary.json",
        ),
        (
            "P7 final-run provenance is retained",
            bool(summary.get("source_commit")) and bool(summary.get("validator_version")),
            "assets/data/part7_summary.json",
        ),
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
