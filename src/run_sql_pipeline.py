"""Execute the Part 2 SQL files in deterministic order against DuckDB."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import duckdb

from config import REPORTS_DIR

SQL_ORDER = ["00_source_contract.sql", "01_standardize_raw.sql", "02_data_quality.sql", "03_entity_key_audit.sql", "04_fraud_label_audit.sql", "05_transaction_base.sql", "06_pit_validation.sql", "07_model_splits.sql", "08_reconciliation.sql", "09_storage_benchmark.sql"]


def export_query(db: duckdb.DuckDBPyConnection, query: str, output: Path) -> None:
    cursor = db.execute(query)
    fields = [item[0] for item in cursor.description]
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(fields)
        writer.writerows(cursor.fetchall())


def run_sql_pipeline(database: Path, parquet_file: Path, source_rows: int, parquet_seconds: float, duckdb_seconds: float) -> None:
    root = Path(__file__).resolve().parents[1]
    split_policy = json.loads((root / "config" / "split_policy.json").read_text(encoding="utf-8"))
    db = duckdb.connect(str(database))
    db.execute("CREATE SCHEMA IF NOT EXISTS audit")
    db.execute("CREATE OR REPLACE TABLE audit.split_policy AS SELECT CAST(? AS DATE) AS development_end, CAST(? AS DATE) AS validation_start, CAST(? AS DATE) AS validation_end, CAST(? AS DATE) AS oot_start, CAST(? AS DATE) AS oot_end", [split_policy["development_end"], split_policy["validation_start"], split_policy["validation_end"], split_policy["oot_start"], split_policy["oot_end"]])
    db.execute("CREATE OR REPLACE TABLE audit.pipeline_counts AS SELECT 'SOURCE_CSV' AS layer, CAST(? AS BIGINT) AS row_count, CAST(NULL AS BIGINT) AS distinct_source_row_id, CAST(NULL AS BIGINT) AS min_source_row_id, CAST(NULL AS BIGINT) AS max_source_row_id, CAST(NULL AS BIGINT) AS fraud_rows UNION ALL SELECT 'PARQUET', COUNT(*), COUNT(DISTINCT source_row_id), MIN(source_row_id), MAX(source_row_id), COUNT(*) FILTER (WHERE LOWER(TRIM(CAST(\"Is Fraud?\" AS VARCHAR))) IN ('yes','true')) FROM read_parquet(?) UNION ALL SELECT 'DUCKDB_RAW', COUNT(*), COUNT(DISTINCT source_row_id), MIN(source_row_id), MAX(source_row_id), COUNT(*) FILTER (WHERE LOWER(TRIM(CAST(\"Is Fraud?\" AS VARCHAR))) IN ('yes','true')) FROM raw.card_transactions", [source_rows, str(parquet_file),])
    for filename in SQL_ORDER:
        sql = (root / "sql" / filename).read_text(encoding="utf-8")
        db.execute(sql)
    export_query(db, "SELECT * FROM audit.reconciliation ORDER BY CASE layer WHEN 'SOURCE_CSV' THEN 1 WHEN 'PARQUET' THEN 2 WHEN 'DUCKDB_RAW' THEN 3 WHEN 'STANDARDIZED' THEN 4 WHEN 'TRANSACTION_BASE' THEN 5 ELSE 6 END", REPORTS_DIR / "transaction_base_reconciliation.csv")
    export_query(db, "SELECT * FROM audit.pit_validation", REPORTS_DIR / "pit_validation_report.csv")
    export_query(db, "SELECT split AS split_name, MIN(transaction_date) AS date_start, MAX(transaction_date) AS date_end, COUNT(*) AS row_count, COUNT(*) FILTER (WHERE fraud_label=1) AS fraud_count, 'OBSERVED' AS status, 'Chronological date split; no random sampling.' AS notes FROM analytics.model_splits GROUP BY split ORDER BY CASE split WHEN 'DEVELOPMENT' THEN 1 WHEN 'VALIDATION' THEN 2 ELSE 3 END", REPORTS_DIR / "split_summary.csv")
    duplicate_query = """
    WITH hashes AS (
      SELECT md5(concat_ws(chr(31), COALESCE(CAST(\"User\" AS VARCHAR),'<NULL>'), COALESCE(CAST(\"Card\" AS VARCHAR),'<NULL>'), COALESCE(CAST(\"Year\" AS VARCHAR),'<NULL>'), COALESCE(CAST(\"Month\" AS VARCHAR),'<NULL>'), COALESCE(CAST(\"Day\" AS VARCHAR),'<NULL>'), COALESCE(\"Time\",'<NULL>'), COALESCE(\"Amount\",'<NULL>'), COALESCE(\"Use Chip\",'<NULL>'), COALESCE(CAST(\"Merchant Name\" AS VARCHAR),'<NULL>'), COALESCE(\"Merchant City\",'<NULL>'), COALESCE(\"Merchant State\",'<NULL>'), COALESCE(CAST(\"Zip\" AS VARCHAR),'<NULL>'), COALESCE(CAST(\"MCC\" AS VARCHAR),'<NULL>'), COALESCE(\"Errors?\",'<NULL>'))) AS feature_hash, \"Is Fraud?\" AS label FROM raw.card_transactions
    ), grouped AS (SELECT feature_hash, COUNT(*) AS rows, COUNT(DISTINCT label) AS labels FROM hashes GROUP BY feature_hash)
    SELECT 'exact_duplicate_rows_excluding_source_row_id' AS metric, COALESCE(SUM(rows)-COUNT(*),0)::BIGINT AS value FROM grouped
    UNION ALL SELECT 'feature_duplicate_groups_excluding_label', COUNT(*) FILTER (WHERE rows > 1)::BIGINT FROM grouped
    UNION ALL SELECT 'conflicting_label_groups', COUNT(*) FILTER (WHERE labels > 1)::BIGINT FROM grouped
    """
    export_query(db, duplicate_query, REPORTS_DIR / "duplicate_audit.csv")
    db.close()


if __name__ == "__main__":
    raise SystemExit("Use src/run_part2_pipeline.py as the top-level runner.")
