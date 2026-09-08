from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]


def _load(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def validate() -> list[tuple[str, bool, str]]:
    summary = _load("assets/data/part8_summary.json")
    report_path = ROOT / "reports/part8/part8_validation_report.csv"
    report = pd.read_csv(report_path)
    page = (ROOT / "part-8.html").read_text(encoding="utf-8")
    summary_text = json.dumps(summary, ensure_ascii=False)
    gates = summary.get("validation", {})
    boundary = summary.get("claim_boundary", {})
    lifecycle = summary.get("lifecycle", {})
    clocks = summary.get("two_clock", {})

    checks = [
        (
            "P8 public status is final evidence-derived",
            summary.get("status") == "MONITORING_GOVERNANCE_LOCKED",
            "assets/data/part8_summary.json",
        ),
        (
            "P8 mandatory gate contract is final locked",
            gates.get("mandatory_gates") == 72
            and gates.get("pass") == 72
            and gates.get("blocked") == 0
            and gates.get("fail") == 0
            and gates.get("final_lock_eligible") is True,
            "assets/data/part8_summary.json",
        ),
        (
            "P8 published validator snapshot is 72/72 PASS",
            len(report) == 72 and "status" in report and report["status"].astype(str).eq("PASS").all(),
            "reports/part8/part8_validation_report.csv",
        ),
        (
            "P8 two-clock monitoring contract is published",
            clocks.get("operational") == "OPERATIONS_NOW" and clocks.get("matured") == "OUTCOMES_MATURED",
            "assets/data/part8_summary.json",
        ),
        (
            "P8 matured outcomes are available",
            lifecycle.get("matured_outcomes_available") is True and int(lifecycle.get("matured_outcome_rows", 0)) > 0,
            "assets/data/part8_summary.json",
        ),
        (
            "P8 claim boundary remains explicit",
            boundary.get("offline_retrospective_monitoring") is True
            and boundary.get("not_production_monitoring") is True
            and boundary.get("raw_row_level_public_data") is False
            and boundary.get("genuine_locked_upstream_evidence") is True,
            "assets/data/part8_summary.json",
        ),
        (
            "P8 page exposes two clocks and non-mutating governance",
            all(token in page for token in ("OPERATIONS_NOW", "OUTCOMES_MATURED", "NO AUTO-RETRAIN"))
            and "not live production monitoring" in page.lower(),
            "part-8.html",
        ),
        (
            "P8 public summary stays aggregate-only",
            all(token not in summary_text for token in ("source_row_id", "transaction_id", "risk_score", "fraud_label")),
            "assets/data/part8_summary.json",
        ),
        (
            "P8 final-run provenance is retained",
            bool(summary.get("source_commit")) and bool(summary.get("validator_version")),
            "assets/data/part8_summary.json",
        ),
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
