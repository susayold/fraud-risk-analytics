"""Write a reproducible storage benchmark for the temporary pipeline run."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-file", type=Path, required=True)
    parser.add_argument("--parquet-file", type=Path, required=True)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--parquet-seconds", type=float, default=0.0)
    parser.add_argument("--duckdb-seconds", type=float, default=0.0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = [{"layer": "CSV", "size_bytes": args.source_file.stat().st_size, "size_mb": round(args.source_file.stat().st_size / 1024 / 1024, 3), "elapsed_seconds": "", "compression": "none", "methodology": "Source file size."}, {"layer": "PARQUET_ZSTD", "size_bytes": args.parquet_file.stat().st_size, "size_mb": round(args.parquet_file.stat().st_size / 1024 / 1024, 3), "elapsed_seconds": args.parquet_seconds, "compression": "ZSTD", "methodology": "DuckDB COPY with ROW_NUMBER source_row_id."}, {"layer": "DUCKDB_DATABASE", "size_bytes": args.database.stat().st_size, "size_mb": round(args.database.stat().st_size / 1024 / 1024, 3), "elapsed_seconds": args.duckdb_seconds, "compression": "DuckDB storage", "methodology": "DuckDB raw + audit + analytics tables."}]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


if __name__ == "__main__":
    main()
