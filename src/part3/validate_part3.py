"""Fail-closed Part 3 aggregate and governance validation."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT / "reports" / "part3"
SUMMARY = ROOT / "assets" / "data" / "part3_summary.json"
DEV_ROWS = 9_673_486
DEV_FRAUD = 13_661
REQUIRED = ["portfolio_summary.csv", "monthly_fraud_trend.csv", "yearly_fraud_trend.csv", "channel_risk.csv", "amount_band_risk.csv", "mcc_risk.csv", "state_risk.csv", "merchant_city_risk.csv", "user_concentration.csv", "card_concentration.csv", "merchant_concentration.csv", "top_entity_concentration.csv", "segment_priority.csv", "split_stability_summary.csv", "part3_validation_report.csv"]


def read(name: str) -> list[dict[str, str]]:
    with (REPORT_DIR / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def n(row: dict[str, str], key: str) -> float:
    return float(row[key])


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
    with (REPORT_DIR / "part3_validation_report.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["test_id", "status", "evidence"]); writer.writeheader(); writer.writerows(checks)
    print(f"PART 3 VALIDATION PASSED: {len(checks)} checks")


if __name__ == "__main__":
    main()
