"""Run the Part 2 audit without loading the transaction file into memory."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from config import RAW_DIR, REPORTS_DIR, SUMMARY_PATH


def write_csv(name: str, fields: list[str], rows: list[dict[str, object]]) -> None:
    with (REPORTS_DIR / name).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def parse_amount(value: str) -> float | None:
    cleaned = re.sub(r"[$, ]", "", value or "")
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None


def parse_day(year: str, month: str, day_value: str) -> date | None:
    try:
        return date(int(year), int(month), int(float(day_value)))
    except (TypeError, ValueError):
        return None


def audit_ibm_csv(path: Path) -> dict[str, object]:
    """Stream the IBM 15-column file and return compact audit statistics."""
    with path.open("r", encoding="utf-8-sig", newline="", errors="replace", buffering=8 * 1024 * 1024) as handle:
        reader = csv.reader(handle)
        columns = next(reader, [])
        positions = {name: index for index, name in enumerate(columns)}
        required = {"User", "Card", "Year", "Month", "Day", "Amount", "Is Fraud?"}
        if not required.issubset(positions):
            raise ValueError(f"Unsupported source schema in {path.name}; missing {sorted(required - set(positions))}")

        row_count = 0
        total_amount = 0.0
        fraud_amount = 0.0
        fraud_transactions = 0
        null_counts = Counter()
        label_counts = Counter()
        invalid_amounts = 0
        invalid_dates = 0
        users: set[str] = set()
        cards: set[tuple[str, str]] = set()
        merchants: set[str] = set()
        daily_rows: Counter[str] = Counter()
        daily_fraud: Counter[str] = Counter()
        daily_fraud_amount: defaultdict[str, float] = defaultdict(float)
        date_min: date | None = None
        date_max: date | None = None

        for row in reader:
            row_count += 1
            if len(row) < len(columns):
                row.extend([""] * (len(columns) - len(row)))
            for index, value in enumerate(row[:len(columns)]):
                if not value.strip():
                    null_counts[columns[index]] += 1
            user = row[positions["User"]].strip()
            card = row[positions["Card"]].strip()
            users.add(user)
            cards.add((user, card))
            if "Merchant Name" in positions and row[positions["Merchant Name"]].strip():
                merchants.add(row[positions["Merchant Name"]].strip())
            amount = parse_amount(row[positions["Amount"]])
            if amount is None:
                invalid_amounts += 1
            else:
                total_amount += amount
            day = parse_day(row[positions["Year"]], row[positions["Month"]], row[positions["Day"]])
            if day is None:
                invalid_dates += 1
                day_key = ""
            else:
                day_key = day.isoformat()
                date_min = day if date_min is None or day < date_min else date_min
                date_max = day if date_max is None or day > date_max else date_max
                daily_rows[day_key] += 1
            label = row[positions["Is Fraud?"]].strip().lower()
            label_counts[label or "<NULL>"] += 1
            if label == "yes":
                fraud_transactions += 1
                if amount is not None:
                    fraud_amount += amount
                    if day_key:
                        daily_fraud_amount[day_key] += amount
                if day_key:
                    daily_fraud[day_key] += 1

    if not row_count:
        raise ValueError(f"Source file is empty: {path}")
    active_dates = sorted(daily_rows)
    return {
        "columns": columns, "rows": row_count, "size_mb": round(path.stat().st_size / 1024 / 1024, 3),
        "users": len(users), "cards": len(cards), "merchants": len(merchants),
        "total_amount": round(total_amount, 2), "fraud_amount": round(fraud_amount, 2),
        "fraud_transactions": fraud_transactions, "fraud_rate": fraud_transactions / row_count,
        "fraud_amount_rate": fraud_amount / total_amount if total_amount else None,
        "null_counts": dict(null_counts), "invalid_amounts": invalid_amounts, "invalid_dates": invalid_dates,
        "label_counts": dict(label_counts), "date_min": date_min.isoformat() if date_min else None,
        "date_max": date_max.isoformat() if date_max else None, "active_days": len(active_dates),
        "daily_rows": dict(daily_rows), "daily_fraud": dict(daily_fraud), "daily_fraud_amount": dict(daily_fraud_amount),
    }


def chronological_splits(stats: dict[str, object]) -> list[dict[str, object]]:
    days = sorted(stats["daily_rows"])
    if len(days) < 3:
        return [{"split_name": "DEVELOPMENT", "date_start": "", "date_end": "", "row_count": "", "fraud_count": "", "status": "PENDING", "notes": "At least three observed dates are required."}]
    validation_index = max(1, int(len(days) * 0.70))
    oot_index = max(validation_index + 1, int(len(days) * 0.85))
    groups = [("DEVELOPMENT", days[:validation_index]), ("VALIDATION", days[validation_index:oot_index]), ("OUT_OF_TIME_OOT", days[oot_index:])]
    return [{"split_name": name, "date_start": group[0], "date_end": group[-1], "row_count": sum(stats["daily_rows"][d] for d in group), "fraud_count": sum(stats["daily_fraud"].get(d, 0) for d in group), "status": "OBSERVED", "notes": "Chronological date split; no random sampling."} for name, group in groups]


def write_observed_reports(path: Path, stats: dict[str, object]) -> None:
    columns = stats["columns"]
    write_csv("data_inventory.csv", ["file_name", "file_type", "file_size_mb", "row_count", "column_count", "primary_grain", "candidate_key", "date_min", "date_max", "notes"], [{"file_name": path.name, "file_type": "csv", "file_size_mb": stats["size_mb"], "row_count": stats["rows"], "column_count": len(columns), "primary_grain": "transaction", "candidate_key": "", "date_min": stats["date_min"], "date_max": stats["date_max"], "notes": "Observed from IBM TabFormer source; no explicit transaction_id column is present."}])
    dictionary_rows = []
    for column in columns:
        dictionary_rows.append({"table_name": path.stem, "column_name": column, "raw_dtype": "string_or_numeric_in_csv", "standardized_dtype": "date" if column in {"Year", "Month", "Day"} else ("numeric" if column in {"User", "Card", "Amount", "Zip", "MCC"} else "string"), "description": "Observed IBM TabFormer field; semantic mapping retained for Part 2.", "grain": "transaction", "nullable": stats["null_counts"].get(column, 0) > 0, "candidate_key": False, "decision_time_available": "review", "target_related": column == "Is Fraud?", "pii_like": column in {"User", "Card", "Zip"}, "use_status": "TARGET_ONLY" if column == "Is Fraud?" else "REVIEW", "reason": "No feature policy is finalized without the T0 review."})
    write_csv("data_dictionary.csv", ["table_name", "column_name", "raw_dtype", "standardized_dtype", "description", "grain", "nullable", "candidate_key", "decision_time_available", "target_related", "pii_like", "use_status", "reason"], dictionary_rows)
    quality_rows = [{"table_name": path.stem, "column_name": column, "check_name": "null_count", "total_rows": stats["rows"], "affected_rows": stats["null_counts"].get(column, 0), "affected_pct": round(stats["null_counts"].get(column, 0) / stats["rows"] * 100, 6), "status": "PASS" if stats["null_counts"].get(column, 0) == 0 else "REVIEW", "notes": "Empty strings counted as nulls."} for column in columns]
    quality_rows += [{"table_name": path.stem, "column_name": "Amount", "check_name": "numeric_parse", "total_rows": stats["rows"], "affected_rows": stats["invalid_amounts"], "affected_pct": round(stats["invalid_amounts"] / stats["rows"] * 100, 6), "status": "PASS" if stats["invalid_amounts"] == 0 else "REVIEW", "notes": "Currency symbols and commas stripped before parse."}, {"table_name": path.stem, "column_name": "Year/Month/Day", "check_name": "valid_date", "total_rows": stats["rows"], "affected_rows": stats["invalid_dates"], "affected_pct": round(stats["invalid_dates"] / stats["rows"] * 100, 6), "status": "PASS" if stats["invalid_dates"] == 0 else "REVIEW", "notes": "Composite transaction date."}]
    write_csv("data_quality_report.csv", ["table_name", "column_name", "check_name", "total_rows", "affected_rows", "affected_pct", "status", "notes"], quality_rows)
    write_csv("key_integrity_report.csv", ["table_name", "key_name", "total_rows", "distinct_keys", "duplicate_key_rows", "orphan_rows", "status", "notes"], [{"table_name": path.stem, "key_name": "User", "total_rows": stats["rows"], "distinct_keys": stats["users"], "duplicate_key_rows": "not_applicable_transaction_grain", "orphan_rows": "not_available_denormalized_source", "status": "REVIEW", "notes": "User repeats by design; no separate user dimension supplied."}, {"table_name": path.stem, "key_name": "User + Card", "total_rows": stats["rows"], "distinct_keys": stats["cards"], "duplicate_key_rows": "not_applicable_transaction_grain", "orphan_rows": "not_available_denormalized_source", "status": "REVIEW", "notes": "Composite card entity key; card repeats across transactions."}])
    write_csv("entity_relationship_audit.csv", ["relationship", "left_table", "right_table", "join_key", "expected_cardinality", "observed_left_rows", "matched_rows", "unmatched_rows", "duplicate_key_rows", "status", "notes"], [{"relationship": "user → card → transaction", "left_table": "users/cards", "right_table": path.stem, "join_key": "User + Card", "expected_cardinality": "1-to-many", "observed_left_rows": stats["cards"], "matched_rows": stats["rows"], "unmatched_rows": "not_available", "duplicate_key_rows": "not_applicable_transaction_grain", "status": "OBSERVED_WITH_LIMITATION", "notes": "Source is denormalized; no standalone dimension tables."}])
    fraud_rows = [{"metric": "label_count", "label": label, "transaction_count": count, "amount": "", "rate": round(count / stats["rows"], 8), "status": "OBSERVED", "notes": "Exact source label value."} for label, count in sorted(stats["label_counts"].items())]
    fraud_rows.append({"metric": "fraud_amount_rate", "label": "Yes", "transaction_count": stats["fraud_transactions"], "amount": stats["fraud_amount"], "rate": stats["fraud_amount_rate"], "status": "OBSERVED", "notes": "Fraud amount divided by total parsed transaction amount."})
    write_csv("fraud_label_report.csv", ["metric", "label", "transaction_count", "amount", "rate", "status", "notes"], fraud_rows)
    write_csv("leakage_register.csv", ["field_or_feature", "role", "decision_time_rule", "status", "notes"], [{"field_or_feature": "Is Fraud?", "role": "target", "decision_time_rule": "never a feature", "status": "TARGET_ONLY", "notes": "Observed target label."}, {"field_or_feature": "post_event_outcome", "role": "post-event", "decision_time_rule": "exclude", "status": "EXCLUDE", "notes": "Not supplied as a source feature."}, {"field_or_feature": "historical_aggregate", "role": "derived", "decision_time_rule": "strict prior timestamp only", "status": "DERIVE", "notes": "Use point-in-time join."}, {"field_or_feature": "User/Card/Zip", "role": "identifier_like", "decision_time_rule": "review necessity and handling", "status": "REVIEW", "notes": "Synthetic identifiers; no raw identifier claim is made."}])
    write_csv("split_summary.csv", ["split_name", "date_start", "date_end", "row_count", "fraud_count", "status", "notes"], chronological_splits(stats))
    write_csv("data_issues.csv", ["issue_id", "severity", "status", "area", "description", "recommended_action"], [{"issue_id": "P2-001", "severity": "INFO", "status": "CLOSED", "area": "source", "description": "Raw IBM transaction archive acquired and audited outside repository storage.", "recommended_action": "Keep raw archive on Drive; use temporary processing only."}, {"issue_id": "P2-002", "severity": "MEDIUM", "status": "OPEN", "area": "keys", "description": "Source has no explicit transaction_id; transaction grain is represented by file row.", "recommended_action": "Create a documented surrogate row id only for analytical processing."}, {"issue_id": "P2-003", "severity": "MEDIUM", "status": "OPEN", "area": "schema", "description": "Source is denormalized; standalone user/card/merchant dimension tables are not supplied.", "recommended_action": "Treat User + Card as an observed composite entity key and document join limitations."}])
    summary = {"status": "READY", "source": "IBM Synthetic Credit Card Transactions", "source_file": path.name, "transactions": stats["rows"], "users": stats["users"], "cards": stats["cards"], "merchants": stats["merchants"], "fraud_transactions": stats["fraud_transactions"], "fraud_rate": stats["fraud_rate"], "fraud_amount_rate": stats["fraud_amount_rate"], "date_min": stats["date_min"], "date_max": stats["date_max"], "active_days": stats["active_days"], "split_status": "OBSERVED_CHRONOLOGICAL_SPLITS", "splits": chronological_splits(stats), "total_amount": stats["total_amount"], "fraud_amount": stats["fraud_amount"]}
    with SUMMARY_PATH.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
    print(json.dumps(summary, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Stream the Part 2 source audit.")
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR, help="Directory containing the source CSV; may be temporary.")
    args = parser.parse_args()
    files = sorted(args.raw_dir.rglob("*.csv"))
    if not files:
        write_csv("data_quality_report.csv", ["table_name", "column_name", "check_name", "total_rows", "affected_rows", "affected_pct", "status", "notes"], [{"table_name": "", "column_name": "", "check_name": "inventory prerequisite", "total_rows": "", "affected_rows": "", "affected_pct": "", "status": "PENDING", "notes": "No source CSV found."}])
        print("No source CSV found; audit remains pending.")
        return
    if len(files) > 1:
        raise ValueError("Expected one IBM transaction CSV; pass a directory containing only the selected source.")
    write_observed_reports(files[0], audit_ibm_csv(files[0]))


if __name__ == "__main__":
    main()
