"""Canonical aggregate-report queries shared by the Part 4 runner and validator."""
from __future__ import annotations

from collections.abc import Callable, Iterable


def _union(parts: Iterable[str]) -> str:
    # Parenthesize each branch so DuckDB cannot reuse the first branch's
    # bindings when several feature columns are projected through a view.
    return " UNION ALL ".join(f"({part})" for part in parts)


def null_profile_query(features: list[str], mart: str = "analytics.behavioral_features_v1") -> str:
    branches = _union(
        f"SELECT '{feature}' feature_name, row_count, null_rows, null_rows*1.0/NULLIF(row_count, 0) null_rate "
        f"FROM (SELECT COUNT(*) row_count, COUNT(*) FILTER (WHERE {feature} IS NULL) null_rows FROM mart_snapshot) aggregate_{feature}"
        for feature in features
    )
    return f"WITH mart_snapshot AS MATERIALIZED (SELECT * FROM {mart}) {branches}"


def distribution_profile_query(features: list[str], mart: str = "analytics.behavioral_features_v1") -> str:
    branches = _union(
        f"SELECT '{feature}' feature_name, min_value, mean_value, median_value, max_value "
        f"FROM (SELECT MIN({feature}) min_value, AVG({feature}) mean_value, MEDIAN({feature}) median_value, MAX({feature}) max_value FROM mart_snapshot) aggregate_{feature}"
        for feature in features
    )
    return f"WITH mart_snapshot AS MATERIALIZED (SELECT * FROM {mart}) {branches}"


def binary_signal_query(features: list[str], evaluation: str = "analytics.part4_evaluation_v1") -> str:
    branches = _union(
        f"SELECT '{feature}' feature_name, CAST(feature_value AS INTEGER) bin_order, "
        f"CAST(feature_value AS VARCHAR) bin, CAST(feature_value AS VARCHAR) feature_value, "
        f"COUNT(*) transactions, SUM(fraud_label) fraud_transactions, AVG(fraud_label) fraud_rate, "
        f"1000 support_threshold, CASE WHEN COUNT(*) >= 1000 THEN 'INTERPRETABLE' ELSE 'LOW_SUPPORT' END support_status "
        f"FROM (SELECT {feature} feature_value, fraud_label FROM evaluation_snapshot WHERE split_name = 'DEVELOPMENT') source_{feature} GROUP BY 1,2,3,4"
        for feature in features
    )
    return f"WITH evaluation_snapshot AS MATERIALIZED (SELECT * FROM {evaluation}) {branches}"


def numeric_signal_query(
    features: list[str],
    bin_case: Callable[[str], str],
    bin_label: Callable[[str], str],
    evaluation: str = "analytics.part4_evaluation_v1",
) -> str:
    parts = []
    for feature in features:
        case_expr = bin_case(feature).replace(feature, "feature_value")
        label_expr = bin_label(feature).replace(feature, "feature_value")
        parts.append(
            f"SELECT '{feature}' feature_name, {case_expr} bin_order, {label_expr} bin, "
            f"NULL::VARCHAR feature_value, COUNT(*) transactions, SUM(fraud_label) fraud_transactions, "
            f"AVG(fraud_label) fraud_rate, 1000 support_threshold, "
            f"CASE WHEN COUNT(*) >= 1000 THEN 'INTERPRETABLE' ELSE 'LOW_SUPPORT' END support_status "
            f"FROM (SELECT {feature} feature_value, fraud_label FROM evaluation_snapshot WHERE split_name = 'DEVELOPMENT') source_{feature} GROUP BY 1,2,3"
        )
    return f"WITH evaluation_snapshot AS MATERIALIZED (SELECT * FROM {evaluation}) {_union(parts)}"


def cold_start_query(mart: str = "analytics.part4_evaluation_v1") -> str:
    return (
        f"WITH mart_snapshot AS MATERIALIZED (SELECT * FROM {mart}) SELECT entity, cold_start, transactions, fraud_transactions, fraud_rate FROM (SELECT 'user' entity, user_cold_start::VARCHAR cold_start, COUNT(*) transactions, SUM(fraud_label) fraud_transactions, AVG(fraud_label) fraud_rate FROM mart_snapshot GROUP BY 1,2) user_profile "
        f"UNION ALL SELECT entity, cold_start, transactions, fraud_transactions, fraud_rate FROM (SELECT 'card' entity, card_cold_start::VARCHAR cold_start, COUNT(*) transactions, SUM(fraud_label) fraud_transactions, AVG(fraud_label) fraud_rate FROM mart_snapshot GROUP BY 1,2) card_profile "
        f"UNION ALL SELECT entity, cold_start, transactions, fraud_transactions, fraud_rate FROM (SELECT 'merchant' entity, merchant_cold_start::VARCHAR cold_start, COUNT(*) transactions, SUM(fraud_label) fraud_transactions, AVG(fraud_label) fraud_rate FROM mart_snapshot GROUP BY 1,2) merchant_profile"
    )


