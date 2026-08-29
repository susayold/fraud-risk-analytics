"""Execute the Part 3 aggregate portfolio analytics pipeline."""

from __future__ import annotations

import argparse
import csv
import json
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


def export_table(db: duckdb.DuckDBPyConnection, table: str, filename: str) -> list[dict[str, object]]:
    cursor = db.execute(f"SELECT * FROM {table}")
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


def write_top_entity_concentration(concentration: list[dict[str, object]]) -> None:
    fields = ["analysis_scope", "entity_type", "rank_band", "fraud_capture_share"]
    rows = []
    for row in concentration:
        for band in ("top_10", "top_100", "top_1pct", "top_5pct"):
            rows.append({"analysis_scope": row["analysis_scope"], "entity_type": row["entity_type"], "rank_band": band, "fraud_capture_share": row[f"{band}_fraud_share"]})
    with (REPORT_DIR / "top_entity_concentration.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)


def make_findings(dev: dict[str, object], channels: list[dict[str, object]], amount_bands: list[dict[str, object]], concentration: list[dict[str, object]]) -> list[dict[str, str]]:
    online = next((row for row in channels if str(row["segment_value"]).lower() == "online transaction"), None)
    top_amount = max(amount_bands, key=lambda row: float(row["fraud_lift"] or 0))
    top_entity = max(concentration, key=lambda row: float(row["top_1pct_fraud_share"] or 0))
    findings = []
    if online:
        findings.append({"title": "Online channel is elevated in Development", "evidence": f"{float(online['fraud_rate'])*100:.3f}% fraud rate; {float(online['fraud_lift']):.2f}x lift; {float(online['fraud_capture_share'])*100:.1f}% of fraud transactions.", "meaning": "Channel is both risk-elevated and material enough to warrant deeper behavioral analysis.", "next_action": "Test channel-specific velocity and amount-deviation questions in Part 4 using strict prior history."})
    findings.append({"title": "Risk is not the same as exposure", "evidence": f"Development contains {int(dev['transactions']):,} transactions and {int(dev['fraud_transactions']):,} fraud-labeled transactions; signed fraud amount share is {float(dev['fraud_amount_share'])*100:.3f}%.", "meaning": "Prevalence, fraud count and signed amount must be read together before prioritizing a segment.", "next_action": "Carry both count-based and amount-based views into later decision economics."})
    findings.append({"title": f"{top_amount['segment_value']} is the highest-lift amount band", "evidence": f"{float(top_amount['fraud_lift']):.2f}x Development lift with {int(top_amount['fraud_transactions']):,} fraud-labeled transactions.", "meaning": "The band is a descriptive hypothesis, not a production rule or loss estimate.", "next_action": "Test amount-context and card-history behavior in Part 4; do not finalize a threshold here."})
    findings.append({"title": f"Entity concentration is visible at the {top_entity['entity_type'].lower()} level", "evidence": f"The top 1% of {top_entity['entity_type'].lower()} entities account for {float(top_entity['top_1pct_fraud_share'])*100:.1f}% of fraud transactions; {int(top_entity['repeat_fraud_entities']):,} entities have repeated fraud labels.", "meaning": "Retrospective concentration motivates history features while remaining distinct from a point-in-time model feature.", "next_action": "Reconstruct prior entity history in Part 4 with timestamps strictly less than T0."})
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
    portfolio = export_table(db, "analytics.part3_portfolio_summary", "portfolio_summary.csv")
    monthly = export_table(db, "analytics.part3_monthly_fraud_trend", "monthly_fraud_trend.csv")
    yearly = export_table(db, "analytics.part3_yearly_fraud_trend", "yearly_fraud_trend.csv")
    channels = export_table(db, "analytics.part3_channel_risk", "channel_risk.csv")
    amount_bands = export_table(db, "analytics.part3_amount_band_risk", "amount_band_risk.csv")
    distributions = export_table(db, "analytics.part3_amount_distribution", "amount_distribution.csv")
    mcc = export_table(db, "analytics.part3_mcc_risk", "mcc_risk.csv")
    states = export_table(db, "analytics.part3_state_risk", "state_risk.csv")
    cities = export_table(db, "analytics.part3_merchant_city_risk", "merchant_city_risk.csv")
    users = export_table(db, "analytics.part3_user_concentration", "user_concentration.csv")
    cards = export_table(db, "analytics.part3_card_concentration", "card_concentration.csv")
    merchants = export_table(db, "analytics.part3_merchant_concentration", "merchant_concentration.csv")
    interactions = export_table(db, "analytics.part3_interaction_risk", "interaction_risk.csv")
    priority = export_table(db, "analytics.part3_segment_priority", "segment_priority.csv")
    stability = export_table(db, "analytics.part3_split_stability", "split_stability_summary.csv")
    concentration = users + cards + merchants
    write_top_entity_concentration(concentration)
    db.close()

    dev = next(row for row in portfolio if row["analysis_scope"] == "DEVELOPMENT_DISCOVERY")
    material_mcc = sorted((row for row in mcc if row["support_status"] == "SUFFICIENT"), key=lambda row: (-float(row["fraud_lift"] or 0), -int(row["fraud_transactions"] or 0)))[:10]
    material_states = sorted((row for row in states if row["support_status"] == "SUFFICIENT"), key=lambda row: (-float(row["fraud_capture_share"] or 0), -int(row["fraud_transactions"] or 0)))[:10]
    priority_display = sorted((row for row in priority if row["support_status"] == "SUFFICIENT"), key=lambda row: ({"PRIORITY_1": 0, "PRIORITY_2": 1, "MONITOR": 2, "LOW_PRIORITY": 3}[row["priority_class"]], -float(row["fraud_capture_share"] or 0)))[:12]
    summary = {
        "status": "PORTFOLIO_READY", "analysis_scope": "DEVELOPMENT_DISCOVERY", "development": dev,
        "portfolio_metrics": portfolio, "monthly_trend": monthly, "yearly_trend": yearly,
        "channel": channels, "amount_bands": amount_bands, "amount_distribution": distributions,
        "mcc": material_mcc, "geography": material_states, "concentration": {row["entity_type"]: row for row in concentration},
        "priority_segments": priority_display, "stability": stability,
        "findings": make_findings(dev, channels, amount_bands, concentration),
        "governance": {"discovery": "DEVELOPMENT only", "validation": "reserved for later model selection", "oot": "untouched except predefined split stability"},
        "artifact_counts": {"channel_rows": len(channels), "amount_band_rows": len(amount_bands), "mcc_rows": len(mcc), "state_rows": len(states), "city_rows": len(cities), "interaction_rows": len(interactions)},
    }
    SUMMARY_PATH.write_text(json.dumps(json_safe(summary), indent=2), encoding="utf-8")
    print("PORTFOLIO_READY")


if __name__ == "__main__":
    main()
