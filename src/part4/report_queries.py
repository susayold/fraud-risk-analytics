"""Canonical aggregate-report queries shared by the Part 4 runner and validator."""
from __future__ import annotations

from collections.abc import Callable, Iterable


def _union(parts: Iterable[str]) -> str:
    return " UNION ALL ".join(parts)


def null_profile_query(features: list[str], mart: str = "analytics.behavioral_features_v1") -> str:
    return _union(
        f"SELECT '{feature}' feature_name, COUNT(*) row_count, "
        f"COUNT(*) FILTER (WHERE {feature} IS NULL) null_rows, "
        f"COUNT(*) FILTER (WHERE {feature} IS NULL)*1.0/NULLIF(COUNT(*), 0) null_rate "
        f"FROM {mart}"
        for feature in features
    )


def distribution_profile_query(features: list[str], mart: str = "analytics.behavioral_features_v1") -> str:
    return _union(
        f"SELECT '{feature}' feature_name, MIN({feature}) min_value, AVG({feature}) mean_value, "
        f"MEDIAN({feature}) median_value, MAX({feature}) max_value FROM {mart}"
        for feature in features
    )


def binary_signal_query(features: list[str], evaluation: str = "analytics.part4_evaluation_v1") -> str:
    return _union(
        f"SELECT '{feature}' feature_name, CAST({feature} AS INTEGER) bin_order, "
        f"CAST({feature} AS VARCHAR) bin, CAST({feature} AS VARCHAR) feature_value, "
        f"COUNT(*) transactions, SUM(fraud_label) fraud_transactions, AVG(fraud_label) fraud_rate, "
        f"1000 support_threshold, CASE WHEN COUNT(*) >= 1000 THEN 'INTERPRETABLE' ELSE 'LOW_SUPPORT' END support_status "
        f"FROM {evaluation} WHERE split_name = 'DEVELOPMENT' GROUP BY 1,2,3,4"
        for feature in features
    )


def numeric_signal_query(
    features: list[str],
    bin_case: Callable[[str], str],
    bin_label: Callable[[str], str],
    evaluation: str = "analytics.part4_evaluation_v1",
) -> str:
    parts = []
    for feature in features:
        parts.append(
            f"SELECT '{feature}' feature_name, {bin_case(feature)} bin_order, {bin_label(feature)} bin, "
            f"NULL::VARCHAR feature_value, COUNT(*) transactions, SUM(fraud_label) fraud_transactions, "
            f"AVG(fraud_label) fraud_rate, 1000 support_threshold, "
            f"CASE WHEN COUNT(*) >= 1000 THEN 'INTERPRETABLE' ELSE 'LOW_SUPPORT' END support_status "
            f"FROM {evaluation} WHERE split_name = 'DEVELOPMENT' GROUP BY 1,2,3"
        )
    return _union(parts)


def cold_start_query(mart: str = "analytics.part4_evaluation_v1") -> str:
    return (
        f"SELECT 'user' entity, user_cold_start::VARCHAR cold_start, COUNT(*) transactions, "
        f"SUM(fraud_label) fraud_transactions, AVG(fraud_label) fraud_rate FROM {mart} GROUP BY 1,2 "
        f"UNION ALL SELECT 'card', card_cold_start::VARCHAR, COUNT(*), SUM(fraud_label), AVG(fraud_label) FROM {mart} GROUP BY 1,2 "
        f"UNION ALL SELECT 'merchant', merchant_cold_start::VARCHAR, COUNT(*), SUM(fraud_label), AVG(fraud_label) FROM {mart} GROUP BY 1,2"
    )


def feature_cardinality_query(source: str = "analytics.part4_behavior_source") -> str:
    return (
        f"SELECT 'user_id' field_name, COUNT(DISTINCT user_id) distinct_values, COUNT(*) FILTER (WHERE user_id IS NULL) null_rows FROM {source} "
        f"UNION ALL SELECT 'card_key', COUNT(DISTINCT card_key), COUNT(*) FILTER (WHERE card_key IS NULL) FROM {source} "
        f"UNION ALL SELECT 'merchant_id_raw', COUNT(DISTINCT merchant_id_raw), COUNT(*) FILTER (WHERE merchant_id_raw IS NULL) FROM {source} "
        f"UNION ALL SELECT 'merchant_category_code', COUNT(DISTINCT merchant_category_code), COUNT(*) FILTER (WHERE merchant_category_code IS NULL) FROM {source} "
        f"UNION ALL SELECT 'use_chip', COUNT(DISTINCT use_chip), COUNT(*) FILTER (WHERE use_chip IS NULL) FROM {source}"
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
SELECT 'user_merchant_is_new_count' metric, COUNT(*) FILTER (WHERE user_merchant_is_new = 1)::BIGINT metric_value FROM {mart}
UNION ALL SELECT 'user_merchant_recency_null_count', COUNT(*) FILTER (WHERE user_merchant_seconds_since_prev_txn IS NULL)::BIGINT FROM {mart}
UNION ALL SELECT 'card_merchant_is_new_count', COUNT(*) FILTER (WHERE card_merchant_is_new = 1)::BIGINT FROM {mart}
UNION ALL SELECT 'card_merchant_recency_null_count', COUNT(*) FILTER (WHERE card_merchant_seconds_since_prev_txn IS NULL)::BIGINT FROM {mart}
UNION ALL SELECT 'user_mcc_is_new_count', COUNT(*) FILTER (WHERE user_mcc_is_new = 1)::BIGINT FROM {mart}
UNION ALL SELECT 'card_mcc_is_new_count', COUNT(*) FILTER (WHERE card_mcc_is_new = 1)::BIGINT FROM {mart}
UNION ALL SELECT 'user_channel_is_new_count', COUNT(*) FILTER (WHERE user_channel_is_new = 1)::BIGINT FROM {mart}
UNION ALL SELECT 'card_channel_is_new_count', COUNT(*) FILTER (WHERE card_channel_is_new = 1)::BIGINT FROM {mart}
""".strip()


def recency_resolution_query(features: list[str], mart: str = "analytics.behavioral_features_v1") -> str:
    return _union(
        f"SELECT '{feature}' feature_name, MIN({feature}) FILTER (WHERE {feature} IS NOT NULL) min_non_null_recency_seconds, "
        f"COUNT(*) FILTER (WHERE {feature} IS NOT NULL AND {feature} < 0) negative_rows, "
        f"COUNT(*) FILTER (WHERE {feature} IS NOT NULL AND {feature} = 0) zero_rows FROM {mart}"
        for feature in features
    )