def feature_cardinality_query(source: str = "analytics.part4_behavior_source") -> str:
    return (
        f"WITH source_snapshot AS MATERIALIZED (SELECT * FROM {source}) "
        f"SELECT * FROM (SELECT 'user_id' field_name, COUNT(DISTINCT user_id) distinct_values, COUNT(*) FILTER (WHERE user_id IS NULL) null_rows FROM source_snapshot) user_card "
        f"UNION ALL SELECT * FROM (SELECT 'card_key', COUNT(DISTINCT card_key), COUNT(*) FILTER (WHERE card_key IS NULL) FROM source_snapshot) card_key_profile "
        f"UNION ALL SELECT * FROM (SELECT 'merchant_id_raw', COUNT(DISTINCT merchant_id_raw), COUNT(*) FILTER (WHERE merchant_id_raw IS NULL) FROM source_snapshot) merchant_profile "
        f"UNION ALL SELECT * FROM (SELECT 'merchant_category_code', COUNT(DISTINCT merchant_category_code), COUNT(*) FILTER (WHERE merchant_category_code IS NULL) FROM source_snapshot) mcc_profile "
        f"UNION ALL SELECT * FROM (SELECT 'use_chip', COUNT(DISTINCT use_chip), COUNT(*) FILTER (WHERE use_chip IS NULL) FROM source_snapshot) channel_profile"
    )


def feature_dependency_query(mart: str = "analytics.behavioral_features_v1") -> str:
    return (
        f"SELECT 'user_history_to_card_history' dependency, CORR(user_prior_txn_count, card_prior_txn_count) metric_value, "
        f"'Descriptive structural check; not model importance.' notes FROM {mart} "
        f"UNION ALL SELECT 'current_positive_to_user_mean_ratio', CORR(CASE WHEN current_positive_amount THEN 1 ELSE 0 END, current_positive_amount_vs_user_mean), "
        f"'NULL-aware exploratory dependency.' FROM {mart}"
    )


def channel_dependency_query(view: str = "analytics.part4_channel_state_dependency") -> str:
    return f"SELECT * FROM {view}"


def relationship_semantics_query(mart: str = "analytics.behavioral_features_v1") -> str:
    return f"""
WITH mart_snapshot AS MATERIALIZED (SELECT * FROM {mart})
SELECT * FROM (SELECT 'user_merchant_is_new_count' metric, COUNT(*) FILTER (WHERE user_merchant_is_new = 1)::BIGINT metric_value FROM mart_snapshot) user_merchant_new
UNION ALL SELECT * FROM (SELECT 'user_merchant_recency_null_count', COUNT(*) FILTER (WHERE user_merchant_seconds_since_prev_txn IS NULL)::BIGINT FROM mart_snapshot) user_merchant_recency
UNION ALL SELECT * FROM (SELECT 'card_merchant_is_new_count', COUNT(*) FILTER (WHERE card_merchant_is_new = 1)::BIGINT FROM mart_snapshot) card_merchant_new
UNION ALL SELECT * FROM (SELECT 'card_merchant_recency_null_count', COUNT(*) FILTER (WHERE card_merchant_seconds_since_prev_txn IS NULL)::BIGINT FROM mart_snapshot) card_merchant_recency
UNION ALL SELECT * FROM (SELECT 'user_mcc_is_new_count', COUNT(*) FILTER (WHERE user_mcc_is_new = 1)::BIGINT FROM mart_snapshot) user_mcc_new
UNION ALL SELECT * FROM (SELECT 'card_mcc_is_new_count', COUNT(*) FILTER (WHERE card_mcc_is_new = 1)::BIGINT FROM mart_snapshot) card_mcc_new
UNION ALL SELECT * FROM (SELECT 'user_channel_is_new_count', COUNT(*) FILTER (WHERE user_channel_is_new = 1)::BIGINT FROM mart_snapshot) user_channel_new
UNION ALL SELECT * FROM (SELECT 'card_channel_is_new_count', COUNT(*) FILTER (WHERE card_channel_is_new = 1)::BIGINT FROM mart_snapshot) card_channel_new
""".strip()


def recency_resolution_query(features: list[str], mart: str = "analytics.behavioral_features_v1") -> str:
    branches = _union(
        f"SELECT '{feature}' feature_name, min_non_null_recency_seconds, negative_rows, zero_rows "
        f"FROM (SELECT MIN({feature}) FILTER (WHERE {feature} IS NOT NULL) min_non_null_recency_seconds, COUNT(*) FILTER (WHERE {feature} IS NOT NULL AND {feature} < 0) negative_rows, COUNT(*) FILTER (WHERE {feature} IS NOT NULL AND {feature} = 0) zero_rows FROM mart_snapshot) aggregate_{feature}"
        for feature in features
    )
    return f"WITH mart_snapshot AS MATERIALIZED (SELECT * FROM {mart}) {branches}"
