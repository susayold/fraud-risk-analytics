"""Create the local analytical DuckDB layer from one processed Parquet file."""

from __future__ import annotations

import argparse
from pathlib import Path

from config import DATABASE_DIR, PROCESSED_DIR


def build_database(parquet_file: Path, database: Path) -> Path:
    try:
        import duckdb
    except ImportError as exc:
        raise SystemExit("DuckDB is required: python -m pip install duckdb") from exc
    database.parent.mkdir(parents=True, exist_ok=True)
    db = duckdb.connect(str(database))
    for schema in ("raw", "audit", "analytics"):
        db.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    db.execute("CREATE OR REPLACE TABLE raw.card_transactions AS SELECT * FROM read_parquet(?)", [str(parquet_file)])
    db.close()
    return database


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parquet-file", type=Path)
    parser.add_argument("--database", type=Path, default=DATABASE_DIR / "fraud_analytics.duckdb")
    args = parser.parse_args()
    parquet = args.parquet_file
    if parquet is None:
        files = sorted(PROCESSED_DIR.glob("*.parquet"))
        if len(files) != 1:
            raise SystemExit("Pass --parquet-file explicitly; exactly one Parquet file is required.")
        parquet = files[0]
    build_database(parquet, args.database)
    print(f"DuckDB raw.card_transactions created from {parquet.name}")


if __name__ == "__main__":
    main()
