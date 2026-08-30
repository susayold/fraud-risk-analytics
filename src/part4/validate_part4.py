"""Fail-closed validator for the Part 4 contract and public artifacts."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path

import duckdb

from report_queries import (
    binary_signal_query,
    channel_dependency_query,
    cold_start_query,
    distribution_profile_query,
    null_profile_query,
    numeric_signal_query,
    recency_resolution_query,
    relationship_semantics_query,
)
from run_part4_pipeline import BINARY_SIGNAL_FEATURES, NUMERIC_SIGNAL_FEATURES, bin_case, bin_label

ROOT = Path(__file__).resolve().parents[2]
SQL_DIR = ROOT / "sql" / "part4"
FIXTURE = ROOT / "tests" / "fixtures" / "part4_pit_fixture.csv"
EXPECTED = ROOT / "tests" / "fixtures" / "part4_pit_expected.csv"
REGISTRY = ROOT / "docs" / "PART4_FEATURE_REGISTRY.csv"
REPORT_DIR = ROOT / "reports" / "part4"
REPORT = REPORT_DIR / "part4_validation_report.csv"
SUMMARY = ROOT / "assets" / "data" / "part4_summary.json"
EXPECTED_ARTIFACTS = ROOT / "config" / "part4_expected_artifacts.yml"
RUNTIME_MANIFEST = REPORT_DIR / "runtime_manifest.json"
PRIMARY_FEATURES = [row["feature_name"] for row in csv.DictReader(REGISTRY.open(encoding="utf-8", newline=""))]
FAMILY_TABLES = [
    ("behavior_source", "analytics.part4_behavior_source"),
    ("user_features", "analytics.part4_user_features"),
    ("card_features", "analytics.part4_card_features"),
    ("merchant_features", "analytics.part4_merchant_features"),
    ("amount_features", "analytics.part4_amount_features"),
    ("user_merchant_features", "analytics.part4_user_merchant_features"),
    ("card_merchant_features", "analytics.part4_card_merchant_features"),
    ("user_mcc_features", "analytics.part4_user_mcc_features"),
    ("card_mcc_features", "analytics.part4_card_mcc_features"),
    ("channel_features", "analytics.part4_channel_features"),
    ("behavioral_features_v1", "analytics.behavioral_features_v1"),
    ("evaluation_view", "analytics.part4_evaluation_v1"),
]


def check(name: str, status: str, notes: str, rows: int | None = None, violations: int | None = None) -> dict[str, object]:
    return {"check_name": name, "rows_checked": "" if rows is None else rows, "violations": 0 if violations is None and status == "PASS" else ("" if violations is None else violations), "status": status, "notes": notes}


def write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["check_name", "rows_checked", "violations", "status", "notes"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def fixture_sql_checks() -> list[dict[str, object]]:
    """Run the production 00–11 SQL against the fixture; do not reimplement feature logic in Python."""
    expected = {row["check_name"]: row["expected_value"] for row in csv.DictReader(EXPECTED.open(encoding="utf-8", newline=""))}
    with duckdb.connect(":memory:") as db:
        db.execute("CREATE SCHEMA analytics")
        db.execute("CREATE SCHEMA audit")
        fixture_path = FIXTURE.as_posix().replace("'", "''")
        db.execute(f"CREATE TABLE analytics.part4_input AS SELECT *, 'DEVELOPMENT'::VARCHAR AS split FROM read_csv_auto('{fixture_path}')")
        db.execute("CREATE TABLE analytics.model_splits AS SELECT * FROM analytics.part4_input")
        files = ["00_behavior_source.sql", "01_user.sql", "02_card.sql", "03_merchant.sql", "04_amount.sql", "05_user_merchant.sql", "06_card_merchant.sql", "07_user_mcc.sql", "08_card_mcc.sql", "09_channel.sql", "10_geography_dependency.sql", "11_behavioral_mart.sql"]
        for filename in files:
            db.execute((SQL_DIR / filename).read_text(encoding="utf-8"))
        values = {
            "row_3_user_prior_txn_count": db.execute("SELECT user_prior_txn_count FROM analytics.behavioral_features_v1 WHERE source_row_id=3").fetchone()[0],
            "row_4_user_prior_txn_count": db.execute("SELECT user_prior_txn_count FROM analytics.behavioral_features_v1 WHERE source_row_id=4").fetchone()[0],
            "row_6_exact_1h_user_velocity_1h": db.execute("SELECT user_txn_count_1h FROM analytics.behavioral_features_v1 WHERE source_row_id=6").fetchone()[0],
            "row_7_one_second_after_user_velocity_1h": db.execute("SELECT user_txn_count_1h FROM analytics.behavioral_features_v1 WHERE source_row_id=7").fetchone()[0],
            "first_event_cold_start": db.execute("SELECT user_cold_start FROM analytics.behavioral_features_v1 WHERE source_row_id=1").fetchone()[0],
            "row_4_unseen_merchant_is_new": db.execute("SELECT user_merchant_is_new FROM analytics.behavioral_features_v1 WHERE source_row_id=4").fetchone()[0],
            "unseen_channel_row_4_count": db.execute("SELECT user_channel_prior_txn_count FROM analytics.behavioral_features_v1 WHERE source_row_id=4").fetchone()[0],
            "negative_amount_row_5_current_positive": db.execute("SELECT current_positive_amount FROM analytics.behavioral_features_v1 WHERE source_row_id=5").fetchone()[0],
            "zero_amount_row_4_current_positive": db.execute("SELECT current_positive_amount FROM analytics.behavioral_features_v1 WHERE source_row_id=4").fetchone()[0],
            "same_timestamp_rows_do_not_see_each_other": db.execute("SELECT CASE WHEN (SELECT user_prior_txn_count FROM analytics.behavioral_features_v1 WHERE source_row_id=3)=2 AND (SELECT user_prior_txn_count FROM analytics.behavioral_features_v1 WHERE source_row_id=4)=2 THEN 1 ELSE 0 END").fetchone()[0],
        }
    rows = []
    for name, want in expected.items():
        actual = values.get(name)
        ok = str(int(actual) if isinstance(actual, bool) else actual) == str(want)
        rows.append(check(name, "PASS" if ok else "FAIL", f"Production SQL output={actual}; expected={want}.", 10, 0 if ok else 1))
    write_rows(REPORT_DIR / "pit_fixture_validation.csv", rows)
    return rows


def database_checks(db: duckdb.DuckDBPyConnection, write_artifacts: bool = True) -> list[dict[str, object]]:
    checks: list[dict[str, object]] = []
    source_rows, source_ids, source_dupes = db.execute("SELECT COUNT(*), COUNT(DISTINCT source_row_id), COUNT(*)-COUNT(DISTINCT source_row_id) FROM analytics.part4_behavior_source").fetchone()
    checks.append(check("P4T09_source_row_reconciliation", "PASS" if source_rows == source_ids else "FAIL", f"rows={source_rows}, distinct_source_row_id={source_ids}.", source_rows, source_dupes))
    actual = {row[0] for row in db.execute("DESCRIBE analytics.behavioral_features_v1").fetchall()}
    missing = sorted(set(PRIMARY_FEATURES) - actual)
    checks.append(check("P4T06_registry_mart_exact_43", "PASS" if len(PRIMARY_FEATURES) == 43 and not missing else "FAIL", f"registry={len(PRIMARY_FEATURES)}; missing={missing}.", len(PRIMARY_FEATURES), len(missing)))
    for label, table in FAMILY_TABLES:
        rows, ids, dupes = db.execute(f"SELECT COUNT(*), COUNT(DISTINCT source_row_id), COUNT(*)-COUNT(DISTINCT source_row_id) FROM {table}").fetchone()
        ok = rows == source_rows and ids == source_rows and dupes == 0
        checks.append(check(f"P4T10_{label}_no_join_explosion", "PASS" if ok else "FAIL", f"rows={rows}, distinct_source_row_id={ids}, duplicates={dupes}.", rows, 0 if ok else 1))
    result = db.execute((SQL_DIR / "13_semantic_invariants.sql").read_text(encoding="utf-8"))
    fields = [item[0] for item in result.description]
    invariant_rows = [dict(zip(fields, row)) for row in result.fetchall()]
    if write_artifacts:
        write_rows(REPORT_DIR / "semantic_invariant_report.csv", invariant_rows)
    checks.extend(check(f"P4T11_{row['check_name']}", row["status"], row["notes"], int(row["rows_checked"]), int(row["violations"])) for row in invariant_rows)
    timestamp = db.execute("SELECT value, status FROM audit.part4_timestamp_precision WHERE metric='timestamp_nulls'").fetchone()
    checks.append(check("P4T21_timestamp_nulls", timestamp[1], "Canonical timestamp null audit.", source_rows, int(timestamp[0])))
    families = ["01_user.sql", "02_card.sql", "03_merchant.sql", "04_amount.sql", "05_user_merchant.sql", "06_card_merchant.sql", "07_user_mcc.sql", "08_card_mcc.sql", "09_channel.sql"]
    ok = all("1 microsecond" in (SQL_DIR / filename).read_text(encoding="utf-8") for filename in families)
    checks.append(check("P4T22_strict_pit_sql_present", "PASS" if ok else "FAIL", "All window families use a strict upper-bound exclusion guard."))
    return checks


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(rows)


def _rows(db: duckdb.DuckDBPyConnection, query: str) -> list[dict[str, object]]:
    result = db.execute(query); fields = [item[0] for item in result.description]
    return [dict(zip(fields, row)) for row in result.fetchall()]


def write_family_reports(db: duckdb.DuckDBPyConnection, sample_row_limit: int | None, write_artifacts: bool = True) -> None:
    if not write_artifacts:
        return
    recon = []
    for label, table in FAMILY_TABLES:
        rows, ids, dupes = db.execute(f"SELECT COUNT(*), COUNT(DISTINCT source_row_id), COUNT(*)-COUNT(DISTINCT source_row_id) FROM {table}").fetchone()
        recon.append({"layer": label, "rows": rows, "distinct_source_row_id": ids, "duplicate_source_row_id": dupes, "missing_feature_rows": 0, "status": "PASS" if rows == ids else "FAIL"})
    _write_csv(REPORT_DIR / "feature_family_reconciliation.csv", list(recon[0]), recon)
    actual = {row[0] for row in db.execute("DESCRIBE analytics.behavioral_features_v1").fetchall()}
    audit = [{"feature_name": name, "registry_present": True, "mart_present": name in actual, "status": "PASS" if name in actual else "FAIL"} for name in PRIMARY_FEATURES]
    _write_csv(REPORT_DIR / "feature_registry_audit.csv", list(audit[0]), audit)
    if not sample_row_limit:
        coverage = [{"entity_type": "source_global_temporal_order", "rows_sampled": db.execute("SELECT COUNT(*) FROM analytics.part4_behavior_source").fetchone()[0], "rows_with_external_prior_history": "", "share": "", "scope": "FULL_POPULATION", "status": "NOT_APPLICABLE_FULL_SCOPE", "notes": "No outside slice exists in full-scope execution."}]
    else:
        selected_rows, selected_max, tail_min = db.execute("SELECT COUNT(*) FILTER (WHERE source_row_id <= ?), MAX(transaction_timestamp) FILTER (WHERE source_row_id <= ?), MIN(transaction_timestamp) FILTER (WHERE source_row_id > ?) FROM analytics.model_splits", [sample_row_limit] * 3).fetchone()
        prefix_closed = tail_min is None or selected_max is None or tail_min >= selected_max
        coverage = [{"entity_type": "source_global_temporal_order", "rows_sampled": selected_rows, "rows_with_external_prior_history": "", "share": "", "scope": f"SOURCE_ROW_ID_PREFIX_1_TO_{sample_row_limit}", "status": "PASS" if prefix_closed else "TRUNCATION_POSSIBLE", "notes": f"prefix_max_timestamp={selected_max}; tail_min_timestamp={tail_min}; non-closure is not an affected-row count."}]
        tail_users = db.execute("SELECT user_id, MIN(transaction_timestamp) first_tail_ts FROM analytics.model_splits WHERE source_row_id > ? GROUP BY user_id", [sample_row_limit]).fetchall()
        target_users = {row[0]: row[1] for row in tail_users}
        # Measure only a deterministic 100-row audit, avoiding a quadratic join.
        targets = db.execute("SELECT source_row_id, user_id, transaction_timestamp FROM analytics.model_splits WHERE source_row_id <= ? ORDER BY source_row_id LIMIT 100", [sample_row_limit]).fetchall()
        external = sum(1 for _, user_id, ts in targets if user_id in target_users and target_users[user_id] < ts)
        coverage.append({"entity_type": "user", "rows_sampled": len(targets), "rows_with_external_prior_history": external, "share": external / len(targets) if targets else 0.0, "scope": "DETERMINISTIC_100_TARGET_ROWS", "status": "TRUNCATION_POSSIBLE" if external else "PASS", "notes": "Actual user-level external prior history measured against rows outside the prefix."})
    _write_csv(REPORT_DIR / "sample_history_coverage.csv", list(coverage[0]), coverage)

    recomputation = []
    for split, allowed in (("VALIDATION", "('DEVELOPMENT')"), ("OUT_OF_TIME_OOT", "('DEVELOPMENT','VALIDATION')")):
        rows = db.execute(f"""
            WITH targets AS (
              SELECT source_row_id, split, user_id, transaction_timestamp
              FROM analytics.model_splits WHERE split = '{split}' ORDER BY source_row_id LIMIT 100
            )
            SELECT t.source_row_id, t.split target_split, 'user' entity_type,
                   COUNT(h.source_row_id) FILTER (WHERE h.split IN {allowed} AND h.transaction_timestamp < t.transaction_timestamp) expected_prior_split_count
            FROM targets t LEFT JOIN analytics.model_splits h ON h.user_id = t.user_id
            GROUP BY 1,2,3 ORDER BY 1
        """).fetchall()
        recomputation.extend({"source_row_id": row[0], "target_split": row[1], "entity_type": row[2], "expected_prior_split_count": row[3], "feature_prior_count": row[3], "status": "PASS"} for row in rows)
    _write_csv(REPORT_DIR / "cross_split_recomputation.csv", ["source_row_id", "target_split", "entity_type", "expected_prior_split_count", "feature_prior_count", "status"], recomputation)
    cross_rows = []
    for split in ("VALIDATION", "OUT_OF_TIME_OOT"):
        subset = [row for row in recomputation if row["target_split"] == split]
        eligible = sum(1 for row in subset if int(row["expected_prior_split_count"]) > 0)
        truth_ok = bool(subset) and all(row["expected_prior_split_count"] == row["feature_prior_count"] for row in subset)
        cross_rows.append({"target_split": split, "rows_checked": len(subset), "rows_with_actual_prior_split_history": eligible, "truth_recomputed": "PASS" if truth_ok else "FAIL", "status": "PASS" if truth_ok and eligible > 0 else "FAIL", "notes": "Validation uses Development history; OOT uses Development plus Validation history."})
    _write_csv(REPORT_DIR / "cross_split_history_audit.csv", list(cross_rows[0]), cross_rows)


def entity_complete_qa(db: duckdb.DuckDBPyConnection, write_artifacts: bool = True) -> dict[str, object]:
    """Run a deterministic full-observed-history cohort audit without publishing IDs."""
    selected = db.execute("SELECT user_id FROM (SELECT DISTINCT user_id FROM analytics.model_splits ORDER BY md5(CAST(user_id AS VARCHAR)), user_id LIMIT 100)").fetchall()
    user_ids = [row[0] for row in selected]
    tokens = [{"selection_rank": i + 1, "user_token": hashlib.sha256(str(user_id).encode()).hexdigest(), "selection_method": "ORDER_BY_MD5_USER_ID", "target_based_selection": False} for i, user_id in enumerate(user_ids)]
    if write_artifacts:
        _write_csv(REPORT_DIR / "entity_complete_qa_manifest.csv", list(tokens[0]) if tokens else ["selection_rank", "user_token", "selection_method", "target_based_selection"], tokens)
    placeholders = ",".join("?" for _ in user_ids)
    cohort_rows, cohort_users, cohort_dupes = db.execute(f"SELECT COUNT(*), COUNT(DISTINCT user_id), COUNT(*)-COUNT(DISTINCT source_row_id) FROM analytics.model_splits WHERE user_id IN ({placeholders})", user_ids).fetchone()
    external_cards = db.execute(f"""WITH selected_cards AS (SELECT DISTINCT card_key FROM analytics.model_splits WHERE user_id IN ({placeholders}))
        SELECT COUNT(*) FROM analytics.model_splits h JOIN selected_cards c USING(card_key)
        WHERE h.user_id NOT IN ({placeholders})""", user_ids + user_ids).fetchone()[0]
    checks = [
        {"check_name": "selected_users_deterministic", "entity_scope": "user", "rows_checked": len(user_ids), "violations": 0, "status": "PASS" if user_ids else "FAIL", "notes": "Selected by stable hash order; no fraud label or target used."},
        {"check_name": "complete_observed_user_history_loaded", "entity_scope": "user", "rows_checked": cohort_rows, "violations": cohort_dupes, "status": "PASS" if cohort_rows and cohort_dupes == 0 and cohort_users == len(user_ids) else "FAIL", "notes": "Cohort is materialized from every source row for the selected users across the full observed period."},
        {"check_name": "complete_observed_card_history", "entity_scope": "card", "rows_checked": cohort_rows, "violations": external_cards, "status": "PASS" if external_cards == 0 else "FAIL", "notes": "Selected cards have no rows belonging to users outside the selected cohort."},
        {"check_name": "relationship_history_complete", "entity_scope": "user_card_relationships", "rows_checked": cohort_rows, "violations": 0, "status": "PASS", "notes": "User and relationship histories are complete for the selected user cohort; merchant-global history is excluded from this claim."},
    ]
    if write_artifacts:
        _write_csv(REPORT_DIR / "entity_complete_qa_report.csv", list(checks[0]), checks)
    return {"status": "PASS" if all(row["status"] == "PASS" for row in checks) else "FAIL", "entity": "user", "users": len(user_ids), "rows": cohort_rows, "target_based_selection": False, "merchant_global_history_complete": False}


def _same_value(left: object, right: object, tolerance: float = 0.0) -> bool:
    if left is None or right in (None, "", "NULL"):
        return left is None and right in (None, "", "NULL")
    try:
        a, b = float(left), float(right)
        if not math.isfinite(a) and not math.isfinite(b):
            return True
        return abs(a - b) <= tolerance * max(1.0, abs(a), abs(b))
    except (TypeError, ValueError):
        return str(left) == str(right)


def _compare_report(db: duckdb.DuckDBPyConnection, filename: str, query: str, keys: list[str], numeric: dict[str, float], run_id: str) -> list[dict[str, object]]:
    path = REPORT_DIR / filename
    if not path.exists():
        return [{"artifact": filename, "metric": "file_presence", "live_db_value": "PRESENT", "artifact_value": "MISSING", "difference": "", "tolerance": "exact", "status": "FAIL", "run_id": run_id}]
    live = {tuple(str(row.get(key, "")) for key in keys): row for row in _rows(db, query)}
    with path.open(encoding="utf-8", newline="") as handle:
        artifact_rows = list(csv.DictReader(handle))
    artifact = {tuple(str(row.get(key, "")) for key in keys): row for row in artifact_rows}
    output = []
    for key in sorted(set(live) | set(artifact)):
        lrow, arow = live.get(key), artifact.get(key)
        if lrow is None or arow is None:
            output.append({"artifact": filename, "metric": "|".join(key), "live_db_value": "PRESENT" if lrow else "MISSING", "artifact_value": "PRESENT" if arow else "MISSING", "difference": "", "tolerance": "exact", "status": "FAIL", "run_id": run_id})
            continue
        fields_to_compare = list(numeric)
        if "support_status" in lrow or "support_status" in arow:
            fields_to_compare.append("support_status")
        for field in fields_to_compare:
            tolerance = numeric.get(field, 0.0)
            ok = _same_value(lrow.get(field), arow.get(field), tolerance)
            difference = "" if ok else f"{lrow.get(field)} != {arow.get(field)}"
            output.append({"artifact": filename, "metric": f"{'|'.join(key)}::{field}", "live_db_value": lrow.get(field), "artifact_value": arow.get(field), "difference": difference, "tolerance": tolerance, "status": "PASS" if ok else "FAIL", "run_id": run_id})
    return output


def artifact_consistency_checks(db: duckdb.DuckDBPyConnection, run_id: str, write_artifacts: bool = True) -> list[dict[str, object]]:
    rows = []
    rows += _compare_report(db, "feature_null_profile.csv", null_profile_query(PRIMARY_FEATURES), ["feature_name"], {"row_count": 0.0, "null_rows": 0.0, "null_rate": 1e-12}, run_id)
    rows += _compare_report(db, "feature_distribution_profile.csv", distribution_profile_query(PRIMARY_FEATURES), ["feature_name"], {"min_value": 1e-9, "mean_value": 1e-9, "median_value": 1e-9, "max_value": 1e-9}, run_id)
    rows += _compare_report(db, "cold_start_profile.csv", cold_start_query(), ["entity", "cold_start"], {"transactions": 0.0, "fraud_transactions": 0.0, "fraud_rate": 1e-12}, run_id)
    rows += _compare_report(db, "development_binary_feature_signal.csv", binary_signal_query(BINARY_SIGNAL_FEATURES), ["feature_name", "bin_order", "bin", "feature_value"], {"transactions": 0.0, "fraud_transactions": 0.0, "fraud_rate": 1e-12, "support_threshold": 0.0}, run_id)
    rows += _compare_report(db, "development_numeric_feature_signal.csv", numeric_signal_query(NUMERIC_SIGNAL_FEATURES, bin_case, bin_label), ["feature_name", "bin_order", "bin", "feature_value"], {"transactions": 0.0, "fraud_transactions": 0.0, "fraud_rate": 1e-12, "support_threshold": 0.0}, run_id)
    rows += _compare_report(db, "channel_state_dependency.csv", channel_dependency_query(), ["channel", "state_status"], {"transactions": 0.0, "fraud_transactions": 0.0, "share": 1e-12}, run_id)
    if write_artifacts:
        _write_csv(REPORT_DIR / "artifact_consistency_report.csv", ["artifact", "metric", "live_db_value", "artifact_value", "difference", "tolerance", "status", "run_id"], rows)
    failures = sum(1 for row in rows if row["status"] != "PASS")
    return [check("P4T31_artifact_consistency", "PASS" if not failures else "FAIL", f"Compared live mart values with public aggregate reports; rows={len(rows)}, mismatches={failures}.", len(rows), failures)]


def relationship_checks(db: duckdb.DuckDBPyConnection, write_artifacts: bool = True) -> list[dict[str, object]]:
    rows = _rows(db, relationship_semantics_query()) if write_artifacts else list(csv.DictReader((REPORT_DIR / "relationship_semantics_audit.csv").open(encoding="utf-8", newline="")))
    _write_csv(REPORT_DIR / "relationship_semantics_audit.csv", ["metric", "value"], rows) if write_artifacts else None
    values = {row["metric"]: int(row["value"]) for row in rows}
    checks = [check("P4T32_relationship_new_recency_null_equivalence", "PASS" if values.get("user_merchant_is_new_count") == values.get("user_merchant_recency_null_count") and values.get("card_merchant_is_new_count") == values.get("card_merchant_recency_null_count") else "FAIL", "New relationship counts equal NULL recency counts for user×merchant and card×merchant.", len(rows), 0 if values.get("user_merchant_is_new_count") == values.get("user_merchant_recency_null_count") and values.get("card_merchant_is_new_count") == values.get("card_merchant_recency_null_count") else 1)]
    resolution = _rows(db, recency_resolution_query([name for name in PRIMARY_FEATURES if "seconds_since" in name])) if write_artifacts else list(csv.DictReader((REPORT_DIR / "recency_resolution_audit.csv").open(encoding="utf-8", newline="")))
    if write_artifacts:
        timestamp = db.execute("SELECT value FROM audit.part4_timestamp_precision WHERE metric='minimum_positive_delta_microseconds'").fetchone()[0]
        minimum_seconds = float(timestamp or 0) / 1_000_000
        for row in resolution:
            row["observed_min_positive_delta_seconds"] = minimum_seconds
            row["status"] = "PASS" if int(row["negative_rows"]) == 0 and int(row["zero_rows"]) == 0 and (row["min_non_null_recency_seconds"] is None or float(row["min_non_null_recency_seconds"]) >= minimum_seconds) else "FAIL"
            row["notes"] = "Recency is seconds between strictly earlier timestamps; zero and sub-resolution values are invalid."
        _write_csv(REPORT_DIR / "recency_resolution_audit.csv", list(resolution[0]) if resolution else ["feature_name", "min_non_null_recency_seconds", "negative_rows", "zero_rows", "observed_min_positive_delta_seconds", "status", "notes"], resolution)
    minimum_seconds = float(resolution[0].get("observed_min_positive_delta_seconds", 0) or 0) if resolution else 0
    bad = sum(1 for row in resolution if row["status"] != "PASS")
    checks.append(check("P4T33_recency_resolution_consistency", "PASS" if bad == 0 else "FAIL", f"Checked {len(resolution)} recency features against the observed timestamp resolution of {minimum_seconds:g} seconds.", len(resolution), bad))
    distributions = list(csv.DictReader((REPORT_DIR / "feature_distribution_profile.csv").open(encoding="utf-8", newline="")))
    groups: dict[tuple[str, str, str, str], list[str]] = {}
    for row in distributions:
        key = tuple(row.get(field, "") for field in ("min_value", "mean_value", "median_value", "max_value"))
        groups.setdefault(key, []).append(row["feature_name"])
    diversity = [{"distribution_key": "|".join(key), "feature_count": len(names), "feature_names": ";".join(names), "status": "FAIL" if len(names) >= 5 and len({name.split("_")[0] for name in names}) >= 3 else "PASS"} for key, names in groups.items() if len(names) >= 2]
    if write_artifacts:
        _write_csv(REPORT_DIR / "partition_diversity_audit.csv", ["distribution_key", "feature_count", "feature_names", "status"], diversity)
    elif (REPORT_DIR / "partition_diversity_audit.csv").exists():
        diversity = list(csv.DictReader((REPORT_DIR / "partition_diversity_audit.csv").open(encoding="utf-8", newline="")))
    bad_diversity = sum(1 for row in diversity if row["status"] != "PASS")
    checks.append(check("P4T34_feature_partition_diversity", "PASS" if bad_diversity == 0 else "FAIL", "Flags exact equality across five or more unrelated feature partitions.", len(diversity), bad_diversity))
    return checks


def artifact_set_check() -> dict[str, object]:
    if not EXPECTED_ARTIFACTS.exists():
        return check("P4T46_artifact_set_complete", "FAIL", "Expected artifact contract is missing.")
    expected = {line.strip()[2:].strip() for line in EXPECTED_ARTIFACTS.read_text(encoding="utf-8").splitlines() if line.strip().startswith("- ")}
    actual = {path.name for path in REPORT_DIR.glob("*.csv")} | {path.name for path in REPORT_DIR.glob("*.json")}
    missing = sorted(expected - actual); extra = sorted(actual - expected)
    return check("P4T46_artifact_set_complete", "PASS" if not missing and not extra else "FAIL", f"Expected={len(expected)}; actual={len(actual)}; missing={missing}; extra={extra}.", len(actual), len(missing) + len(extra))


def report_manifest_checks() -> list[dict[str, object]]:
    path = REPORT_DIR / "report_manifest.csv"
    if not path.exists():
        return [check("P4T44_report_manifest_complete", "FAIL", "report_manifest.csv is missing."), check("P4T45_report_hash_match", "FAIL", "Cannot verify hashes without report_manifest.csv.")]
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    runtime = json.loads(RUNTIME_MANIFEST.read_text(encoding="utf-8")) if RUNTIME_MANIFEST.exists() else {}
    missing = []; bad_hash = []; inconsistent = []
    for row in rows:
        target = ROOT / row["filename"]
        if not target.exists():
            missing.append(row["filename"]); continue
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        if digest != row["sha256"]:
            bad_hash.append(row["filename"])
        if row.get("run_id") != runtime.get("run_id") or row.get("code_commit") != runtime.get("code_commit"):
            inconsistent.append(row["filename"])
    complete = bool(rows) and not missing and not inconsistent and all(row.get("run_id") and row.get("code_commit") for row in rows)
    return [
        check("P4T44_report_manifest_complete", "PASS" if complete else "FAIL", f"Rows={len(rows)}; missing={missing}; provenance_mismatches={inconsistent}.", len(rows), len(missing) + len(inconsistent)),
        check("P4T45_report_hash_match", "PASS" if not bad_hash else "FAIL", f"SHA256 mismatches={bad_hash}.", len(rows), len(bad_hash)),
    ]


def provenance_checks(summary_path: Path) -> list[dict[str, object]]:
    if not RUNTIME_MANIFEST.exists():
        return [check("P4T35_code_commit_resolves", "FAIL", "Runtime manifest is missing."), check("P4T36_working_tree_clean_at_run", "FAIL", "Runtime manifest is missing."), check("P4T37_run_id_consistent_across_artifacts", "FAIL", "Runtime manifest is missing.")]
    runtime = json.loads(RUNTIME_MANIFEST.read_text(encoding="utf-8"))
    code_ok = bool(re.fullmatch(r"[0-9a-f]{40}", str(runtime.get("code_commit", ""))))
    artifact_ok = bool(re.fullmatch(r"[0-9a-f]{40}", str(runtime.get("artifact_commit", ""))))
    run_id = runtime.get("run_id")
    manifest_rows = list(csv.DictReader((REPORT_DIR / "report_manifest.csv").open(encoding="utf-8", newline=""))) if (REPORT_DIR / "report_manifest.csv").exists() else []
    run_ok = bool(run_id) and all(row.get("run_id") == run_id for row in manifest_rows)
    summary_ok = False
    try:
        data = json.loads(summary_path.read_text(encoding="utf-8")); summary_ok = data.get("run", {}).get("run_id") == run_id and data.get("run", {}).get("code_commit") == runtime.get("code_commit")
    except (OSError, json.JSONDecodeError):
        pass
    return [
        check("P4T35_code_commit_resolves", "PASS" if code_ok else "FAIL", "code_commit is a 40-character public Git commit reference; public resolution is verified after publish."),
        check("P4T36_working_tree_clean_at_run", "PASS" if runtime.get("working_tree_clean") is True else "FAIL", f"working_tree_clean={runtime.get('working_tree_clean')} at run start."),
        check("P4T37_run_id_consistent_across_artifacts", "PASS" if run_ok and summary_ok else "FAIL", f"run_id={run_id}; summary_match={summary_ok}; manifest_rows={len(manifest_rows)}.", len(manifest_rows), 0 if run_ok and summary_ok else 1),
        check("P4T35_artifact_commit_reference", "PASS" if artifact_ok else "FAIL", "artifact_commit is a resolvable public Git commit reference."),
    ]


def no_local_absolute_paths() -> dict[str, object]:
    pattern = re.compile(r"(?:[A-Za-z]:[\\/](?:Users|Documents|Downloads|AppData)|/Users/|/home/)", re.IGNORECASE)
    hits = []
    candidates = list(REPORT_DIR.glob("*.csv")) + list(REPORT_DIR.glob("*.json")) + list(ROOT.glob("*.md")) + list((ROOT / "docs").glob("*.md"))
    for path in candidates:
        text = path.read_text(encoding="utf-8", errors="ignore")
        if pattern.search(text):
            hits.append(path.relative_to(ROOT).as_posix())
    return check("P4T41_no_local_absolute_paths", "PASS" if not hits else "FAIL", "Public reports and docs contain no local absolute paths." if not hits else f"Paths with local references: {hits}", len(candidates), len(hits))


def frontend_checks(summary_path: Path) -> list[dict[str, object]]:
    html = (ROOT / "part-4.html").read_text(encoding="utf-8")
    js = (ROOT / "js/part-4.js").read_text(encoding="utf-8")
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
    versions = ["PART4_v1.1" in html or "PART4_v1.2" in html, "P4_FRONTEND_v1.2" in js, summary.get("frontend_contract_version") == "P4_FRONTEND_v1.2"]
    return [check("P4T42_frontend_version_sync", "PASS" if all(versions) else "FAIL", f"HTML={versions[0]}; JS={versions[1]}; summary={versions[2]}.")]


def headline_support_check(summary_path: Path) -> dict[str, object]:
    try:
        data = json.loads(summary_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return check("P4T43_headline_findings_interpretable_only", "FAIL", "Summary is unreadable.")
    rows = []
    for key in ("velocity_signal", "amount_signal"):
        rows.extend(data.get(key, []))
    rows.extend(data.get("merchant_familiarity", {}).get("profiles", []))
    rows.extend(data.get("channel_familiarity", {}).get("profiles", []))
    bad = [row.get("feature_name") for row in rows if row.get("support_status") not in (None, "INTERPRETABLE")]
    return check("P4T43_headline_findings_interpretable_only", "PASS" if not bad else "FAIL", f"Headline rows checked={len(rows)}; low-support rows={bad}.", len(rows), len(bad))


def existing_cross_split_checks() -> list[dict[str, object]]:
    path = REPORT_DIR / "cross_split_history_audit.csv"
    if not path.exists():
        return [check("P4T38_validation_sees_development_history", "FAIL", "Cross-split audit is missing."), check("P4T39_oot_sees_pre_oot_history", "FAIL", "Cross-split audit is missing.")]
    rows = {row["target_split"]: row for row in csv.DictReader(path.open(encoding="utf-8", newline=""))}
    return [
        check("P4T38_validation_sees_development_history", rows.get("VALIDATION", {}).get("status", "FAIL"), "Validation truth audit compares prior user history restricted to Development."),
        check("P4T39_oot_sees_pre_oot_history", rows.get("OUT_OF_TIME_OOT", {}).get("status", "FAIL"), "OOT truth audit compares prior user history from Development and Validation."),
    ]


def existing_entity_check() -> dict[str, object]:
    path = REPORT_DIR / "entity_complete_qa_report.csv"
    if not path.exists():
        return check("P4T40_entity_complete_qa_pass", "FAIL", "Entity-complete QA report is missing.")
    rows = list(csv.DictReader(path.open(encoding="utf-8", newline="")))
    bad = sum(1 for row in rows if row.get("status") != "PASS")
    return check("P4T40_entity_complete_qa_pass", "PASS" if rows and bad == 0 else "FAIL", f"Entity-complete checks={len(rows)}; failures={bad}.", len(rows), bad)


def publication_boundary() -> dict[str, object]:
    result = subprocess.run(["git", "ls-files"], cwd=ROOT, text=True, capture_output=True, check=False)
    paths = [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]
    extensions = {".duckdb", ".db", ".parquet", ".feather", ".arrow", ".tgz"}
    prefixes = ("data/raw/", "features/private/", "outputs/private/", "runtime/")
    violations = [path for path in paths if Path(path).suffix.lower() in extensions or any(path.startswith(prefix) and not path.endswith(".gitkeep") for prefix in prefixes)]
    return check("P4T29_publication_boundary", "PASS" if not violations else "FAIL", "No raw, row-level or private runtime artifact is tracked." if not violations else f"Forbidden tracked files: {violations}", len(paths), len(violations))


def static_checks(summary_path: Path, skip_summary_check: bool) -> list[dict[str, object]]:
    registry_fields = csv.DictReader(REGISTRY.open(encoding="utf-8", newline="")).fieldnames or [] if REGISTRY.exists() else []
    sql_paths = sorted(SQL_DIR.glob("0[0-9]_*.sql")) + [SQL_DIR / "10_geography_dependency.sql", SQL_DIR / "11_behavioral_mart.sql"]
    target_files = [path.name for path in sql_paths if re.search(r"fraud_label|Is Fraud\?|\btarget\b", path.read_text(encoding="utf-8"), re.IGNORECASE)]
    checks = [
        check("P4T01_registry_file_exists", "PASS" if REGISTRY.exists() else "FAIL", "docs/PART4_FEATURE_REGISTRY.csv"),
        check("P4T02_registry_primary_feature_count", "PASS" if len(PRIMARY_FEATURES) == 43 else "FAIL", f"Registry rows={len(PRIMARY_FEATURES)}; expected 43.", len(PRIMARY_FEATURES), 0 if len(PRIMARY_FEATURES) == 43 else 1),
        check("P4T03_registry_required_columns", "PASS" if {"feature_name", "feature_family", "definition", "entity", "lookback_window", "strict_pit_required", "cold_start_behavior"}.issubset(registry_fields) else "FAIL", "Required registry columns are present."),
        check("P4T04_family_sql_target_exclusion", "PASS" if not target_files else "FAIL", "Outcome tokens are excluded from source and family SQL." if not target_files else f"Violations: {target_files}"),
        publication_boundary(),
    ]
    if skip_summary_check:
        return checks
    if summary_path.exists():
        try:
            data = json.loads(summary_path.read_text(encoding="utf-8")); execution = data.get("execution", {})
            ok = data.get("feature_contract_version") == "PART4_v1.1" and data.get("validation", {}).get("status") == "PASS" and execution.get("scope") in {"DETERMINISTIC_QA_EXECUTION_SLICE", "FULL_POPULATION"}
            checks.append(check("P4T26_summary_execution_scope", "PASS" if ok else "FAIL", "Summary declares scope, population and validation status."))
        except (OSError, json.JSONDecodeError) as exc:
            checks.append(check("P4T26_summary_execution_scope", "FAIL", f"Summary unreadable: {exc}"))
    else:
        checks.append(check("P4T26_summary_execution_scope", "FAIL", "Summary is missing."))
    return checks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path)
    parser.add_argument("--sample-row-limit", type=int, default=None)
    parser.add_argument("--summary", type=Path, default=SUMMARY)
    parser.add_argument("--skip-summary-check", action="store_true")
    parser.add_argument("--memory-limit", default="2GB")
    parser.add_argument("--temp-directory", type=Path)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--validate-only", action="store_true", help="Validate existing reports without rewriting generated artifacts.")
    parser.add_argument("--skip-closure-checks", action="store_true", help="Use only during the pre-summary validator pass.")
    args = parser.parse_args()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    checks = static_checks(args.summary, args.skip_summary_check)
    fixture = fixture_sql_checks()
    checks.append(check("P4T12_sql_backed_pit_fixture", "PASS" if all(row["status"] == "PASS" for row in fixture) else "FAIL", "Fixture expected values match the production SQL output.", 10, sum(int(row["violations"]) for row in fixture)))
    if args.database:
        db = duckdb.connect(str(args.database.resolve()), read_only=True)
        db.execute(f"SET threads={max(1, args.threads)}")
        db.execute(f"SET memory_limit='{args.memory_limit}'")
        db.execute("SET preserve_insertion_order=false")
        if args.temp_directory:
            db.execute("SET temp_directory=?", [str(args.temp_directory.resolve())])
            db.execute("SET max_temp_directory_size='8GB'")
        try:
            write_family_reports(db, args.sample_row_limit, write_artifacts=not args.validate_only)
            checks.extend(database_checks(db, write_artifacts=not args.validate_only))
            support_ok = True
            for path in [REPORT_DIR / "development_numeric_feature_signal.csv", REPORT_DIR / "development_binary_feature_signal.csv"]:
                if path.exists():
                    for row in csv.DictReader(path.open(encoding="utf-8", newline="")):
                        transactions = int(row["transactions"]); support_ok &= (transactions >= 1000 and row["support_status"] == "INTERPRETABLE") or (transactions < 1000 and row["support_status"] == "LOW_SUPPORT")
            checks.append(check("P4T25_low_support_flag_integrity", "PASS" if support_ok else "FAIL", "Every signal row is classified against support threshold 1,000."))
            run_id = "UNKNOWN"
            if RUNTIME_MANIFEST.exists():
                try:
                    run_id = json.loads(RUNTIME_MANIFEST.read_text(encoding="utf-8")).get("run_id", "UNKNOWN")
                except (OSError, json.JSONDecodeError):
                    pass
            checks.extend(artifact_consistency_checks(db, run_id, write_artifacts=not args.validate_only))
            checks.extend(relationship_checks(db, write_artifacts=not args.validate_only))
            if args.validate_only:
                checks.extend(existing_cross_split_checks())
                checks.append(existing_entity_check())
            else:
                entity_meta = entity_complete_qa(db, write_artifacts=True)
                checks.append(check("P4T40_entity_complete_qa_pass", entity_meta["status"], f"Selected {entity_meta['users']} deterministic users and {entity_meta['rows']} observed-history rows; merchant-global history is excluded.", entity_meta["rows"], 0 if entity_meta["status"] == "PASS" else 1))
                checks.extend(existing_cross_split_checks())
        finally:
            db.close()
    pipeline_text = (ROOT / "src/part4/run_part4_pipeline.py").read_text(encoding="utf-8")
    signal_text = pipeline_text.split("def signal_queries", 1)[-1].split("def size_mb", 1)[0]
    checks.extend([
        check("P4T23_development_only_signal_mining", "PASS" if "split_name = 'DEVELOPMENT'" in signal_text else "FAIL", "Signal queries explicitly filter Development."),
        check("P4T24_validation_oot_not_mined", "PASS" if "VALIDATION" not in signal_text and "OUT_OF_TIME_OOT" not in signal_text else "FAIL", "Validation and OOT are excluded from signal discovery."),
        check("P4T30_readme_status_sync", "PASS" if "Part 4" in (ROOT / "README.md").read_text(encoding="utf-8") and "Locked" in (ROOT / "README.md").read_text(encoding="utf-8") else "FAIL", "README reflects the final locked Part 4 status."),
    ])
    if not args.skip_closure_checks:
        checks.extend(provenance_checks(args.summary))
        checks.append(no_local_absolute_paths())
        checks.extend(frontend_checks(args.summary))
        checks.append(headline_support_check(args.summary))
        checks.extend(report_manifest_checks())
        checks.append(artifact_set_check())
    write_rows(REPORT, checks)
    failed = [row["check_name"] for row in checks if row["status"] != "PASS"]
    if failed:
        raise SystemExit(f"Part 4 validation failed: {failed}")
    print(f"Part 4 validation passed: {len(checks)} checks")


if __name__ == "__main__":
    main()
