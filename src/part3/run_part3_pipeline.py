"""Execute the Part 3 aggregate portfolio analytics pipeline."""

from __future__ import annotations

import argparse
import csv
import json
from math import isfinite
from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parents[2]
SQL_DIR = ROOT / "sql" / "part3"
REPORT_DIR = ROOT / "reports" / "part3"
SUMMARY_PATH = ROOT / "assets" / "data" / "part3_summary.json"
SQL_ORDER = [
    "00_portfolio_summary.sql", "01_time_trend.sql", "02_channel_risk.sql", "03_amount_band_risk.sql",
    "04_mcc_risk.sql", "05_geography_risk.sql", "06_user_card_concentration.sql",
    "07_merchant_concentration.sql", "08_segment_priority.sql", "09_split_stability.sql",
]


def export_table(db: duckdb.DuckDBPyConnection, table: str, filename: str, order_by: str | None = None) -> list[dict[str, object]]:
    query = f"SELECT * FROM {table}"
    if order_by:
        query += f" ORDER BY {order_by}"
    cursor = db.execute(query)
    fields = [item[0] for item in cursor.description]
    rows = [dict(zip(fields, row)) for row in cursor.fetchall()]
    with (REPORT_DIR / filename).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(fields)
        writer.writerows([[row[field] for field in fields] for row in rows])
    return rows


