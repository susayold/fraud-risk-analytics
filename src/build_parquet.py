"""Convert the exact IBM source contract to Parquet with source_row_id."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from config import PROCESSED_DIR, RAW_DIR

CONTRACT = Path(__file__).resolve().parents[1] / "config" / "source_contract.json"


def validate_source_header(source_file: Path) -> list[str]:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    with source_file.open("r", encoding="utf-8-sig", newline="", errors="replace") as handle:
        actual = next(csv.reader(handle), [])
    expected = contract["expected_columns"]
    if actual != expected:
        raise ValueError(f"Source contract mismatch. Expected {expected}; received {actual}.")
    return actual


def convert_csv_to_parquet(source_file: Path, output_dir: Path) -> Path:
    try:
        import duckdb
    except ImportError as exc:
        raise SystemExit("DuckDB is required: python -m pip install duckdb") from exc
    validate_source_header(source_file)
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / "card_transactions.parquet"
    db = duckdb.connect()
    # DuckDB accepts a parameter for the source reader but treats a parameterized
    # COPY destination as a glob. Quote the validated temporary destination instead.
    destination = str(target).replace("'", "''")
    db.execute(f"COPY (SELECT ROW_NUMBER() OVER () AS source_row_id, * FROM read_csv_auto(?, header=true)) TO '{destination}' (FORMAT PARQUET, COMPRESSION ZSTD)", [str(source_file)])
    db.close()
    return target


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-file", type=Path)
    parser.add_argument("--output-dir", type=Path, default=PROCESSED_DIR)
    args = parser.parse_args()
    source = args.source_file
    if source is None:
        files = sorted(RAW_DIR.glob("*.csv"))
        if len(files) != 1:
            raise SystemExit("Pass --source-file explicitly; exactly one source CSV is required.")
        source = files[0]
    target = convert_csv_to_parquet(source, args.output_dir)
    print(f"{source.name} -> {target} (source_row_id 1..N)")


if __name__ == "__main__":
    main()
