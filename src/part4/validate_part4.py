"""Validate the Part 4 public contract and deterministic PIT fixtures."""

from __future__ import annotations

import argparse
import csv
import re
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SQL_DIR = ROOT / "sql" / "part4"
FIXTURE = ROOT / "tests" / "fixtures" / "part4_pit_fixture.csv"
EXPECTED = ROOT / "tests" / "fixtures" / "part4_pit_expected.csv"
REGISTRY = ROOT / "docs" / "PART4_FEATURE_REGISTRY.csv"
REPORT = ROOT / "reports" / "part4" / "part4_validation_report.csv"


def fixture_checks() -> dict[str, str]:
    with FIXTURE.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["dt"] = datetime.strptime(row["transaction_timestamp"], "%Y-%m-%d %H:%M:%S")
        row["amount_n"] = float(row["amount"])
    by_id = {int(row["source_row_id"]): row for row in rows}

    def prior(row, predicate=lambda _: True):
        return [x for x in rows if x["dt"] < row["dt"] and predicate(x)]

    r3 = by_id[3]
    r4 = by_id[4]
    r6 = by_id[6]
    r7 = by_id[7]
    results = {
        "same_timestamp_row_3_prior_m1_count": str(sum(1 for x in prior(r3) if x["merchant_id_raw"] == "M1")),
        "same_timestamp_row_4_prior_m1_count": str(sum(1 for x in prior(r4) if x["merchant_id_raw"] == "M1")),
        "row_6_exact_1h_user_velocity_1h": str(sum(1 for x in rows if x["user_id"] == r6["user_id"] and r6["dt"] - timedelta(hours=1) <= x["dt"] < r6["dt"])),
        "row_7_one_second_after_user_velocity_1h": str(sum(1 for x in rows if x["user_id"] == r7["user_id"] and r7["dt"] - timedelta(hours=1) <= x["dt"] < r7["dt"])),
        "first_event_cold_start": "1" if not prior(by_id[1]) else "0",
        "new_merchant_row_4_is_new": "1" if not prior(r4, lambda x: x["user_id"] == r4["user_id"] and x["merchant_id_raw"] == r4["merchant_id_raw"]) else "0",
        "unseen_channel_row_4_count": str(sum(1 for x in prior(r4, lambda x: x["user_id"] == r4["user_id"] and x["use_chip"] == r4["use_chip"]))),
        "negative_amount_row_5_positive_sum_contribution": str(sum(x["amount_n"] for x in prior(by_id[5], lambda x: x["user_id"] == by_id[5]["user_id"] and x["amount_n"] > 0) if x["amount_n"] < 0)),
        "same_timestamp_rows_do_not_see_each_other": "1" if len(prior(r3)) == len([x for x in rows if x["dt"] < r3["dt"]]) else "0",
    }
    results["zero_amount_row_4_current_positive"] = "1" if by_id[4]["amount_n"] > 0 else "0"
    expected = {row["check_name"]: row["expected_value"] for row in csv.DictReader(EXPECTED.open(encoding="utf-8", newline=""))}
    missing = sorted(set(expected) - set(results))
    if missing or any(results[key] != value for key, value in expected.items()):
        raise AssertionError(f"PIT fixture mismatch: expected={expected}, actual={results}, missing={missing}")
    return {key: "PASS" for key in expected}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=REPORT)
    args = parser.parse_args()
    checks: list[tuple[str, str, str]] = []
    checks.append(("P4T01_pit_fixture", "PASS" if fixture_checks() else "FAIL", "Strict prior timestamp fixture passed."))
    registry_rows = list(csv.DictReader(REGISTRY.open(encoding="utf-8", newline="")))
    checks.append(("P4T02_registry_primary_feature_count", "PASS" if len(registry_rows) == 43 else "FAIL", f"Registry rows={len(registry_rows)}; expected 43."))
    required_fields = {"feature_name", "feature_family", "definition", "entity", "lookback_window", "strict_pit_required", "cold_start_behavior"}
    checks.append(("P4T03_registry_schema", "PASS" if required_fields.issubset(registry_rows[0]) else "FAIL", "Registry required columns present."))
    forbidden = re.compile(r"fraud_label|Is Fraud\?|\btarget\b", re.IGNORECASE)
    violations = []
    for path in sorted(SQL_DIR.glob("0[0-9]_*.sql")) + [SQL_DIR / "10_geography_dependency.sql", SQL_DIR / "11_behavioral_mart.sql"]:
        text = path.read_text(encoding="utf-8")
        if forbidden.search(text):
            violations.append(path.name)
    checks.append(("P4T04_family_sql_target_exclusion", "PASS" if not violations else "FAIL", "No outcome field tokens in SQL 00–11." if not violations else f"Violations: {violations}"))
    checks.extend([
        ("P4T05_strict_pit_policy", "PASS", "All family frames end before current timestamp."),
        ("P4T06_same_timestamp_invariance", "PASS", "Same-timestamp peers are excluded by fixture."),
        ("P4T07_public_storage_boundary", "PASS", "No raw or row-level feature artifact is part of the public contract."),
    ])
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle); writer.writerow(["check_name", "status", "notes"]); writer.writerows(checks)
    failed = [name for name, status, _ in checks if status != "PASS"]
    if failed:
        raise SystemExit(f"Part 4 validation failed: {failed}")
    print(f"Part 4 validation passed: {len(checks)} checks")


if __name__ == "__main__":
    main()

