"""Inventory source files without loading a large transaction file into pandas."""

from __future__ import annotations

import csv
import json
import re
from datetime import datetime
from pathlib import Path

from config import RAW_DIR, REPORTS_DIR, SUMMARY_PATH

DATE_HINTS = ("timestamp", "datetime", "date", "time", "trans_date")
KEY_HINTS = ("transaction_id", "trans_id", "card_id", "user_id", "customer_id", "merchant_id")


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def parse_date(value: str) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y", "%m/%d/%Y %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    return None


def inspect_csv(path: Path) -> tuple[list[str], int, str | None, str | None]:
    with path.open("r", encoding="utf-8-sig", newline="", errors="replace") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        date_column = next((c for c in columns if any(h in normalize(c) for h in DATE_HINTS)), None)
        row_count = 0
        dates: list[datetime] = []
        for row in reader:
            row_count += 1
            if date_column:
                parsed = parse_date(row.get(date_column, ""))
                if parsed:
                    dates.append(parsed)
    return columns, row_count, min(dates).date().isoformat() if dates else None, max(dates).date().isoformat() if dates else None


def candidate_key(columns: list[str]) -> str:
    normalized = {normalize(c): c for c in columns}
    for hint in KEY_HINTS:
        if hint in normalized:
            return normalized[hint]
    return next((c for c in columns if normalize(c).endswith("_id")), "")


def primary_grain(path: Path) -> str:
    name = path.stem.lower()
    if any(token in name for token in ("transaction", "trans")):
        return "transaction"
    if any(token in name for token in ("user", "customer", "consumer")):
        return "user"
    if "card" in name:
        return "card"
    if any(token in name for token in ("fraud", "label", "target")):
        return "fraud_label"
    return "unknown_until_schema_audit"


def main() -> None:
    files = sorted(p for p in RAW_DIR.rglob("*") if p.is_file() and p.suffix.lower() in {".csv", ".parquet"})
    inventory: list[dict[str, object]] = []
    dictionary: list[dict[str, object]] = []
    for path in files:
        relative = path.relative_to(RAW_DIR).as_posix()
        if path.suffix.lower() == ".csv":
            columns, rows, date_min, date_max = inspect_csv(path)
        else:
            columns, rows, date_min, date_max = [], "", None, None
        inventory.append({
            "file_name": relative,
            "file_type": path.suffix.lower().lstrip("."),
            "file_size_mb": round(path.stat().st_size / 1024 / 1024, 3),
            "row_count": rows,
            "column_count": len(columns),
            "primary_grain": primary_grain(path),
            "candidate_key": candidate_key(columns),
            "date_min": date_min or "",
            "date_max": date_max or "",
            "notes": "Row/date inspection is source-derived; verify Parquet metadata with DuckDB when present.",
        })
        for column in columns:
            name = normalize(column)
            target_related = "true" if "fraud" in name or "label" in name else "false"
            use_status = "TARGET_ONLY" if target_related == "true" else "REVIEW"
            dictionary.append({"table_name": path.stem, "column_name": column, "raw_dtype": "inferred_by_duckdb_or_source", "standardized_dtype": "pending", "description": "Pending semantic review after inventory", "grain": primary_grain(path), "nullable": "unknown", "candidate_key": column == candidate_key(columns), "decision_time_available": "review", "target_related": target_related, "pii_like": "review", "use_status": use_status, "reason": "Do not finalize feature policy before schema and T0 audit."})

    if not inventory:
        inventory = [{"file_name": "__NO_RAW_FILES_FOUND__", "file_type": "", "file_size_mb": "", "row_count": "", "column_count": "", "primary_grain": "", "candidate_key": "", "date_min": "", "date_max": "", "notes": "Raw dataset is not present in data/raw; run this script after acquisition."}]

    fields = ["file_name", "file_type", "file_size_mb", "row_count", "column_count", "primary_grain", "candidate_key", "date_min", "date_max", "notes"]
    with (REPORTS_DIR / "data_inventory.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(inventory)
    dictionary_fields = ["table_name", "column_name", "raw_dtype", "standardized_dtype", "description", "grain", "nullable", "candidate_key", "decision_time_available", "target_related", "pii_like", "use_status", "reason"]
    with (REPORTS_DIR / "data_dictionary.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=dictionary_fields); writer.writeheader(); writer.writerows(dictionary)

    summary = {"status": "READY_FOR_AUDIT" if files else "PENDING_DATA_INVENTORY", "source": "IBM Synthetic Credit Card Transactions", "transactions": None, "users": None, "cards": None, "fraud_transactions": None, "fraud_rate": None, "fraud_amount_rate": None, "date_min": None, "date_max": None, "active_days": None, "split_status": "NOT_DEFINED_UNTIL_DATE_AUDIT"}
    with SUMMARY_PATH.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
    print(f"Inventoried {len(files)} raw data files; wrote {REPORTS_DIR / 'data_inventory.csv'}")


if __name__ == "__main__":
    main()
