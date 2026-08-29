"""Fail-closed Part 3 aggregate and governance validation."""

from __future__ import annotations

import csv
import json
from math import isfinite
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT / "reports" / "part3"
SUMMARY = ROOT / "assets" / "data" / "part3_summary.json"
DEV_ROWS = 9_673_486
DEV_FRAUD = 13_661
REQUIRED = ["portfolio_summary.csv", "monthly_fraud_trend.csv", "yearly_fraud_trend.csv", "channel_risk.csv", "amount_band_risk.csv", "mcc_risk.csv", "state_risk.csv", "merchant_city_risk.csv", "user_concentration.csv", "card_concentration.csv", "merchant_concentration.csv", "top_entity_concentration.csv", "segment_priority.csv", "split_stability_summary.csv", "part3_validation_report.csv"]
PRIORITY_CLASSES = {"PRIORITY_1", "PRIORITY_2", "MONITOR", "LOW_PRIORITY"}
SUMMARY_KEYS = {"status", "analysis_scope", "development", "portfolio_metrics", "monthly_trend", "yearly_trend", "channel", "amount_bands", "amount_distribution", "mcc", "geography", "concentration", "priority_segments", "stability", "findings", "governance", "artifact_counts"}


def read(name: str) -> list[dict[str, str]]:
    with (REPORT_DIR / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def n(row: dict[str, str], key: str) -> float:
    return float(row[key])


def finite(row: dict[str, object], key: str) -> bool:
    try:
        return isfinite(float(row[key]))
    except (TypeError, ValueError, KeyError):
        return False


def expected_priority(row: dict[str, str]) -> str:
    if row["support_status"] == "LOW_SUPPORT":
        return "LOW_PRIORITY"
    lift = n(row, "fraud_lift")
    capture = n(row, "fraud_capture_share")
    amount_capture = float(row["fraud_amount_capture_share"]) if row.get("fraud_amount_capture_share") not in (None, "") else None
    if lift >= 2 and (capture >= .05 or (amount_capture is not None and amount_capture >= .05)):
        return "PRIORITY_1"
    if lift >= 1.25 or capture >= .03 or (amount_capture is not None and amount_capture >= .03):
        return "PRIORITY_2"
    return "MONITOR"


def check(name: str, condition: bool, evidence: str, rows: list[dict[str, object]]) -> None:
    rows.append({"test_id": name, "status": "PASS" if condition else "FAIL", "evidence": evidence})
    if not condition:
        raise AssertionError(f"{name}: {evidence}")


def main() -> None:
    for name in REQUIRED[:-1]:
        if not (REPORT_DIR / name).exists():
            raise AssertionError(f"missing report: {name}")
    if not SUMMARY.exists():
        raise AssertionError("missing Part 3 summary JSON")
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    if summary.get("status") != "PORTFOLIO_READY":
        raise AssertionError(f"summary status: {summary.get('status')}")
    checks: list[dict[str, object]] = []
    portfolio = read("portfolio_summary.csv")
    dev = next(row for row in portfolio if row["analysis_scope"] == "DEVELOPMENT_DISCOVERY")
    check("P3T01", int(dev["transactions"]) == DEV_ROWS, f"Development rows={dev['transactions']}", checks)
    check("P3T02", int(dev["fraud_transactions"]) == DEV_FRAUD, f"Development fraud rows={dev['fraud_transactions']}", checks)
    for test_id, filename in [("P3T03", "channel_risk.csv"), ("P3T04", "amount_band_risk.csv"), ("P3T05", "mcc_risk.csv"), ("P3T06", "state_risk.csv"), ("P3T07", "merchant_city_risk.csv")]:
        rows = read(filename)
        check(test_id, sum(n(row, "transaction_share") for row in rows) >= .999999 and sum(n(row, "transaction_share") for row in rows) <= 1.000001, f"{filename} transaction shares sum to {sum(n(row, 'transaction_share') for row in rows):.9f}", checks)
    amount = read("amount_band_risk.csv")
    check("P3T05_BANDS", len(amount) == 8 and sum(int(row["transactions"]) for row in amount) == DEV_ROWS, f"amount bands={len(amount)}, rows={sum(int(row['transactions']) for row in amount)}", checks)
    state = read("state_risk.csv")
    check("P3T07_UNKNOWN", any(row["segment_value"] == "<UNKNOWN>" for row in state), "missing geography is retained as <UNKNOWN>", checks)
    for filename in ("user_concentration.csv", "card_concentration.csv", "merchant_concentration.csv"):
        rows = read(filename)
        check("P3T08_" + filename.split("_")[0].upper(), len(rows) == 1 and int(rows[0]["entity_fraud_transactions"]) == DEV_FRAUD and all(0 <= n(rows[0], key) <= 1 for key in ("top_10_fraud_share", "top_100_fraud_share", "top_1pct_fraud_share", "top_5pct_fraud_share")), f"{filename} denominator={rows[0]['entity_fraud_transactions']}", checks)
    public_headers = [field for name in REQUIRED[:-1] for field in (read(name)[0].keys() if read(name) else [])]
    check("P3T09", not any("source_row_id" in field or field in {"transaction_id", "user_id", "card_id", "merchant_id"} for field in public_headers), "aggregate reports contain no row-level identifiers", checks)
    detailed_scopes = {row["analysis_scope"] for filename in ("channel_risk.csv", "amount_band_risk.csv", "mcc_risk.csv", "state_risk.csv", "merchant_city_risk.csv", "segment_priority.csv") for row in read(filename)}
    check("P3T10", detailed_scopes == {"DEVELOPMENT_DISCOVERY"}, f"detailed scopes={sorted(detailed_scopes)}", checks)
    check("P3T11", int(summary["development"]["transactions"]) == DEV_ROWS and len(summary["channel"]) == len(read("channel_risk.csv")), "website summary matches baseline/channel reports", checks)
    website_text = (ROOT / "part-3.html").read_text(encoding="utf-8") if (ROOT / "part-3.html").exists() else ""
    forbidden = ("causes fraud", "loss prevented", "bank loss", "realized fraud loss")
    check("P3T12", not any(term in website_text.lower() for term in forbidden), "website avoids causal or loss-prevention claims", checks)
    priority_summary_fields = {"analysis_scope", "segment_type", "segment_value", "transactions", "transaction_share", "fraud_transactions", "fraud_rate", "fraud_lift", "fraud_capture_share", "fraud_amount_capture_share", "support_status", "priority_class"}
    priority_rows = summary.get("priority_segments", [])
    priority_schema_ok = all(priority_summary_fields.issubset(row) for row in priority_rows) and all(
        finite(row, "transaction_share") and finite(row, "fraud_transactions") and finite(row, "fraud_rate") and finite(row, "fraud_lift") and finite(row, "fraud_capture_share")
        and 0 <= n(row, "transaction_share") <= 1 and n(row, "fraud_transactions") >= 0 and n(row, "fraud_rate") >= 0 and n(row, "fraud_lift") >= 0 and 0 <= n(row, "fraud_capture_share") <= 1
        and (row.get("fraud_amount_capture_share") in (None, "") or finite(row, "fraud_amount_capture_share"))
        and row.get("priority_class") in PRIORITY_CLASSES
        for row in priority_rows
    )
    check("P3T13_PRIORITY_SCHEMA", priority_schema_ok, f"priority summary rows={len(priority_rows)} with required finite fields", checks)
    priority_lookup = {(row["segment_type"], row["segment_value"]): row["priority_class"] for row in read("segment_priority.csv")}
    mcc_rows = summary.get("mcc", [])
    mcc_schema_ok = all(
        {"segment_value", "transactions", "transaction_share", "fraud_transactions", "fraud_rate", "fraud_lift", "fraud_capture_share", "fraud_amount_capture_share", "support_status", "priority_class"}.issubset(row)
        and row.get("priority_class") in PRIORITY_CLASSES
        and priority_lookup.get(("mcc", str(row.get("segment_value")))) == row.get("priority_class")
        for row in mcc_rows
    )
    check("P3T14_MCC_PRIORITY", mcc_schema_ok, f"public MCC rows={len(mcc_rows)} map to segment_priority.csv", checks)
    check("P3T15_SUMMARY_SCHEMA", SUMMARY_KEYS.issubset(summary.keys()), f"summary keys present={len(summary.keys())}", checks)
    js_text = (ROOT / "js" / "part-3.js").read_text(encoding="utf-8")
    render_contract = {
        "renderTrend": ("month", "fraud_rate", "fraud_transactions", "transactions"),
        "renderChannels": ("segment_value", "fraud_rate", "fraud_lift", "fraud_capture_share"),
        "renderAmount": ("transaction_share", "fraud_lift", "fraud_transactions", "fraud_amount_capture_share"),
        "renderMcc": ("segment_value", "fraud_lift", "fraud_rate", "fraud_transactions", "priority_class"),
        "renderGeography": ("segment_value", "fraud_capture_share", "fraud_lift", "transactions"),
        "renderConcentration": ("top_1pct_fraud_share", "top_100_fraud_share", "fraud_affected_entities", "repeat_fraud_entities"),
        "renderPriority": ("transaction_share", "fraud_lift", "fraud_transactions", "priority_class", "fraud_capture_share"),
    }
    render_contract_ok = True
    render_evidence = []
    for function_name, fields in render_contract.items():
        start = js_text.find(f"function {function_name}")
        end = js_text.find("\n  function ", start + 1) if start >= 0 else -1
        block = js_text[start:end if end >= 0 else len(js_text)] if start >= 0 else ""
        missing_fields = [field for field in fields if field not in block]
        if missing_fields:
            render_contract_ok = False
            render_evidence.append(f"{function_name}: missing {missing_fields}")
    check("P3T16_RENDER_CONTRACT", render_contract_ok, "; ".join(render_evidence) or "all JS renderer fields are represented", checks)
    priority_report = read("segment_priority.csv")
    priority_rules_ok = all(row["priority_class"] == expected_priority(row) for row in priority_report)
    check("P3T17_PRIORITY_RULE", priority_rules_ok, f"priority rows checked={len(priority_report)} against the locked rule", checks)
    monthly_rows = read("monthly_fraud_trend.csv")
    yearly_rows = read("yearly_fraud_trend.csv")
    trend_order_ok = [row["month"] for row in monthly_rows] == sorted(row["month"] for row in monthly_rows) and [int(row["year"]) for row in yearly_rows] == sorted(int(row["year"]) for row in yearly_rows)
    check("P3T18_TREND_ORDER", trend_order_ok, "monthly and yearly reports are monotonically ordered", checks)
    with (REPORT_DIR / "part3_validation_report.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["test_id", "status", "evidence"]); writer.writeheader(); writer.writerows(checks)
    print(f"PART 3 VALIDATION PASSED: {len(checks)} checks")


if __name__ == "__main__":
    main()
