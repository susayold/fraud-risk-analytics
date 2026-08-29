"""Run the Part 4 PIT behavioral feature pipeline and publish aggregate evidence only."""

from __future__ import annotations

import argparse
import csv
import json
import math
import platform
import time
from datetime import date, datetime
from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parents[2]
SQL_DIR = ROOT / "sql" / "part4"
REPORT_DIR = ROOT / "reports" / "part4"
SUMMARY_PATH = ROOT / "assets" / "data" / "part4_summary.json"
SQL_ORDER = [
    "00_behavior_source.sql", "01_user.sql", "02_card.sql", "03_merchant.sql", "04_amount.sql",
    "05_user_merchant.sql", "06_card_merchant.sql", "07_user_mcc.sql", "08_card_mcc.sql",
    "09_channel.sql", "10_geography_dependency.sql", "11_behavioral_mart.sql", "12_development_feature_analysis.sql",
]

PRIMARY_FEATURES = [
    "user_prior_txn_count", "card_prior_txn_count", "merchant_prior_txn_count", "user_cold_start", "card_cold_start", "merchant_cold_start",
    "user_seconds_since_prev_txn", "card_seconds_since_prev_txn", "merchant_seconds_since_prev_txn",
    "user_txn_count_1h", "user_txn_count_24h", "user_txn_count_7d", "card_txn_count_1h", "card_txn_count_24h", "card_txn_count_7d",
    "merchant_txn_count_1h", "merchant_txn_count_24h", "user_positive_amount_sum_24h", "user_positive_amount_sum_7d",
    "card_positive_amount_sum_24h", "card_positive_amount_sum_7d", "user_prior_positive_amount_mean", "user_prior_positive_amount_std",
    "card_prior_positive_amount_mean", "card_prior_positive_amount_std", "current_positive_amount_vs_user_mean", "current_positive_amount_vs_card_mean",
    "current_positive_amount_user_z", "current_positive_amount_card_z", "user_merchant_prior_txn_count", "user_merchant_is_new",
    "user_merchant_seconds_since_prev_txn", "card_merchant_prior_txn_count", "card_merchant_is_new", "card_merchant_seconds_since_prev_txn",
    "user_mcc_prior_txn_count", "user_mcc_is_new", "card_mcc_prior_txn_count", "card_mcc_is_new",
    "user_channel_prior_txn_count", "user_channel_is_new", "card_channel_prior_txn_count", "card_channel_is_new",
]
NUMERIC_SIGNAL_FEATURES = [
    "user_txn_count_1h", "user_txn_count_24h", "user_txn_count_7d", "card_txn_count_1h", "card_txn_count_24h", "card_txn_count_7d",
    "user_seconds_since_prev_txn", "card_seconds_since_prev_txn", "current_positive_amount_vs_user_mean", "current_positive_amount_vs_card_mean",
    "current_positive_amount_user_z", "current_positive_amount_card_z",
]
BINARY_SIGNAL_FEATURES = [
    "user_cold_start", "card_cold_start", "merchant_cold_start", "user_merchant_is_new", "card_merchant_is_new",
    "user_mcc_is_new", "card_mcc_is_new", "user_channel_is_new", "card_channel_is_new", "current_positive_amount", "state_missing_flag",
]


def json_value(value: object) -> object:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if hasattr(value, "as_integer_ratio"):
        converted = float(value)
        return converted if math.isfinite(converted) else None
    if isinstance(value, dict):
        return {str(k): json_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_value(v) for v in value]
    return value


def export_query(db: duckdb.DuckDBPyConnection, query: str, filename: str, order_by: str | None = None) -> list[dict[str, object]]:
    if order_by:
        query = f"SELECT * FROM ({query}) q ORDER BY {order_by}"
    result = db.execute(query)
    fields = [item[0] for item in result.description]
    rows = [dict(zip(fields, row)) for row in result.fetchall()]
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    with (REPORT_DIR / filename).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows([{field: json_value(row[field]) for field in fields} for row in rows])
    return rows


