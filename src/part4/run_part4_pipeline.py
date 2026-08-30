"""Run Part 4 offline and publish aggregate evidence only.

The pipeline is fail-closed: validation owns the validation report and the
public summary is written only after the current run passes that validator.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import platform
import subprocess
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[2]
SQL_DIR = ROOT / "sql" / "part4"
REPORT_DIR = ROOT / "reports" / "part4"
SUMMARY_PATH = ROOT / "assets" / "data" / "part4_summary.json"
CONTRACT_VERSION = "PART4_v1.1"
PIT_VERSION = "P4_PIT_v1.0"
BINS_VERSION = "P4_BINS_v1.0"
VALIDATION_VERSION = "P4_VALIDATION_v1.1"
FRONTEND_VERSION = "P4_FRONTEND_v1.1"
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
    "merchant_txn_count_1h", "merchant_txn_count_24h", "user_seconds_since_prev_txn", "card_seconds_since_prev_txn", "merchant_seconds_since_prev_txn",
    "current_positive_amount_vs_user_mean", "current_positive_amount_vs_card_mean", "current_positive_amount_user_z", "current_positive_amount_card_z",
]
BINARY_SIGNAL_FEATURES = [
    "user_cold_start", "card_cold_start", "merchant_cold_start", "user_merchant_is_new", "card_merchant_is_new",
    "user_mcc_is_new", "card_mcc_is_new", "user_channel_is_new", "card_channel_is_new", "current_positive_amount", "state_missing_flag",
]


def json_value(value: object) -> object:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, bool) or isinstance(value, int):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {str(k): json_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_value(v) for v in value]
    return value


def clean_generated_outputs() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    for path in list(REPORT_DIR.glob("*.csv")) + list(REPORT_DIR.glob("*.json")):
        path.unlink(missing_ok=True)
    SUMMARY_PATH.unlink(missing_ok=True)


def export_query(db: duckdb.DuckDBPyConnection, query: str, filename: str, order_by: str | None = None) -> list[dict[str, object]]:
    if order_by:
        query = f"SELECT * FROM ({query}) q ORDER BY {order_by}"
    result = db.execute(query)
    fields = [item[0] for item in result.description]
    rows = [dict(zip(fields, row)) for row in result.fetchall()]
    with (REPORT_DIR / filename).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader()
        writer.writerows([{field: json_value(row[field]) for field in fields} for row in rows])
    return rows


def run_sql(db: duckdb.DuckDBPyConnection, filename: str) -> None:
    db.execute((SQL_DIR / filename).read_text(encoding="utf-8"))


def bin_case(feature: str) -> str:
    if "seconds_since" in feature:
        return "CASE WHEN {f} IS NULL THEN 0 WHEN {f} < 60 THEN 1 WHEN {f} < 300 THEN 2 WHEN {f} < 1800 THEN 3 WHEN {f} < 21600 THEN 4 WHEN {f} < 86400 THEN 5 WHEN {f} < 604800 THEN 6 WHEN {f} < 2592000 THEN 7 ELSE 8 END".format(f=feature)
    if "_vs_" in feature:
        return "CASE WHEN {f} IS NULL THEN 0 WHEN {f} < 0.25 THEN 1 WHEN {f} < 0.5 THEN 2 WHEN {f} < 1 THEN 3 WHEN {f} < 2 THEN 4 WHEN {f} < 5 THEN 5 WHEN {f} < 10 THEN 6 ELSE 7 END".format(f=feature)
    if feature.endswith("_z"):
        return "CASE WHEN {f} IS NULL THEN 0 WHEN {f} < -2 THEN 1 WHEN {f} < -1 THEN 2 WHEN {f} < 1 THEN 3 WHEN {f} < 2 THEN 4 WHEN {f} < 3 THEN 5 WHEN {f} < 5 THEN 6 ELSE 7 END".format(f=feature)
    return "CASE WHEN {f} IS NULL THEN 0 WHEN {f} = 0 THEN 0 WHEN {f} = 1 THEN 1 WHEN {f} < 5 THEN 2 WHEN {f} < 10 THEN 3 WHEN {f} < 20 THEN 4 ELSE 5 END".format(f=feature)


def bin_label(feature: str) -> str:
    if "seconds_since" in feature:
        return "CASE {f} WHEN 0 THEN 'NULL' WHEN 1 THEN '<1 minute' WHEN 2 THEN '1–5 minutes' WHEN 3 THEN '5–30 minutes' WHEN 4 THEN '30 minutes–6 hours' WHEN 5 THEN '6–24 hours' WHEN 6 THEN '1–7 days' WHEN 7 THEN '7–30 days' ELSE '30+ days' END".format(f=bin_case(feature))
    if "_vs_" in feature:
        return "CASE {f} WHEN 0 THEN 'NULL' WHEN 1 THEN '<0.25x' WHEN 2 THEN '0.25–0.5x' WHEN 3 THEN '0.5–1x' WHEN 4 THEN '1–2x' WHEN 5 THEN '2–5x' WHEN 6 THEN '5–10x' ELSE '10x+' END".format(f=bin_case(feature))
    if feature.endswith("_z"):
        return "CASE {f} WHEN 0 THEN 'NULL' WHEN 1 THEN 'z < -2' WHEN 2 THEN '-2 ≤ z < -1' WHEN 3 THEN '-1 ≤ z < 1' WHEN 4 THEN '1 ≤ z < 2' WHEN 5 THEN '2 ≤ z < 3' WHEN 6 THEN '3 ≤ z < 5' ELSE 'z ≥ 5' END".format(f=bin_case(feature))
    return "CASE {f} WHEN 0 THEN '0' WHEN 1 THEN '1' WHEN 2 THEN '2–4' WHEN 3 THEN '5–9' WHEN 4 THEN '10–19' ELSE '20+' END".format(f=bin_case(feature))


def signal_queries() -> tuple[str, str]:
    numeric_parts = []
    for feature in NUMERIC_SIGNAL_FEATURES:
        order_expr = bin_case(feature); label_expr = bin_label(feature)
        numeric_parts.append(f"SELECT '{feature}' feature_name, {order_expr} bin_order, {label_expr} bin, NULL::VARCHAR feature_value, COUNT(*) transactions, SUM(fraud_label) fraud_transactions, AVG(fraud_label) fraud_rate, 1000 support_threshold, CASE WHEN COUNT(*) >= 1000 THEN 'INTERPRETABLE' ELSE 'LOW_SUPPORT' END support_status FROM analytics.part4_evaluation_v1 WHERE split_name = 'DEVELOPMENT' GROUP BY 1,2,3")
    binary_parts = []
    for feature in BINARY_SIGNAL_FEATURES:
        binary_parts.append(f"SELECT '{feature}' feature_name, CAST({feature} AS INTEGER) bin_order, CAST({feature} AS VARCHAR) bin, CAST({feature} AS VARCHAR) feature_value, COUNT(*) transactions, SUM(fraud_label) fraud_transactions, AVG(fraud_label) fraud_rate, 1000 support_threshold, CASE WHEN COUNT(*) >= 1000 THEN 'INTERPRETABLE' ELSE 'LOW_SUPPORT' END support_status FROM analytics.part4_evaluation_v1 WHERE split_name = 'DEVELOPMENT' GROUP BY 1,2,3,4")
    return " UNION ALL ".join(numeric_parts), " UNION ALL ".join(binary_parts)


def size_mb(path: Path | None) -> float:
    if not path or not path.exists():
        return 0.0
    return round(sum(p.stat().st_size for p in path.rglob("*") if p.is_file()) / 1048576, 3)


def write_runtime_profile(stage_times: list[tuple[str, float, int]], temp_directory: Path | None, args: argparse.Namespace) -> None:
    with (REPORT_DIR / "runtime_profile.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle); writer.writerow(["stage", "rows", "elapsed_seconds", "peak_temp_storage_mb", "memory_limit", "threads", "status"])
        for stage, elapsed, rows in stage_times:
            writer.writerow([stage, rows, round(elapsed, 3), size_mb(temp_directory), args.memory_limit, args.threads, "PASS"])


def build_summary(db: duckdb.DuckDBPyConnection, reports: dict[str, list[dict[str, object]]], elapsed: float, args: argparse.Namespace, run_meta: dict[str, object]) -> dict[str, object]:
    base_fields = ["transactions", "distinct_source_row_id", "date_start", "date_end", "development_transactions", "validation_transactions", "oot_transactions", "fraud_transactions"]
    base = dict(zip(base_fields, db.execute("SELECT COUNT(*), COUNT(DISTINCT source_row_id), MIN(transaction_timestamp), MAX(transaction_timestamp), COUNT(*) FILTER (WHERE split_name='DEVELOPMENT'), COUNT(*) FILTER (WHERE split_name='VALIDATION'), COUNT(*) FILTER (WHERE split_name='OUT_OF_TIME_OOT'), COUNT(*) FILTER (WHERE fraud_label=1) FROM analytics.part4_evaluation_v1").fetchone()))
    pop = db.execute("SELECT COUNT(*) FROM analytics.model_splits").fetchone()[0]
    sample = args.sample_row_limit is not None
    scope = "DETERMINISTIC_QA_EXECUTION_SLICE" if sample else "FULL_POPULATION"
    coverage_rows = []
    coverage_path = REPORT_DIR / "sample_history_coverage.csv"
    if coverage_path.exists():
        with coverage_path.open(encoding="utf-8", newline="") as handle:
            coverage_rows = list(csv.DictReader(handle))
    interpretable = lambda row: row.get("support_status") == "INTERPRETABLE"
    velocity = [row for row in reports["development_numeric_feature_signal"] if "count" in str(row["feature_name"]) and interpretable(row)]
    amount = [row for row in reports["development_numeric_feature_signal"] if ("amount" in str(row["feature_name"])) and interpretable(row)]
    merchant = [row for row in reports["development_binary_feature_signal"] if "merchant" in str(row["feature_name"]) and interpretable(row)]
    channel = [row for row in reports["development_binary_feature_signal"] if "channel" in str(row["feature_name"]) and interpretable(row)]
    findings = [
        {"title": "Behavior is built strictly before T0", "evidence": f"{base['distinct_source_row_id']:,} unique source rows reconcile through the evaluation view.", "meaning": "The contract excludes current and same-timestamp peers from history.", "next_action": "Carry the PIT contract into Part 5 model training."},
        {"title": "Cold start is explicit", "evidence": f"{len(reports['cold_start_profile'])} cold-start profiles are published across user, card and merchant levels.", "meaning": "No prior history is not silently imputed as normal behavior.", "next_action": "Monitor left-censoring at the source-period edge."},
        {"title": "Signal bins are feature-specific", "evidence": f"{len(velocity) + len(amount)} interpretable Development bins are available in this execution scope.", "meaning": "Counts, seconds, ratios and signed z-scores use separate units and bins.", "next_action": "Freeze candidate features before Validation/OOT evaluation."},
        {"title": "Amount behavior keeps source semantics", "evidence": f"{len(amount)} interpretable amount-deviation bins preserve positive-only baselines.", "meaning": "Negative and zero amounts do not silently enter purchase history.", "next_action": "Evaluate amount deviations with cost-sensitive metrics in Part 5."},
        {"title": "Low support remains visible", "evidence": "Every signal row carries INTERPRETABLE or LOW_SUPPORT status at threshold 1,000.", "meaning": "Sparse bins are descriptive only and are excluded from headline findings.", "next_action": "Review support after any full-population rerun."},
    ]
    return json_value({
        "status": "BEHAVIOR_READY_SAMPLE_QA" if sample else "BEHAVIOR_READY",
        "lock_status": "NOT_LOCKED",
        "feature_contract_version": CONTRACT_VERSION,
        "pit_contract_version": PIT_VERSION,
        "signal_bin_contract_version": BINS_VERSION,
        "validation_contract_version": VALIDATION_VERSION,
        "frontend_contract_version": FRONTEND_VERSION,
        "pit_rule": "history_timestamp < current_timestamp",
        "base": {**base, "source_population_rows": pop, "execution_scope": scope},
        "execution": {"scope": scope, "rows": base["transactions"], "source_population_rows": pop, "sampling_method": "source_row_id_prefix" if sample else "none", "representative_sample_claim": False, "full_population_feature_run": not sample, "sql_fixture_pass": True, "semantic_invariants_pass": True, "entity_complete_qa_pass": False, "history_coverage_status": coverage_rows[0].get("status") if coverage_rows else "NOT_AVAILABLE"},
        "feature_families": reports["feature_family_summary"],
        "cold_start": {"profiles": reports["cold_start_profile"]},
        "velocity_signal": velocity[:24], "amount_signal": amount[:24],
        "merchant_familiarity": {"profiles": merchant[:24]}, "channel_familiarity": {"profiles": channel[:24]},
        "dependency": {"channel_state": reports["channel_state_dependency"]},
        "validation": {"status": "PASS", "contract_version": VALIDATION_VERSION, "pipeline_seconds": round(elapsed, 3), "full_population_signal_profile": not sample},
        "signal_profile": {"source": "DEVELOPMENT", "execution_scope": "QA_SLICE" if sample else "FULL_POPULATION", "used_for_feature_discovery": True, "validation_mined": False, "oot_mined": False, "performance_claim": False},
        "claim_boundary": {"full_population_behavior_signal_claimed": not sample, "representative_sample_claimed": False, "model_performance_claimed": False, "causality_claimed": False, "production_latency_claimed": False},
        "findings": findings,
        "governance": {"signal_scope": "DEVELOPMENT only", "target_history": "forbidden", "row_level_publication": "forbidden", "claims": ["PIT-correct feature construction", "explicit cold start", "feature-specific descriptive Development bins"], "not_claimed": ["full-population behavioral signal" if sample else "", "AUC improvement", "loss reduction", "causality", "production latency", "production deployment"]},
        "run": run_meta,
    })


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--memory-limit", default="4GB")
    parser.add_argument("--temp-directory", type=Path)
    parser.add_argument("--retain-mart", action="store_true")
    parser.add_argument("--sample-row-limit", type=int)
    parser.add_argument("--clean-generated", action="store_true", help="Remove only generated Part 4 reports and summary before running.")
    args = parser.parse_args()
    if args.sample_row_limit is not None and args.sample_row_limit < 1:
        raise SystemExit("--sample-row-limit must be positive")
    database = args.database.resolve()
    if not database.exists():
        raise SystemExit(f"Database not found: {database}")
    if args.clean_generated:
        clean_generated_outputs()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    if args.temp_directory:
        args.temp_directory.mkdir(parents=True, exist_ok=True)
    run_id = f"P4-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    git_commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False).stdout.strip() or "UNKNOWN"
    run_meta = {"run_id": run_id, "git_commit": git_commit, "run_timestamp_utc": datetime.now(timezone.utc).isoformat(), "feature_contract_version": CONTRACT_VERSION, "pit_contract_version": PIT_VERSION, "signal_bin_contract_version": BINS_VERSION, "validation_contract_version": VALIDATION_VERSION, "frontend_contract_version": FRONTEND_VERSION, "database_source": "temporary offline database (not published)", "threads": args.threads, "memory_limit": args.memory_limit, "sample_row_limit": args.sample_row_limit}
    db = duckdb.connect(str(database)); db.execute(f"SET threads={max(1, args.threads)}"); db.execute(f"SET memory_limit='{args.memory_limit}'"); db.execute("SET preserve_insertion_order=false")
    if args.temp_directory:
        db.execute("SET temp_directory=?", [str(args.temp_directory.resolve())])
    input_clause = f"WHERE source_row_id <= {int(args.sample_row_limit)}" if args.sample_row_limit is not None else ""
    db.execute(f"CREATE OR REPLACE VIEW analytics.part4_input AS SELECT * FROM analytics.model_splits {input_clause}")
    started = time.perf_counter(); stage_times: list[tuple[str, float, int]] = []
    for filename in SQL_ORDER:
        stage_start = time.perf_counter(); run_sql(db, filename); stage_times.append((filename, time.perf_counter() - stage_start, int(db.execute("SELECT COUNT(*) FROM analytics.part4_behavior_source").fetchone()[0]) if filename != "00_behavior_source.sql" else int(db.execute("SELECT COUNT(*) FROM analytics.part4_behavior_source").fetchone()[0])))
    reports: dict[str, list[dict[str, object]]] = {}
    reports["timestamp_precision_audit"] = export_query(db, "SELECT * FROM audit.part4_timestamp_precision", "timestamp_precision_audit.csv", "metric")
    reports["cold_start_profile"] = export_query(db, "SELECT 'user' entity, user_cold_start::VARCHAR cold_start, COUNT(*) transactions, SUM(fraud_label) fraud_transactions, AVG(fraud_label) fraud_rate FROM analytics.part4_evaluation_v1 GROUP BY 1,2 UNION ALL SELECT 'card', card_cold_start::VARCHAR, COUNT(*), SUM(fraud_label), AVG(fraud_label) FROM analytics.part4_evaluation_v1 GROUP BY 1,2 UNION ALL SELECT 'merchant', merchant_cold_start::VARCHAR, COUNT(*), SUM(fraud_label), AVG(fraud_label) FROM analytics.part4_evaluation_v1 GROUP BY 1,2", "cold_start_profile.csv", "entity, cold_start")
    reports["feature_null_profile"] = export_query(db, " UNION ALL ".join([f"SELECT '{feature}' feature_name, COUNT(*) row_count, COUNT(*) FILTER (WHERE {feature} IS NULL) null_rows, COUNT(*) FILTER (WHERE {feature} IS NULL)*1.0/COUNT(*) null_rate FROM analytics.behavioral_features_v1" for feature in PRIMARY_FEATURES]), "feature_null_profile.csv", "feature_name")
    reports["feature_distribution_profile"] = export_query(db, " UNION ALL ".join([f"SELECT '{feature}' feature_name, MIN({feature}) min_value, AVG({feature}) mean_value, MEDIAN({feature}) median_value, MAX({feature}) max_value FROM analytics.behavioral_features_v1" for feature in PRIMARY_FEATURES]), "feature_distribution_profile.csv", "feature_name")
    reports["feature_cardinality_profile"] = export_query(db, "SELECT 'user_id' field_name, COUNT(DISTINCT user_id) distinct_values, COUNT(*) FILTER (WHERE user_id IS NULL) null_rows FROM analytics.part4_behavior_source UNION ALL SELECT 'card_key', COUNT(DISTINCT card_key), COUNT(*) FILTER (WHERE card_key IS NULL) FROM analytics.part4_behavior_source UNION ALL SELECT 'merchant_id_raw', COUNT(DISTINCT merchant_id_raw), COUNT(*) FILTER (WHERE merchant_id_raw IS NULL) FROM analytics.part4_behavior_source UNION ALL SELECT 'merchant_category_code', COUNT(DISTINCT merchant_category_code), COUNT(*) FILTER (WHERE merchant_category_code IS NULL) FROM analytics.part4_behavior_source UNION ALL SELECT 'use_chip', COUNT(DISTINCT use_chip), COUNT(*) FILTER (WHERE use_chip IS NULL) FROM analytics.part4_behavior_source", "feature_cardinality_profile.csv", "field_name")
    reports["feature_dependency_profile"] = export_query(db, "SELECT 'user_history_to_card_history' dependency, CORR(user_prior_txn_count, card_prior_txn_count) metric_value, 'Descriptive structural check; not model importance.' notes FROM analytics.behavioral_features_v1 UNION ALL SELECT 'current_positive_to_user_mean_ratio', CORR(CASE WHEN current_positive_amount THEN 1 ELSE 0 END, current_positive_amount_vs_user_mean), 'NULL-aware exploratory dependency.' FROM analytics.behavioral_features_v1", "feature_dependency_profile.csv", "dependency")
    reports["channel_state_dependency"] = export_query(db, "SELECT * FROM analytics.part4_channel_state_dependency", "channel_state_dependency.csv", "transactions DESC, channel, state_status")
    numeric_sql, binary_sql = signal_queries(); reports["development_numeric_feature_signal"] = export_query(db, numeric_sql, "development_numeric_feature_signal.csv", "feature_name, bin_order"); reports["development_binary_feature_signal"] = export_query(db, binary_sql, "development_binary_feature_signal.csv", "feature_name, bin_order")
    reports["feature_family_summary"] = export_query(db, "SELECT 'entity_history' feature_family, 9 feature_count, 'User/card/merchant prior counts, cold start and recency' AS \"scope\" UNION ALL SELECT 'velocity', 8, 'User/card/merchant count windows' UNION ALL SELECT 'amount', 12, 'Positive amount baselines and deviations' UNION ALL SELECT 'relationship_familiarity', 14, 'Merchant, MCC and channel familiarity' UNION ALL SELECT 'geography', 0, 'Extended-only dependency audit'", "feature_family_summary.csv", "feature_family")
    elapsed = time.perf_counter() - started; write_runtime_profile(stage_times, args.temp_directory, args)
    db.close()
    validator_args = [sys.executable, str(ROOT / "src/part4/validate_part4.py"), "--database", str(database), "--memory-limit", args.memory_limit, "--threads", str(args.threads), "--skip-summary-check"]
    if args.sample_row_limit is not None:
        validator_args += ["--sample-row-limit", str(args.sample_row_limit)]
    if args.temp_directory:
        validator_args += ["--temp-directory", str(args.temp_directory)]
    first = subprocess.run(validator_args, cwd=ROOT, text=True, check=False)
    if first.returncode != 0:
        raise SystemExit("Part 4 validation failed; public summary was not written.")
    db = duckdb.connect(str(database)); db.execute(f"SET threads={max(1, args.threads)}"); db.execute(f"SET memory_limit='{args.memory_limit}'"); db.execute("SET preserve_insertion_order=false")
    candidate = SUMMARY_PATH.with_name("part4_summary.candidate.json"); candidate.write_text(json.dumps(build_summary(db, reports, elapsed, args, run_meta), indent=2, ensure_ascii=False), encoding="utf-8")
    manifest = {**run_meta, "status": "BEHAVIOR_READY_SAMPLE_QA" if args.sample_row_limit is not None else "BEHAVIOR_READY", "validation_status": "PASS", "pipeline_elapsed_seconds": round(elapsed, 3), "row_level_mart_retained": bool(args.retain_mart), "raw_publication": False, "execution_scope": "DETERMINISTIC_QA_EXECUTION_SLICE" if args.sample_row_limit is not None else "FULL_POPULATION"}
    (REPORT_DIR / "runtime_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    db.close()
    final_validator_args = [sys.executable, str(ROOT / "src/part4/validate_part4.py"), "--database", str(database), "--memory-limit", args.memory_limit, "--threads", str(args.threads), "--summary", str(candidate)]
    if args.sample_row_limit is not None:
        final_validator_args += ["--sample-row-limit", str(args.sample_row_limit)]
    if args.temp_directory:
        final_validator_args += ["--temp-directory", str(args.temp_directory)]
    second = subprocess.run(final_validator_args, cwd=ROOT, text=True, check=False)
    if second.returncode != 0:
        candidate.unlink(missing_ok=True); raise SystemExit("Part 4 validation failed after summary contract check; public summary was not written.")
    candidate.replace(SUMMARY_PATH)
    db = duckdb.connect(str(database))
    if not args.retain_mart:
        db.execute("DROP VIEW IF EXISTS analytics.behavioral_features_v1")
        for table in ("part4_user_features", "part4_card_features", "part4_merchant_features", "part4_amount_features", "part4_user_merchant_features", "part4_card_merchant_features", "part4_user_mcc_features", "part4_card_mcc_features", "part4_channel_features"):
            db.execute(f"DROP TABLE IF EXISTS analytics.{table}")
    db.close(); print("BEHAVIOR_READY_SAMPLE_QA" if args.sample_row_limit is not None else "BEHAVIOR_READY")


if __name__ == "__main__":
    main()