def to_json_value(value: object) -> object:
    if hasattr(value, "as_integer_ratio"):
        return float(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def json_safe(value: object) -> object:
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    return to_json_value(value)


def attach_priority(rows: list[dict[str, object]], segment_type: str, priority_lookup: dict[tuple[str, str], str]) -> list[dict[str, object]]:
    enriched = []
    for row in rows:
        key = (segment_type, str(row["segment_value"]))
        if key not in priority_lookup:
            raise ValueError(f"Missing priority class for {segment_type} {row['segment_value']}")
        copy = dict(row)
        copy["priority_class"] = priority_lookup[key]
        enriched.append(copy)
    return enriched


PRIORITY_CLASSES = {"PRIORITY_1", "PRIORITY_2", "MONITOR", "LOW_PRIORITY"}
SUMMARY_REQUIRED_KEYS = {
    "status", "analysis_scope", "development", "portfolio_metrics", "monthly_trend", "yearly_trend",
    "channel", "amount_bands", "amount_distribution", "mcc", "geography", "concentration",
    "priority_segments", "stability", "findings", "governance", "artifact_counts",
}


def finite(value: object, field: str) -> float:
    if value is None or isinstance(value, bool):
        raise ValueError(f"Summary field {field} is not numeric")
    result = float(value)
    if not isfinite(result):
        raise ValueError(f"Summary field {field} is not finite")
    return result


def validate_summary(summary: dict[str, object]) -> None:
    missing = SUMMARY_REQUIRED_KEYS - summary.keys()
    if missing:
        raise ValueError(f"Summary contract missing top-level keys: {sorted(missing)}")
    if summary["status"] != "PORTFOLIO_READY" or summary["analysis_scope"] != "DEVELOPMENT_DISCOVERY":
        raise ValueError("Summary status or analysis scope is invalid")
    development = summary["development"]
    if not isinstance(development, dict):
        raise ValueError("Summary development object is invalid")
    for field in ("transactions", "fraud_transactions", "fraud_rate", "total_amount", "fraud_amount", "fraud_amount_share", "avg_amount", "avg_fraud_amount", "median_amount", "median_fraud_amount"):
        finite(development.get(field), f"development.{field}")

    priority_fields = ("analysis_scope", "segment_type", "segment_value", "transactions", "transaction_share", "fraud_transactions", "fraud_rate", "fraud_lift", "fraud_capture_share", "fraud_amount_capture_share", "support_status", "priority_class")
    for row in summary["priority_segments"]:
        missing_fields = [field for field in priority_fields if field not in row]
        if missing_fields:
            raise ValueError(f"Priority summary row missing fields: {missing_fields}")
        finite(row["transactions"], "priority_segments.transactions")
        transaction_share = finite(row["transaction_share"], "priority_segments.transaction_share")
        fraud_transactions = finite(row["fraud_transactions"], "priority_segments.fraud_transactions")
        fraud_rate = finite(row["fraud_rate"], "priority_segments.fraud_rate")
        fraud_lift = finite(row["fraud_lift"], "priority_segments.fraud_lift")
        fraud_capture = finite(row["fraud_capture_share"], "priority_segments.fraud_capture_share")
        if not 0 <= transaction_share <= 1 or fraud_transactions < 0 or fraud_rate < 0 or fraud_lift < 0 or not 0 <= fraud_capture <= 1:
            raise ValueError(f"Priority summary values are outside contract bounds: {row}")
        if row["fraud_amount_capture_share"] is not None:
            finite(row["fraud_amount_capture_share"], "priority_segments.fraud_amount_capture_share")
        if row["priority_class"] not in PRIORITY_CLASSES:
            raise ValueError(f"Invalid priority class: {row['priority_class']}")

    mcc_fields = ("segment_value", "transactions", "transaction_share", "fraud_transactions", "fraud_rate", "fraud_lift", "fraud_capture_share", "fraud_amount_capture_share", "support_status", "priority_class")
    for row in summary["mcc"]:
        missing_fields = [field for field in mcc_fields if field not in row]
        if missing_fields or row["priority_class"] not in PRIORITY_CLASSES:
            raise ValueError(f"MCC public summary row violates contract: {row}")
        finite(row["transactions"], "mcc.transactions")
        finite(row["transaction_share"], "mcc.transaction_share")
        finite(row["fraud_transactions"], "mcc.fraud_transactions")
        finite(row["fraud_rate"], "mcc.fraud_rate")
        finite(row["fraud_lift"], "mcc.fraud_lift")
        finite(row["fraud_capture_share"], "mcc.fraud_capture_share")
        if row["fraud_amount_capture_share"] is not None:
            finite(row["fraud_amount_capture_share"], "mcc.fraud_amount_capture_share")

    trend_contract = {"month", "fraud_rate", "fraud_transactions", "transactions"}
    for row in summary["monthly_trend"]:
        if not trend_contract.issubset(row):
            raise ValueError(f"Monthly trend row violates contract: {row}")
        finite(row["fraud_rate"], "monthly_trend.fraud_rate"); finite(row["fraud_transactions"], "monthly_trend.fraud_transactions"); finite(row["transactions"], "monthly_trend.transactions")
    years = [int(row["year"]) for row in summary["yearly_trend"]]
    months = [str(row["month"]) for row in summary["monthly_trend"]]
    if months != sorted(months) or years != sorted(years):
        raise ValueError("Trend summary is not deterministically ordered")


def write_top_entity_concentration(concentration: list[dict[str, object]]) -> None:
    fields = ["analysis_scope", "entity_type", "rank_band", "fraud_capture_share"]
    rows = []
    for row in concentration:
        for band in ("top_10", "top_100", "top_1pct", "top_5pct"):
            rows.append({"analysis_scope": row["analysis_scope"], "entity_type": row["entity_type"], "rank_band": band, "fraud_capture_share": row[f"{band}_fraud_share"]})
    with (REPORT_DIR / "top_entity_concentration.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)


def make_findings(dev: dict[str, object], channels: list[dict[str, object]], amount_bands: list[dict[str, object]], concentration: list[dict[str, object]], stability: list[dict[str, object]]) -> list[dict[str, str]]:
    online = next((row for row in channels if str(row["segment_value"]).lower() == "online transaction"), None)
    top_amount = max(amount_bands, key=lambda row: float(row["fraud_lift"] or 0))
    top_entity = max(concentration, key=lambda row: float(row["top_1pct_fraud_share"] or 0))
    findings = []
    if online:
        findings.append({"title": "Online channel is elevated in Development", "evidence": f"{float(online['fraud_rate'])*100:.3f}% fraud rate; {float(online['fraud_lift']):.2f}x lift; {float(online['fraud_capture_share'])*100:.1f}% of fraud transactions.", "meaning": "Channel is both risk-elevated and material enough to warrant deeper behavioral analysis.", "next_action": "Test channel-specific velocity and amount-deviation questions in Part 4 using strict prior history."})
    findings.append({"title": "Risk is not the same as exposure", "evidence": f"Development contains {int(dev['transactions']):,} transactions and {int(dev['fraud_transactions']):,} fraud-labeled transactions; signed fraud amount share is {float(dev['fraud_amount_share'])*100:.3f}%.", "meaning": "Prevalence, fraud count and signed amount must be read together before prioritizing a segment.", "next_action": "Carry both count-based and amount-based views into later decision economics."})
    findings.append({"title": f"{top_amount['segment_value']} is the highest-lift amount band", "evidence": f"{float(top_amount['fraud_lift']):.2f}x Development lift with {int(top_amount['fraud_transactions']):,} fraud-labeled transactions.", "meaning": "The band is a descriptive hypothesis, not a production rule or loss estimate.", "next_action": "Test amount-context and card-history behavior in Part 4; do not finalize a threshold here."})
    findings.append({"title": f"Entity concentration is visible at the {top_entity['entity_type'].lower()} level", "evidence": f"The top 1% of {top_entity['entity_type'].lower()} entities account for {float(top_entity['top_1pct_fraud_share'])*100:.1f}% of fraud transactions; {int(top_entity['repeat_fraud_entities']):,} entities have repeated fraud labels.", "meaning": "Retrospective concentration motivates history features while remaining distinct from a point-in-time model feature.", "next_action": "Reconstruct prior entity history in Part 4 with timestamps strictly less than T0."})
    development_split = next((row for row in stability if row["split_name"] == "DEVELOPMENT"), None)
    validation = next((row for row in stability if row["split_name"] == "VALIDATION"), None)
    oot = next((row for row in stability if row["split_name"] == "OUT_OF_TIME_OOT"), None)
    if validation and oot:
        development_chip_share = float(development_split["chip_share"]) if development_split else 0.0
        findings.append({"title": "Channel composition shifts after Development", "evidence": f"Chip share moves from {development_chip_share*100:.1f}% in Development to {float(validation['chip_share'])*100:.1f}% in Validation and {float(oot['chip_share'])*100:.1f}% in OOT.", "meaning": "A channel absent during detailed discovery appears later, so downstream categorical handling must be unknown-safe.", "next_action": "In Part 4/5, support unseen channel values and monitor channel-mix drift without mining OOT subsegments."})
    return findings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True, help="Temporary Part 2 DuckDB database.")
    args = parser.parse_args()
    database = args.database.resolve()
    if not database.exists():
        raise SystemExit(f"DuckDB database not found: {database}")
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    db = duckdb.connect(str(database))
    for filename in SQL_ORDER:
        db.execute((SQL_DIR / filename).read_text(encoding="utf-8"))
    portfolio = export_table(db, "analytics.part3_portfolio_summary", "portfolio_summary.csv", "analysis_scope")
    monthly = export_table(db, "analytics.part3_monthly_fraud_trend", "monthly_fraud_trend.csv", "month")
    yearly = export_table(db, "analytics.part3_yearly_fraud_trend", "yearly_fraud_trend.csv", "year")
    channels = export_table(db, "analytics.part3_channel_risk", "channel_risk.csv", "fraud_capture_share DESC, segment_value")
    amount_bands = export_table(db, "analytics.part3_amount_band_risk", "amount_band_risk.csv", "CASE segment_value WHEN 'NEGATIVE / REFUND-LIKE' THEN 1 WHEN 'ZERO' THEN 2 WHEN '>0–25' THEN 3 WHEN '25–50' THEN 4 WHEN '50–100' THEN 5 WHEN '100–250' THEN 6 WHEN '250–500' THEN 7 WHEN '500+' THEN 8 ELSE 9 END")
    distributions = export_table(db, "analytics.part3_amount_distribution", "amount_distribution.csv", "label_group")
    mcc = export_table(db, "analytics.part3_mcc_risk", "mcc_risk.csv", "segment_value")
    states = export_table(db, "analytics.part3_state_risk", "state_risk.csv", "segment_value")
    cities = export_table(db, "analytics.part3_merchant_city_risk", "merchant_city_risk.csv", "segment_value")
    users = export_table(db, "analytics.part3_user_concentration", "user_concentration.csv", "entity_type")
    cards = export_table(db, "analytics.part3_card_concentration", "card_concentration.csv", "entity_type")
    merchants = export_table(db, "analytics.part3_merchant_concentration", "merchant_concentration.csv", "entity_type")
    interactions = export_table(db, "analytics.part3_interaction_risk", "interaction_risk.csv", "segment_value")
    priority = export_table(db, "analytics.part3_segment_priority", "segment_priority.csv", "CASE priority_class WHEN 'PRIORITY_1' THEN 1 WHEN 'PRIORITY_2' THEN 2 WHEN 'MONITOR' THEN 3 ELSE 4 END, fraud_capture_share DESC, fraud_lift DESC, segment_type, segment_value")
    stability = export_table(db, "analytics.part3_split_stability", "split_stability_summary.csv", "CASE split_name WHEN 'DEVELOPMENT' THEN 1 WHEN 'VALIDATION' THEN 2 ELSE 3 END")
    concentration = users + cards + merchants
    write_top_entity_concentration(concentration)
    db.close()

    dev = next(row for row in portfolio if row["analysis_scope"] == "DEVELOPMENT_DISCOVERY")
    priority_lookup = {(str(row["segment_type"]), str(row["segment_value"])): str(row["priority_class"]) for row in priority}
    material_mcc = sorted((row for row in mcc if row["support_status"] == "SUFFICIENT"), key=lambda row: (-float(row["fraud_lift"] or 0), -int(row["fraud_transactions"] or 0)))[:10]
    material_mcc = attach_priority(material_mcc, "mcc", priority_lookup)
    material_states = sorted((row for row in states if row["support_status"] == "SUFFICIENT"), key=lambda row: (-float(row["fraud_capture_share"] or 0), -int(row["fraud_transactions"] or 0)))[:10]
    priority_display = sorted((row for row in priority if row["support_status"] == "SUFFICIENT"), key=lambda row: ({"PRIORITY_1": 0, "PRIORITY_2": 1, "MONITOR": 2, "LOW_PRIORITY": 3}[row["priority_class"]], -float(row["fraud_capture_share"] or 0)))[:12]
    summary = {
        "status": "PORTFOLIO_READY", "analysis_scope": "DEVELOPMENT_DISCOVERY", "development": dev,
        "portfolio_metrics": portfolio, "monthly_trend": monthly, "yearly_trend": yearly,
        "channel": channels, "amount_bands": amount_bands, "amount_distribution": distributions,
        "mcc": material_mcc, "geography": material_states, "concentration": {row["entity_type"]: row for row in concentration},
        "priority_segments": priority_display, "stability": stability,
        "findings": make_findings(dev, channels, amount_bands, concentration, stability),
        "governance": {"discovery": "DEVELOPMENT only", "validation": "reserved for later model selection", "oot": "untouched except predefined split stability"},
        "artifact_counts": {"channel_rows": len(channels), "amount_band_rows": len(amount_bands), "mcc_rows": len(mcc), "state_rows": len(states), "city_rows": len(cities), "interaction_rows": len(interactions)},
    }
    validate_summary(summary)
    SUMMARY_PATH.write_text(json.dumps(json_safe(summary), indent=2), encoding="utf-8")
    print("PORTFOLIO_READY")


if __name__ == "__main__":
    main()
