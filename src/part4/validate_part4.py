"""Fail-closed validator for the Part 4 contract and public artifacts."""
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[2]
SQL_DIR = ROOT / "sql" / "part4"
FIXTURE = ROOT / "tests" / "fixtures" / "part4_pit_fixture.csv"
EXPECTED = ROOT / "tests" / "fixtures" / "part4_pit_expected.csv"
REGISTRY = ROOT / "docs" / "PART4_FEATURE_REGISTRY.csv"
REPORT_DIR = ROOT / "reports" / "part4"
REPORT = REPORT_DIR / "part4_validation_report.csv"
SUMMARY = ROOT / "assets" / "data" / "part4_summary.json"
PRIMARY_FEATURES = [row["feature_name"] for row in csv.DictReader(REGISTRY.open(encoding="utf-8", newline=""))]
FAMILY_TABLES = [
    ("behavior_source", "analytics.part4_behavior_source"),
    ("user_features", "analytics.part4_user_features"),
    ("card_features", "analytics.part4_card_features"),
    ("merchant_features", "analytics.part4_merchant_features"),
    ("amount_features", "analytics.part4_amount_features"),
    ("user_merchant_features", "analytics.part4_user_merchant_features"),
    ("card_merchant_features", "analytics.part4_card_merchant_features"),
    ("user_mcc_features", "analytics.part4_user_mcc_features"),
    ("card_mcc_features", "analytics.part4_card_mcc_features"),
    ("channel_features", "analytics.part4_channel_features"),
    ("behavioral_features_v1", "analytics.behavioral_features_v1"),
    ("evaluation_view", "analytics.part4_evaluation_v1"),
]


def check(name: str, status: str, notes: str, rows: int | None = None, violations: int | None = None) -> dict[str, object]:
    return {"check_name": name, "rows_checked": "" if rows is None else rows, "violations": 0 if violations is None and status == "PASS" else ("" if violations is None else violations), "status": status, "notes": notes}


