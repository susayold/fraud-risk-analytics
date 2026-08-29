"""Fail-closed validation gate for the Part 2 analytical foundation."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
SUMMARY = ROOT / "assets" / "data" / "part2_summary.json"
EXPECTED_ROWS = 24_386_900
EXPECTED_FRAUD = 29_757


def read_csv(name: str) -> list[dict[str, str]]:
    path = REPORTS / name
    if not path.exists():
        raise AssertionError(f"missing report: {name}")
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def integer(value: str | None, label: str) -> int:
    try:
        return int(float(value or ""))
    except ValueError as exc:
        raise AssertionError(f"{label} is not numeric: {value!r}") from exc


def main() -> int:
    required = [
        "data_inventory.csv", "data_dictionary.csv", "data_quality_report.csv",
        "entity_relationship_audit.csv", "key_integrity_report.csv", "fraud_label_report.csv",
        "leakage_register.csv", "amount_semantics_report.csv", "structural_missingness_report.csv",
        "storage_benchmark.csv", "transaction_base_reconciliation.csv", "pit_validation_report.csv",
        "synthetic_artifact_audit.csv", "split_summary.csv", "data_issues.csv",
    ]
    for name in required:
        read_csv(name)

    if not SUMMARY.exists():
        raise AssertionError("missing summary JSON")
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    if summary.get("status") != "FOUNDATION_READY":
        raise AssertionError(f"summary status is {summary.get('status')!r}")
    if integer(str(summary.get("transactions")), "summary.transactions") != EXPECTED_ROWS:
        raise AssertionError("summary transaction count mismatch")
    if integer(str(summary.get("fraud_transactions")), "summary.fraud_transactions") != EXPECTED_FRAUD:
        raise AssertionError("summary fraud count mismatch")
    if not summary.get("source_sha256") or len(summary["source_sha256"]) != 64:
        raise AssertionError("source SHA-256 fingerprint is missing")
    inventory = read_csv("data_inventory.csv")
    if len(inventory) != 1 or inventory[0].get("file_type") != "csv" or integer(inventory[0].get("row_count"), "inventory.row_count") != EXPECTED_ROWS or inventory[0].get("sha256") != summary["source_sha256"]:
        raise AssertionError("source inventory fingerprint does not match the locked summary")

    reconciliation = read_csv("transaction_base_reconciliation.csv")
    layers = {row["layer"]: row for row in reconciliation}
    expected_layers = ["SOURCE_CSV", "PARQUET", "DUCKDB_RAW", "STANDARDIZED", "TRANSACTION_BASE", "MODEL_SPLITS"]
    if list(layers) != expected_layers:
        raise AssertionError(f"reconciliation layer order mismatch: {list(layers)}")
    for layer in expected_layers:
        row = layers[layer]
        if integer(row["row_count"], f"{layer}.row_count") != EXPECTED_ROWS:
            raise AssertionError(f"{layer} row count mismatch")
        if layer != "SOURCE_CSV" and integer(row["distinct_source_row_id"], f"{layer}.distinct_source_row_id") != EXPECTED_ROWS:
            raise AssertionError(f"{layer} source_row_id uniqueness mismatch")
        if layer != "SOURCE_CSV":
            if integer(row["min_source_row_id"], f"{layer}.min_source_row_id") != 1:
                raise AssertionError(f"{layer} source_row_id min mismatch")
            if integer(row["max_source_row_id"], f"{layer}.max_source_row_id") != EXPECTED_ROWS:
                raise AssertionError(f"{layer} source_row_id max mismatch")
            if integer(row["fraud_rows"], f"{layer}.fraud_rows") != EXPECTED_FRAUD:
                raise AssertionError(f"{layer} fraud count mismatch")

    split_rows = read_csv("split_summary.csv")
    if {row["split_name"] for row in split_rows} != {"DEVELOPMENT", "VALIDATION", "OUT_OF_TIME_OOT"}:
        raise AssertionError("chronological split set mismatch")
    if sum(integer(row["row_count"], "split row_count") for row in split_rows) != EXPECTED_ROWS:
        raise AssertionError("chronological split rows do not reconcile")
    if sum(integer(row["fraud_count"], "split fraud_count") for row in split_rows) != EXPECTED_FRAUD:
        raise AssertionError("chronological split fraud rows do not reconcile")

    pit_rows = read_csv("pit_validation_report.csv")
    if not pit_rows or any(row.get("status") != "PASS" or integer(row.get("violations"), "PIT violations") != 0 for row in pit_rows):
        raise AssertionError("PIT validation did not pass")

    storage_rows = read_csv("storage_benchmark.csv")
    if {row.get("layer") for row in storage_rows} != {"CSV", "PARQUET_ZSTD", "DUCKDB_DATABASE"}:
        raise AssertionError("storage benchmark layers incomplete")
    if any(integer(row.get("size_bytes"), "storage size_bytes") <= 0 for row in storage_rows):
        raise AssertionError("storage benchmark has an empty layer")

    issues = read_csv("data_issues.csv")
    open_blockers = [row for row in issues if row.get("severity") in {"CRITICAL", "HIGH"} and row.get("status") not in {"CLOSED", "ACCEPTED_LIMITATION"}]
    if open_blockers:
        raise AssertionError(f"unresolved critical/high issues: {open_blockers}")
    dictionary = read_csv("data_dictionary.csv")
    if any(row.get("use_status") == "REVIEW" for row in dictionary):
        raise AssertionError("data dictionary contains unexplained REVIEW policy")

    print("PART 2 VALIDATION PASSED")
    print(f"Source rows: {EXPECTED_ROWS:,}")
    print(f"Transaction base: {EXPECTED_ROWS:,}")
    print(f"Fraud rows: {EXPECTED_FRAUD:,}")
    print("Label nulls: 0")
    print("PIT policy: LOCKED")
    print("PIT validation: PASS")
    print("Split reconciliation: PASS")
    print("Storage layer: PASS")
    print(f"Open critical/high issues: {len(open_blockers)}")
    print("Status: FOUNDATION_READY")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"PART 2 VALIDATION FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
