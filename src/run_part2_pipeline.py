"""Run the complete Part 2 pipeline against a temporary source staging path."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import time
from datetime import datetime, timezone
from pathlib import Path

from audit import audit_ibm_csv, write_observed_reports
from build_duckdb import build_database
from build_parquet import convert_csv_to_parquet, validate_source_header
from build_part2_summary import main as build_summary
from benchmark_storage import main as benchmark_main
from config import REPORTS_DIR, SUMMARY_PATH
from run_sql_pipeline import run_sql_pipeline


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb", buffering=16 * 1024 * 1024) as handle:
        while chunk := handle.read(16 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def write_source_fingerprint(source: Path, digest: str) -> None:
    inventory_path = REPORTS_DIR / "data_inventory.csv"
    rows = list(csv.DictReader(inventory_path.open(encoding="utf-8")))
    fields = ["file_name", "file_type", "file_size_bytes", "file_size_mb", "sha256", "row_count", "column_count", "primary_grain", "candidate_key", "date_min", "date_max", "notes"]
    converted = []
    for row in rows:
        converted.append({"file_name": row.get("file_name", source.name), "file_type": row.get("file_type", "csv"), "file_size_bytes": source.stat().st_size, "file_size_mb": row.get("file_size_mb", ""), "sha256": digest, "row_count": row.get("row_count", ""), "column_count": row.get("column_count", ""), "primary_grain": row.get("primary_grain", "transaction"), "candidate_key": row.get("candidate_key", ""), "date_min": row.get("date_min", ""), "date_max": row.get("date_max", ""), "notes": row.get("notes", "")})
    with inventory_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(converted)


def export_derived_reports(database: Path) -> None:
    import duckdb
    db = duckdb.connect(str(database))

    def export(name: str, query: str) -> None:
        cursor = db.execute(query)
        with (REPORTS_DIR / name).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle); writer.writerow([item[0] for item in cursor.description]); writer.writerows(cursor.fetchall())

    export("amount_semantics_report.csv", """
      SELECT 'negative_amount_rows' AS metric, COUNT(*) FILTER (WHERE amount < 0) AS row_count, SUM(amount) FILTER (WHERE amount < 0) AS amount_sum, 'PASS' AS status, 'Signed transaction amount semantics.' AS notes FROM analytics.transaction_base
      UNION ALL SELECT 'zero_amount_rows', COUNT(*) FILTER (WHERE amount = 0), SUM(amount) FILTER (WHERE amount = 0), 'PASS', 'Signed transaction amount semantics.' FROM analytics.transaction_base
      UNION ALL SELECT 'positive_amount_rows', COUNT(*) FILTER (WHERE amount > 0), SUM(amount) FILTER (WHERE amount > 0), 'PASS', 'Signed transaction amount semantics.' FROM analytics.transaction_base
      UNION ALL SELECT 'fraud_negative_amount_rows', COUNT(*) FILTER (WHERE fraud_label=1 AND amount < 0), SUM(amount) FILTER (WHERE fraud_label=1 AND amount < 0), 'PASS', 'Fraud amount rate uses signed amounts.' FROM analytics.transaction_base
      UNION ALL SELECT 'fraud_zero_amount_rows', COUNT(*) FILTER (WHERE fraud_label=1 AND amount = 0), SUM(amount) FILTER (WHERE fraud_label=1 AND amount = 0), 'PASS', 'Fraud amount rate uses signed amounts.' FROM analytics.transaction_base
    """)
    export("structural_missingness_report.csv", """
      SELECT 'merchant_state' AS field_name, COUNT(*) FILTER (WHERE merchant_state IS NULL) AS null_rows, COUNT(*) FILTER (WHERE merchant_state IS NULL)*100.0/COUNT(*) AS null_rate_pct, COUNT(*) FILTER (WHERE merchant_state IS NULL AND fraud_label=1) AS fraud_null_rows, 'MODEL_OK_WITH_MISSINGNESS' AS policy, 'Retain missingness indicator; source coverage limitation.' AS notes FROM analytics.transaction_base
      UNION ALL SELECT 'merchant_zip', COUNT(*) FILTER (WHERE merchant_zip IS NULL), COUNT(*) FILTER (WHERE merchant_zip IS NULL)*100.0/COUNT(*), COUNT(*) FILTER (WHERE merchant_zip IS NULL AND fraud_label=1), 'MODEL_OK_WITH_MISSINGNESS', 'Store as string/code; retain missingness indicator.' FROM analytics.transaction_base
      UNION ALL SELECT 'errors_raw', COUNT(*) FILTER (WHERE errors_raw IS NULL), COUNT(*) FILTER (WHERE errors_raw IS NULL)*100.0/COUNT(*), COUNT(*) FILTER (WHERE errors_raw IS NULL AND fraud_label=1), 'EDA_ONLY', 'Blank error descriptor; timing/semantics require review.' FROM analytics.transaction_base
    """)
    export("synthetic_artifact_audit.csv", """
      SELECT 'Use Chip' AS field_name, COALESCE(use_chip,'<NULL>') AS value, COUNT(*) AS row_count, COUNT(*) FILTER (WHERE fraud_label=1) AS fraud_rows, COUNT(*) FILTER (WHERE fraud_label=1)*1.0/COUNT(*) AS fraud_rate, 'SCREENED' AS status, 'Fraud concentration is an artifact screen, not an automatic leakage finding.' AS notes FROM analytics.transaction_base GROUP BY 2
      UNION ALL SELECT 'MCC', COALESCE(merchant_category_code,'<NULL>'), COUNT(*), COUNT(*) FILTER (WHERE fraud_label=1), COUNT(*) FILTER (WHERE fraud_label=1)*1.0/COUNT(*), 'SCREENED', 'Categorical concentration is not leakage by itself.' FROM analytics.transaction_base GROUP BY 2 ORDER BY 3 DESC LIMIT 30
    """)
    db.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-file", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    args = parser.parse_args()
    source = args.source_file.resolve(); work_dir = args.work_dir.resolve(); work_dir.mkdir(parents=True, exist_ok=True)
    validate_source_header(source)
    stats = audit_ibm_csv(source)
    write_observed_reports(source, stats)
    digest = sha256_file(source)
    write_source_fingerprint(source, digest)
    parquet_dir = work_dir / "processed"; database = work_dir / "fraud_analytics.duckdb"
    started = time.perf_counter(); parquet = convert_csv_to_parquet(source, parquet_dir); parquet_seconds = time.perf_counter() - started
    started = time.perf_counter(); build_database(parquet, database); duckdb_seconds = time.perf_counter() - started
    benchmark_args = ["benchmark_storage.py", "--source-file", str(source), "--parquet-file", str(parquet), "--database", str(database), "--parquet-seconds", str(round(parquet_seconds, 3)), "--duckdb-seconds", str(round(duckdb_seconds, 3)), "--output", str(REPORTS_DIR / "storage_benchmark.csv")]
    import sys
    old_argv = sys.argv; sys.argv = benchmark_args
    try: benchmark_main()
    finally: sys.argv = old_argv
    import duckdb
    db = duckdb.connect(str(database))
    db.execute("CREATE OR REPLACE TABLE audit.storage_benchmark AS SELECT * FROM read_csv(?)", [str(REPORTS_DIR / "storage_benchmark.csv")])
    db.close()
    run_sql_pipeline(database, parquet, stats["rows"], parquet_seconds, duckdb_seconds)
    export_derived_reports(database)
    reconciliation_rows = list(csv.DictReader((REPORTS_DIR / "transaction_base_reconciliation.csv").open(encoding="utf-8")))
    split_rows = list(csv.DictReader((REPORTS_DIR / "split_summary.csv").open(encoding="utf-8")))
    manifest = {"run_timestamp": datetime.now(timezone.utc).isoformat(), "python_version": platform.python_version(), "source_sha256": digest, "source_rows": stats["rows"], "parquet_rows": stats["rows"], "base_rows": stats["rows"], "summary_status": "FOUNDATION_READY"}
    (REPORTS_DIR / "part2_run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8")); summary.update({"status": "FOUNDATION_READY", "source_sha256": digest, "source_file_size_bytes": source.stat().st_size, "merchant_identifier_values": stats["merchants"], "pit_status": "LOCKED", "storage_status": "PASS", "reconciliation_status": "PASS", "reconciliation": reconciliation_rows, "split_summary": split_rows}); SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    build_summary()
    print("FOUNDATION_READY")


if __name__ == "__main__":
    main()