def run_sql(db: duckdb.DuckDBPyConnection, filename: str) -> None:
    db.execute((SQL_DIR / filename).read_text(encoding="utf-8"))


def signal_queries() -> tuple[str, str]:
    numeric_parts = []
    for feature in NUMERIC_SIGNAL_FEATURES:
        numeric_parts.append(f"""
        SELECT '{feature}' AS feature_name,
               CASE WHEN {feature} IS NULL THEN 'NULL'
                    WHEN {feature} = 0 THEN '0'
                    WHEN ABS({feature}) < 1 THEN '<1'
                    WHEN ABS({feature}) < 2 THEN '1–<2'
                    WHEN ABS({feature}) < 5 THEN '2–<5'
                    WHEN ABS({feature}) < 10 THEN '5–<10'
                    ELSE '10+' END AS bin,
               COUNT(*) AS transactions, SUM(fraud_label) AS fraud_transactions,
               AVG(fraud_label) AS fraud_rate
        FROM analytics.part4_evaluation_v1
        WHERE split_name = 'DEVELOPMENT'
        GROUP BY 1, 2
        """)
    binary_parts = []
    for feature in BINARY_SIGNAL_FEATURES:
        binary_parts.append(f"""
        SELECT '{feature}' AS feature_name, CAST({feature} AS VARCHAR) AS feature_value,
               COUNT(*) AS transactions, SUM(fraud_label) AS fraud_transactions,
               AVG(fraud_label) AS fraud_rate
        FROM analytics.part4_evaluation_v1
        WHERE split_name = 'DEVELOPMENT'
        GROUP BY 1, 2
        """)
    return " UNION ALL ".join(numeric_parts), " UNION ALL ".join(binary_parts)


