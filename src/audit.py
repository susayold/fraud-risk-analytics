"""Create auditable Part 2 report shells and summary status after inventory."""

from __future__ import annotations

import csv
from pathlib import Path

from config import REPORTS_DIR


def write_csv(name: str, fields: list[str], rows: list[dict[str, object]]) -> None:
    with (REPORTS_DIR / name).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(rows)


def main() -> None:
    inventory = list(csv.DictReader((REPORTS_DIR / "data_inventory.csv").open(encoding="utf-8")))
    has_source = bool(inventory and inventory[0].get("file_name") != "__NO_RAW_FILES_FOUND__")
    status = "READY_TO_RUN" if has_source else "PENDING"
    write_csv("data_quality_report.csv", ["table_name", "column_name", "check_name", "total_rows", "affected_rows", "affected_pct", "status", "notes"], [{"table_name": "", "column_name": "", "check_name": "inventory prerequisite", "total_rows": "", "affected_rows": "", "affected_pct": "", "status": status, "notes": "Run DuckDB quality SQL after source files are acquired."}])
    write_csv("entity_relationship_audit.csv", ["relationship", "left_table", "right_table", "join_key", "expected_cardinality", "observed_left_rows", "matched_rows", "unmatched_rows", "duplicate_key_rows", "status", "notes"], [{"relationship": "user → card → transaction", "status": status, "notes": "Cardinality is never assumed; populate from key audit SQL."}])
    write_csv("key_integrity_report.csv", ["table_name", "key_name", "total_rows", "distinct_keys", "duplicate_key_rows", "orphan_rows", "status", "notes"], [{"table_name": "", "key_name": "", "status": status, "notes": "Populate from sql/02_key_integrity.sql."}])
    print(f"Audit report shells written with status={status}; no metrics were fabricated.")


if __name__ == "__main__":
    main()
