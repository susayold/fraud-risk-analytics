"""Build the local DuckDB layer from processed Parquet files."""

from config import DATABASE_DIR, PROCESSED_DIR


def main() -> None:
    try:
        import duckdb
    except ImportError as exc:
        raise SystemExit("DuckDB is required: pip install duckdb") from exc
    parquet_files = sorted(PROCESSED_DIR.glob("*.parquet"))
    if not parquet_files:
        raise SystemExit("No processed Parquet files found; run src/build_parquet.py first.")
    db = duckdb.connect(str(DATABASE_DIR / "fraud_analytics.duckdb"))
    for schema in ("raw", "audit", "analytics"):
        db.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    for path in parquet_files:
        table = path.stem.replace("-", "_")
        db.execute(f"CREATE OR REPLACE TABLE raw.{table} AS SELECT * FROM read_parquet(?)", [str(path)])
    db.close(); print("DuckDB schemas and raw tables created.")


if __name__ == "__main__":
    main()