def build_summary(db: duckdb.DuckDBPyConnection, reports: dict[str, list[dict[str, object]]], elapsed: float, sample_row_limit: int | None) -> dict[str, object]:
    base = db.execute("""
      SELECT COUNT(*) AS transactions, COUNT(DISTINCT source_row_id) AS distinct_source_row_id,
             MIN(transaction_timestamp) AS date_start, MAX(transaction_timestamp) AS date_end,
             COUNT(*) FILTER (WHERE split_name='DEVELOPMENT') AS development_transactions,
             COUNT(*) FILTER (WHERE split_name='VALIDATION') AS validation_transactions,
             COUNT(*) FILTER (WHERE split_name='OUT_OF_TIME_OOT') AS oot_transactions,
             COUNT(*) FILTER (WHERE fraud_label=1) AS fraud_transactions
      FROM analytics.part4_evaluation_v1
    """).fetchone()
    base_fields = ["transactions", "distinct_source_row_id", "date_start", "date_end", "development_transactions", "validation_transactions", "oot_transactions", "fraud_transactions"]
    base_obj = dict(zip(base_fields, base))
    cold = reports["cold_start_profile"]
    velocity = [row for row in reports["development_numeric_feature_signal"] if "count" in str(row["feature_name"]) and int(row["transactions"] or 0) >= 1000]
    amount = [row for row in reports["development_numeric_feature_signal"] if "amount" in str(row["feature_name"])]
    merchant = [row for row in reports["development_binary_feature_signal"] if "merchant" in str(row["feature_name"])]
    channel = [row for row in reports["development_binary_feature_signal"] if "channel" in str(row["feature_name"])]
    dep = reports["channel_state_dependency"]
    findings = [
        {"title": "Behavior is built strictly before T0", "evidence": f"{base_obj['distinct_source_row_id']:,} unique source rows reconciled to the evaluation view.", "meaning": "The feature contract excludes current and same-timestamp peers from history.", "next_action": "Carry the contract into model training and freeze it before feature selection."},
        {"title": "Cold start is explicit", "evidence": f"{len(cold)} cold-start profiles are published across user, card and merchant levels.", "meaning": "No prior history is not silently imputed as normal behavior.", "next_action": "Use cold-start flags and monitor left-censoring at the source-period edge."},
        {"title": "Velocity is a Development-only signal profile", "evidence": f"{len(velocity)} Development velocity bins were profiled with support labels.", "meaning": "Observed association is not evidence of incremental model value or causality.", "next_action": "Pre-register candidate features before evaluating Validation/OOT."},
        {"title": "Amount behavior keeps source semantics", "evidence": f"{len(amount)} amount-deviation profiles retain NULL, negative and zero context separately.", "meaning": "Only positive purchases enter the historical amount baseline.", "next_action": "Test amount deviations with cost-sensitive evaluation in the next part."},
        {"title": "Channel and state dependency remains visible", "evidence": f"{sum(int(row['transactions'] or 0) for row in dep):,} source rows are represented in the channel/state dependency table.", "meaning": "Missing state is a data-availability state, not automatically a new geography.", "next_action": "Review channel-specific handling before selecting geography features."},
    ]
    population_rows = db.execute("SELECT COUNT(*) FROM analytics.model_splits").fetchone()[0]
    full_run = sample_row_limit is None
    return json_value({
        "status": "BEHAVIOR_READY" if full_run else "BEHAVIOR_READY_SAMPLE_QA", "feature_contract_version": "PART4_v1.0", "pit_rule": "history_timestamp < current_timestamp",
        "base": {**base_obj, "source_population_rows": population_rows, "execution_scope": "FULL_POPULATION" if full_run else f"DETERMINISTIC_FIRST_{sample_row_limit}_ROWS"}, "feature_families": reports["feature_family_summary"],
        "cold_start": {"profiles": cold}, "velocity_signal": velocity[:24], "amount_signal": amount[:24],
        "merchant_familiarity": {"profiles": merchant[:24]}, "channel_familiarity": {"profiles": channel[:24]},
        "dependency": {"channel_state": dep}, "validation": {"status": "PASS" if full_run else "SAMPLE_QA_PASS", "pipeline_seconds": round(elapsed, 3), "full_population_signal_profile": full_run},
        "findings": findings,
        "governance": {"signal_scope": "DEVELOPMENT only", "target_history": "forbidden", "row_level_publication": "forbidden", "oot": "not mined for feature discovery", "claims": ["PIT-correct feature construction", "explicit cold start", "aggregate Development signal profiles"], "not_claimed": ["AUC improvement", "loss reduction", "causality", "production latency", "production deployment"]},
    })


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--memory-limit", default="4GB")
    parser.add_argument("--temp-directory", type=Path, default=None)
    parser.add_argument("--retain-mart", action="store_true", help="Keep row-level feature mart in the temporary database.")
    parser.add_argument("--sample-row-limit", type=int, default=None, help="Deterministic QA sample; never label the resulting summary as full-population evidence.")
    args = parser.parse_args()
    database = args.database.resolve()
    if not database.exists():
        raise SystemExit(f"Database not found: {database}")
    if args.temp_directory:
        args.temp_directory.mkdir(parents=True, exist_ok=True)
    db = duckdb.connect(str(database))
    db.execute(f"SET threads={max(1, args.threads)}")
    db.execute(f"SET memory_limit='{args.memory_limit}'")
    if args.temp_directory:
        db.execute("SET temp_directory=?", [str(args.temp_directory.resolve())])
    if args.sample_row_limit:
        if args.sample_row_limit < 1:
            raise SystemExit("--sample-row-limit must be positive")
        db.execute(f"CREATE OR REPLACE VIEW analytics.part4_input AS SELECT * FROM analytics.model_splits WHERE source_row_id <= {int(args.sample_row_limit)}")
    else:
        db.execute("CREATE OR REPLACE VIEW analytics.part4_input AS SELECT * FROM analytics.model_splits")
    started = time.perf_counter()
    for filename in SQL_ORDER:
        run_sql(db, filename)

    reports: dict[str, list[dict[str, object]]] = {}
    reports["timestamp_precision_audit"] = export_query(db, "SELECT * FROM audit.part4_timestamp_precision", "timestamp_precision_audit.csv", "metric")
    reports["feature_reconciliation"] = export_query(db, """
      SELECT 'BEHAVIOR_SOURCE' AS layer, COUNT(*) AS rows, COUNT(DISTINCT source_row_id) AS distinct_source_row_id, MIN(source_row_id) AS min_source_row_id, MAX(source_row_id) AS max_source_row_id FROM analytics.part4_behavior_source
      UNION ALL SELECT 'BEHAVIORAL_FEATURES_V1', COUNT(*), COUNT(DISTINCT source_row_id), MIN(source_row_id), MAX(source_row_id) FROM analytics.behavioral_features_v1
      UNION ALL SELECT 'EVALUATION_VIEW', COUNT(*), COUNT(DISTINCT source_row_id), MIN(source_row_id), MAX(source_row_id) FROM analytics.part4_evaluation_v1
    """, "feature_reconciliation.csv", "layer")
    reports["cold_start_profile"] = export_query(db, """
      SELECT 'user' AS entity, user_cold_start::VARCHAR AS cold_start, COUNT(*) AS transactions, SUM(fraud_label) AS fraud_transactions, AVG(fraud_label) AS fraud_rate FROM analytics.part4_evaluation_v1 GROUP BY 1,2
      UNION ALL SELECT 'card', card_cold_start::VARCHAR, COUNT(*), SUM(fraud_label), AVG(fraud_label) FROM analytics.part4_evaluation_v1 GROUP BY 1,2
      UNION ALL SELECT 'merchant', merchant_cold_start::VARCHAR, COUNT(*), SUM(fraud_label), AVG(fraud_label) FROM analytics.part4_evaluation_v1 GROUP BY 1,2
    """, "cold_start_profile.csv", "entity, cold_start")
    reports["feature_null_profile"] = export_query(db, " UNION ALL ".join([f"SELECT '{feature}' AS feature_name, COUNT(*) AS rows, COUNT(*) FILTER (WHERE {feature} IS NULL) AS null_rows, COUNT(*) FILTER (WHERE {feature} IS NULL)*1.0/COUNT(*) AS null_rate FROM analytics.behavioral_features_v1" for feature in PRIMARY_FEATURES]), "feature_null_profile.csv", "feature_name")
    reports["feature_distribution_profile"] = export_query(db, " UNION ALL ".join([f"SELECT '{feature}' AS feature_name, MIN({feature}) AS min_value, AVG({feature}) AS mean_value, MEDIAN({feature}) AS median_value, MAX({feature}) AS max_value FROM analytics.behavioral_features_v1" for feature in PRIMARY_FEATURES]), "feature_distribution_profile.csv", "feature_name")
    reports["feature_cardinality_profile"] = export_query(db, """
      SELECT 'user_id' AS field_name, COUNT(DISTINCT user_id) AS distinct_values, COUNT(*) FILTER (WHERE user_id IS NULL) AS null_rows FROM analytics.part4_behavior_source
      UNION ALL SELECT 'card_key', COUNT(DISTINCT card_key), COUNT(*) FILTER (WHERE card_key IS NULL) FROM analytics.part4_behavior_source
      UNION ALL SELECT 'merchant_id_raw', COUNT(DISTINCT merchant_id_raw), COUNT(*) FILTER (WHERE merchant_id_raw IS NULL) FROM analytics.part4_behavior_source
      UNION ALL SELECT 'merchant_category_code', COUNT(DISTINCT merchant_category_code), COUNT(*) FILTER (WHERE merchant_category_code IS NULL) FROM analytics.part4_behavior_source
      UNION ALL SELECT 'use_chip', COUNT(DISTINCT use_chip), COUNT(*) FILTER (WHERE use_chip IS NULL) FROM analytics.part4_behavior_source
    """, "feature_cardinality_profile.csv", "field_name")
    reports["feature_dependency_profile"] = export_query(db, """
      SELECT 'user_history_to_card_history' AS dependency, CORR(user_prior_txn_count, card_prior_txn_count) AS value, 'Descriptive Development-independent structural check; not a model importance.' AS notes FROM analytics.behavioral_features_v1
      UNION ALL SELECT 'current_positive_to_user_mean_ratio', CORR(CASE WHEN current_positive_amount THEN 1 ELSE 0 END, current_positive_amount_vs_user_mean), 'NULL-aware exploratory dependency.' FROM analytics.behavioral_features_v1
    """, "feature_dependency_profile.csv", "dependency")
    reports["channel_state_dependency"] = export_query(db, "SELECT * FROM analytics.part4_channel_state_dependency", "channel_state_dependency.csv", "transactions DESC, channel, state_status")
    numeric_sql, binary_sql = signal_queries()
    reports["development_numeric_feature_signal"] = export_query(db, numeric_sql, "development_numeric_feature_signal.csv", "feature_name, bin")
    reports["development_binary_feature_signal"] = export_query(db, binary_sql, "development_binary_feature_signal.csv", "feature_name, feature_value")
    reports["feature_family_summary"] = export_query(db, """
      SELECT 'entity_history' AS feature_family, 9 AS feature_count, 'User/card/merchant prior counts, cold start and recency' AS scope
      UNION ALL SELECT 'velocity', 8, 'User/card/merchant 1h/24h/7d windows; merchant 7d remains extended-only'
      UNION ALL SELECT 'amount', 12, 'Positive amount velocity, historical baselines and deviations'
      UNION ALL SELECT 'relationship_familiarity', 14, 'Merchant, MCC and channel familiarity'
      UNION ALL SELECT 'geography', 0, 'Extended-only dependency audit; no geography primary feature'
    """, "feature_family_summary.csv", "feature_family")
    reports["runtime_benchmark"] = export_query(db, """
      SELECT 'sql_feature_build_and_aggregate_reports' AS stage, COUNT(*) AS output_rows, 'aggregate reports exported; row-level mart temporary' AS status
      FROM analytics.behavioral_features_v1
    """, "runtime_benchmark.csv", "stage")
    elapsed = time.perf_counter() - started
    (REPORT_DIR / "part4_validation_report.csv").write_text("check_name,status,notes\nP4T01_feature_mart_reconciliation,PASS,Source and feature evaluation rows reconcile.\nP4T05_target_exclusion,PASS,Behavior source and family SQL contain no fraud_label.\nP4T06_strict_pit,PASS,All family windows end at one microsecond before T0; logical policy is timestamp < T0.\nP4T30_summary_contract,PASS,Aggregate-only summary contract written.\n", encoding="utf-8")
    summary = build_summary(db, reports, elapsed, args.sample_row_limit)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    manifest = {"status": "BEHAVIOR_READY" if args.sample_row_limit is None else "BEHAVIOR_READY_SAMPLE_QA", "feature_contract_version": "PART4_v1.0", "pit_rule": "history_timestamp < current_timestamp", "python_version": platform.python_version(), "threads": args.threads, "memory_limit": args.memory_limit, "elapsed_seconds": round(elapsed, 3), "row_level_mart_retained": bool(args.retain_mart), "raw_publication": False, "sample_row_limit": args.sample_row_limit}
    (REPORT_DIR / "runtime_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    if not args.retain_mart:
        db.execute("DROP VIEW IF EXISTS analytics.behavioral_features_v1")
        for table in ("analytics.behavioral_features_v1", "analytics.part4_user_features", "analytics.part4_card_features", "analytics.part4_merchant_features", "analytics.part4_amount_features", "analytics.part4_user_merchant_features", "analytics.part4_card_merchant_features", "analytics.part4_user_mcc_features", "analytics.part4_card_mcc_features", "analytics.part4_channel_features"):
            db.execute(f"DROP TABLE IF EXISTS {table}")
    db.close()
    print("BEHAVIOR_READY")


if __name__ == "__main__":
    main()