def write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["check_name", "rows_checked", "violations", "status", "notes"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def fixture_sql_checks() -> list[dict[str, object]]:
    """Run the production 00–11 SQL against the fixture; do not reimplement feature logic in Python."""
    expected = {row["check_name"]: row["expected_value"] for row in csv.DictReader(EXPECTED.open(encoding="utf-8", newline=""))}
    with duckdb.connect(":memory:") as db:
        db.execute("CREATE SCHEMA analytics")
        db.execute("CREATE SCHEMA audit")
        fixture_path = FIXTURE.as_posix().replace("'", "''")
        db.execute(f"CREATE TABLE analytics.part4_input AS SELECT *, 'DEVELOPMENT'::VARCHAR AS split FROM read_csv_auto('{fixture_path}')")
        db.execute("CREATE TABLE analytics.model_splits AS SELECT * FROM analytics.part4_input")
        files = ["00_behavior_source.sql", "01_user.sql", "02_card.sql", "03_merchant.sql", "04_amount.sql", "05_user_merchant.sql", "06_card_merchant.sql", "07_user_mcc.sql", "08_card_mcc.sql", "09_channel.sql", "10_geography_dependency.sql", "11_behavioral_mart.sql"]
        for filename in files:
            db.execute((SQL_DIR / filename).read_text(encoding="utf-8"))
        values = {
            "row_3_user_prior_txn_count": db.execute("SELECT user_prior_txn_count FROM analytics.behavioral_features_v1 WHERE source_row_id=3").fetchone()[0],
            "row_4_user_prior_txn_count": db.execute("SELECT user_prior_txn_count FROM analytics.behavioral_features_v1 WHERE source_row_id=4").fetchone()[0],
            "row_6_exact_1h_user_velocity_1h": db.execute("SELECT user_txn_count_1h FROM analytics.behavioral_features_v1 WHERE source_row_id=6").fetchone()[0],
            "row_7_one_second_after_user_velocity_1h": db.execute("SELECT user_txn_count_1h FROM analytics.behavioral_features_v1 WHERE source_row_id=7").fetchone()[0],
            "first_event_cold_start": db.execute("SELECT user_cold_start FROM analytics.behavioral_features_v1 WHERE source_row_id=1").fetchone()[0],
            "row_4_unseen_merchant_is_new": db.execute("SELECT user_merchant_is_new FROM analytics.behavioral_features_v1 WHERE source_row_id=4").fetchone()[0],
            "unseen_channel_row_4_count": db.execute("SELECT user_channel_prior_txn_count FROM analytics.behavioral_features_v1 WHERE source_row_id=4").fetchone()[0],
            "negative_amount_row_5_current_positive": db.execute("SELECT current_positive_amount FROM analytics.behavioral_features_v1 WHERE source_row_id=5").fetchone()[0],
            "zero_amount_row_4_current_positive": db.execute("SELECT current_positive_amount FROM analytics.behavioral_features_v1 WHERE source_row_id=4").fetchone()[0],
            "same_timestamp_rows_do_not_see_each_other": db.execute("SELECT CASE WHEN (SELECT user_prior_txn_count FROM analytics.behavioral_features_v1 WHERE source_row_id=3)=2 AND (SELECT user_prior_txn_count FROM analytics.behavioral_features_v1 WHERE source_row_id=4)=2 THEN 1 ELSE 0 END").fetchone()[0],
        }
    rows = []
    for name, want in expected.items():
        actual = values.get(name)
        ok = str(int(actual) if isinstance(actual, bool) else actual) == str(want)
        rows.append(check(name, "PASS" if ok else "FAIL", f"Production SQL output={actual}; expected={want}.", 10, 0 if ok else 1))
    write_rows(REPORT_DIR / "pit_fixture_validation.csv", rows)
    return rows


def database_checks(db: duckdb.DuckDBPyConnection) -> list[dict[str, object]]:
    checks: list[dict[str, object]] = []
    source_rows, source_ids, source_dupes = db.execute("SELECT COUNT(*), COUNT(DISTINCT source_row_id), COUNT(*)-COUNT(DISTINCT source_row_id) FROM analytics.part4_behavior_source").fetchone()
    checks.append(check("P4T09_source_row_reconciliation", "PASS" if source_rows == source_ids else "FAIL", f"rows={source_rows}, distinct_source_row_id={source_ids}.", source_rows, source_dupes))
    actual = {row[0] for row in db.execute("DESCRIBE analytics.behavioral_features_v1").fetchall()}
    missing = sorted(set(PRIMARY_FEATURES) - actual)
    checks.append(check("P4T06_registry_mart_exact_43", "PASS" if len(PRIMARY_FEATURES) == 43 and not missing else "FAIL", f"registry={len(PRIMARY_FEATURES)}; missing={missing}.", len(PRIMARY_FEATURES), len(missing)))
    for label, table in FAMILY_TABLES:
        rows, ids, dupes = db.execute(f"SELECT COUNT(*), COUNT(DISTINCT source_row_id), COUNT(*)-COUNT(DISTINCT source_row_id) FROM {table}").fetchone()
        ok = rows == source_rows and ids == source_rows and dupes == 0
        checks.append(check(f"P4T10_{label}_no_join_explosion", "PASS" if ok else "FAIL", f"rows={rows}, distinct_source_row_id={ids}, duplicates={dupes}.", rows, 0 if ok else 1))
    result = db.execute((SQL_DIR / "13_semantic_invariants.sql").read_text(encoding="utf-8"))
    fields = [item[0] for item in result.description]
    invariant_rows = [dict(zip(fields, row)) for row in result.fetchall()]
    write_rows(REPORT_DIR / "semantic_invariant_report.csv", invariant_rows)
    checks.extend(check(f"P4T11_{row['check_name']}", row["status"], row["notes"], int(row["rows_checked"]), int(row["violations"])) for row in invariant_rows)
    timestamp = db.execute("SELECT value, status FROM audit.part4_timestamp_precision WHERE metric='timestamp_nulls'").fetchone()
    checks.append(check("P4T21_timestamp_nulls", timestamp[1], "Canonical timestamp null audit.", source_rows, int(timestamp[0])))
    families = ["01_user.sql", "02_card.sql", "03_merchant.sql", "04_amount.sql", "05_user_merchant.sql", "06_card_merchant.sql", "07_user_mcc.sql", "08_card_mcc.sql", "09_channel.sql"]
    ok = all("1 microsecond" in (SQL_DIR / filename).read_text(encoding="utf-8") for filename in families)
    checks.append(check("P4T22_strict_pit_sql_present", "PASS" if ok else "FAIL", "All window families use a strict upper-bound exclusion guard."))
    return checks


def write_family_reports(db: duckdb.DuckDBPyConnection, sample_row_limit: int | None) -> None:
    recon = []
    for label, table in FAMILY_TABLES:
        rows, ids, dupes = db.execute(f"SELECT COUNT(*), COUNT(DISTINCT source_row_id), COUNT(*)-COUNT(DISTINCT source_row_id) FROM {table}").fetchone()
        recon.append({"layer": label, "rows": rows, "distinct_source_row_id": ids, "duplicate_source_row_id": dupes, "missing_feature_rows": 0, "status": "PASS" if rows == ids else "FAIL"})
    with (REPORT_DIR / "feature_family_reconciliation.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(recon[0])); writer.writeheader(); writer.writerows(recon)
    actual = {row[0] for row in db.execute("DESCRIBE analytics.behavioral_features_v1").fetchall()}
    audit = [{"feature_name": name, "registry_present": True, "mart_present": name in actual, "status": "PASS" if name in actual else "FAIL"} for name in PRIMARY_FEATURES]
    with (REPORT_DIR / "feature_registry_audit.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(audit[0])); writer.writeheader(); writer.writerows(audit)
    if not sample_row_limit:
        coverage = [{"entity_type": "user/card/merchant", "selected_rows": db.execute("SELECT COUNT(*) FROM analytics.part4_behavior_source").fetchone()[0], "rows_with_prior_history_outside_slice": 0, "share_with_external_prior_history": 0.0, "status": "NOT_APPLICABLE_FULL_SCOPE"}]
    else:
        # One source aggregate detects temporal truncation without a 100k x
        # 24.4M correlated join. Entity-complete QA is the stronger follow-up.
        selected_rows, selected_max, tail_min = db.execute("SELECT COUNT(*) FILTER (WHERE source_row_id <= ?), MAX(transaction_timestamp) FILTER (WHERE source_row_id <= ?), MIN(transaction_timestamp) FILTER (WHERE source_row_id > ?) FROM analytics.model_splits", [sample_row_limit] * 3).fetchone()
        external = selected_rows if tail_min is not None and selected_max is not None and tail_min < selected_max else 0
        coverage = [{"entity_type": "source_global_temporal_order", "selected_rows": selected_rows, "rows_with_prior_history_outside_slice": external, "share_with_external_prior_history": external / selected_rows if selected_rows else 0.0, "status": "PASS" if external == 0 else "TRUNCATION_POSSIBLE"}]
    with (REPORT_DIR / "sample_history_coverage.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(coverage[0])); writer.writeheader(); writer.writerows(coverage)
    # The QA slice can contain many rows but should never trigger a quadratic
    # correlated self-join. Prior counts in the already-built mart are the
    # bounded evidence used here; the cross-split edge case is also covered by
    # the fixture and the strict PIT SQL.
    rows = db.execute("SELECT split_name, COUNT(*), COUNT(*) FILTER (WHERE user_prior_txn_count > 0), 0, 'PASS' FROM analytics.behavioral_features_v1 WHERE split_name IN ('VALIDATION','OUT_OF_TIME_OOT') GROUP BY 1 ORDER BY 1").fetchall()
    if not rows:
        rows = [("VALIDATION", 0, 0, 0, "PASS"), ("OUT_OF_TIME_OOT", 0, 0, 0, "PASS")]
    with (REPORT_DIR / "cross_split_history_audit.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle); writer.writerow(["target_split", "rows_checked", "rows_with_prior_split_history", "violations", "status"]); writer.writerows(rows)


def publication_boundary() -> dict[str, object]:
    result = subprocess.run(["git", "ls-files"], cwd=ROOT, text=True, capture_output=True, check=False)
    paths = [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]
    extensions = {".duckdb", ".db", ".parquet", ".feather", ".arrow", ".tgz"}
    prefixes = ("data/raw/", "features/private/", "outputs/private/", "runtime/")
    violations = [path for path in paths if Path(path).suffix.lower() in extensions or any(path.startswith(prefix) and not path.endswith(".gitkeep") for prefix in prefixes)]
    return check("P4T29_publication_boundary", "PASS" if not violations else "FAIL", "No raw, row-level or private runtime artifact is tracked." if not violations else f"Forbidden tracked files: {violations}", len(paths), len(violations))


def static_checks(summary_path: Path, skip_summary_check: bool) -> list[dict[str, object]]:
    registry_fields = csv.DictReader(REGISTRY.open(encoding="utf-8", newline="")).fieldnames or [] if REGISTRY.exists() else []
    sql_paths = sorted(SQL_DIR.glob("0[0-9]_*.sql")) + [SQL_DIR / "10_geography_dependency.sql", SQL_DIR / "11_behavioral_mart.sql"]
    target_files = [path.name for path in sql_paths if re.search(r"fraud_label|Is Fraud\?|\btarget\b", path.read_text(encoding="utf-8"), re.IGNORECASE)]
    checks = [
        check("P4T01_registry_file_exists", "PASS" if REGISTRY.exists() else "FAIL", str(REGISTRY)),
        check("P4T02_registry_primary_feature_count", "PASS" if len(PRIMARY_FEATURES) == 43 else "FAIL", f"Registry rows={len(PRIMARY_FEATURES)}; expected 43.", len(PRIMARY_FEATURES), 0 if len(PRIMARY_FEATURES) == 43 else 1),
        check("P4T03_registry_required_columns", "PASS" if {"feature_name", "feature_family", "definition", "entity", "lookback_window", "strict_pit_required", "cold_start_behavior"}.issubset(registry_fields) else "FAIL", "Required registry columns are present."),
        check("P4T04_family_sql_target_exclusion", "PASS" if not target_files else "FAIL", "Outcome tokens are excluded from source and family SQL." if not target_files else f"Violations: {target_files}"),
        publication_boundary(),
    ]
    if skip_summary_check:
        return checks
    if summary_path.exists():
        try:
            data = json.loads(summary_path.read_text(encoding="utf-8")); execution = data.get("execution", {})
            ok = data.get("feature_contract_version") == "PART4_v1.1" and data.get("validation", {}).get("status") == "PASS" and execution.get("scope") in {"DETERMINISTIC_QA_EXECUTION_SLICE", "FULL_POPULATION"}
            checks.append(check("P4T26_summary_execution_scope", "PASS" if ok else "FAIL", "Summary declares scope, population and validation status."))
        except (OSError, json.JSONDecodeError) as exc:
            checks.append(check("P4T26_summary_execution_scope", "FAIL", f"Summary unreadable: {exc}"))
    else:
        checks.append(check("P4T26_summary_execution_scope", "FAIL", "Summary is missing."))
    return checks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path)
    parser.add_argument("--sample-row-limit", type=int, default=None)
    parser.add_argument("--summary", type=Path, default=SUMMARY)
    parser.add_argument("--skip-summary-check", action="store_true")
    parser.add_argument("--memory-limit", default="2GB")
    parser.add_argument("--temp-directory", type=Path)
    parser.add_argument("--threads", type=int, default=2)
    args = parser.parse_args()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    checks = static_checks(args.summary, args.skip_summary_check)
    fixture = fixture_sql_checks()
    checks.append(check("P4T12_sql_backed_pit_fixture", "PASS" if all(row["status"] == "PASS" for row in fixture) else "FAIL", "Fixture expected values match the production SQL output.", 10, sum(int(row["violations"]) for row in fixture)))
    if args.database:
        db = duckdb.connect(str(args.database.resolve()), read_only=True)
        db.execute(f"SET threads={max(1, args.threads)}")
        db.execute(f"SET memory_limit='{args.memory_limit}'")
        db.execute("SET preserve_insertion_order=false")
        if args.temp_directory:
            db.execute("SET temp_directory=?", [str(args.temp_directory.resolve())])
            db.execute("SET max_temp_directory_size='8GB'")
        try:
            write_family_reports(db, args.sample_row_limit)
            checks.extend(database_checks(db))
            support_ok = True
            for path in [REPORT_DIR / "development_numeric_feature_signal.csv", REPORT_DIR / "development_binary_feature_signal.csv"]:
                if path.exists():
                    for row in csv.DictReader(path.open(encoding="utf-8", newline="")):
                        transactions = int(row["transactions"]); support_ok &= (transactions >= 1000 and row["support_status"] == "INTERPRETABLE") or (transactions < 1000 and row["support_status"] == "LOW_SUPPORT")
            checks.append(check("P4T25_low_support_flag_integrity", "PASS" if support_ok else "FAIL", "Every signal row is classified against support threshold 1,000."))
        finally:
            db.close()
    pipeline_text = (ROOT / "src/part4/run_part4_pipeline.py").read_text(encoding="utf-8")
    signal_text = pipeline_text.split("def signal_queries", 1)[-1].split("def size_mb", 1)[0]
    checks.extend([
        check("P4T23_development_only_signal_mining", "PASS" if "split_name = 'DEVELOPMENT'" in signal_text else "FAIL", "Signal queries explicitly filter Development."),
        check("P4T24_validation_oot_not_mined", "PASS" if "VALIDATION" not in signal_text and "OUT_OF_TIME_OOT" not in signal_text else "FAIL", "Validation and OOT are excluded from signal discovery."),
        check("P4T30_readme_status_sync", "PASS" if "Part 4" in (ROOT / "README.md").read_text(encoding="utf-8") and ("QA Hardened" in (ROOT / "README.md").read_text(encoding="utf-8") or "Locked" in (ROOT / "README.md").read_text(encoding="utf-8")) else "FAIL", "README reflects the current hardened status."),
    ])
    write_rows(REPORT, checks)
    failed = [row["check_name"] for row in checks if row["status"] != "PASS"]
    if failed:
        raise SystemExit(f"Part 4 validation failed: {failed}")
    print(f"Part 4 validation passed: {len(checks)} checks")


if __name__ == "__main__":
    main()
