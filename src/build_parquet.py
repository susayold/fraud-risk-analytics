"""Convert audited CSV sources to compressed Parquet with DuckDB."""

from config import PROCESSED_DIR, RAW_DIR


def main() -> None:
    try:
        import duckdb
    except ImportError as exc:
        raise SystemExit("DuckDB is required for Parquet conversion: pip install duckdb") from exc
    files = sorted(RAW_DIR.rglob("*.csv"))
    if not files:
        raise SystemExit("No CSV files found in data/raw; inventory source data before conversion.")
    connection = duckdb.connect()
    for source in files:
        target = PROCESSED_DIR / f"{source.stem}.parquet"
        connection.execute("COPY (SELECT * FROM read_csv_auto(? , header=true)) TO ? (FORMAT PARQUET, COMPRESSION ZSTD)", [str(source), str(target)])
        print(f"{source.name} -> {target.name}")
    connection.close()


if __name__ == "__main__":
    main()
