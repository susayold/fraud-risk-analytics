/* Public publication rule: this row-level mart is temporary and never exported to GitHub. */
CREATE OR REPLACE VIEW analytics.behavioral_features_v1 AS
SELECT b.source_row_id, b.transaction_timestamp, b.split_name,
       b.user_id, b.card_key, b.merchant_id_raw, b.merchant_category_code, b.use_chip, b.merchant_state,
       b.amount,
       u.user_prior_txn_count, u.user_cold_start, u.user_seconds_since_prev_txn, u.user_txn_count_1h, u.user_txn_count_24h, u.user_txn_count_7d,
       c.card_prior_txn_count, c.card_cold_start, c.card_seconds_since_prev_txn, c.card_txn_count_1h, c.card_txn_count_24h, c.card_txn_count_7d,
       m.merchant_prior_txn_count, m.merchant_cold_start, m.merchant_seconds_since_prev_txn, m.merchant_txn_count_1h, m.merchant_txn_count_24h,
       a.current_positive_amount, a.user_positive_amount_sum_24h, a.user_positive_amount_sum_7d, a.card_positive_amount_sum_24h, a.card_positive_amount_sum_7d,
       a.user_prior_positive_amount_mean, a.user_prior_positive_amount_std, a.card_prior_positive_amount_mean, a.card_prior_positive_amount_std,
       a.current_positive_amount_vs_user_mean, a.current_positive_amount_vs_card_mean, a.current_positive_amount_user_z, a.current_positive_amount_card_z,
       um.user_merchant_prior_txn_count, um.user_merchant_is_new, um.user_merchant_seconds_since_prev_txn,
       cm.card_merchant_prior_txn_count, cm.card_merchant_is_new, cm.card_merchant_seconds_since_prev_txn,
       umcc.user_mcc_prior_txn_count, umcc.user_mcc_is_new, cmcc.card_mcc_prior_txn_count, cmcc.card_mcc_is_new,
       ch.user_channel_prior_txn_count, ch.user_channel_is_new, ch.card_channel_prior_txn_count, ch.card_channel_is_new,
       CASE WHEN b.merchant_state IS NULL THEN 1 ELSE 0 END::INTEGER AS state_missing_flag,
       'PART4_v1.0' AS feature_contract_version,
       'history_timestamp < current_timestamp' AS pit_policy_version,
       CURRENT_TIMESTAMP AS feature_build_ts
FROM analytics.part4_behavior_source b
JOIN analytics.part4_user_features u USING (source_row_id)
JOIN analytics.part4_card_features c USING (source_row_id)
JOIN analytics.part4_merchant_features m USING (source_row_id)
JOIN analytics.part4_amount_features a USING (source_row_id)
JOIN analytics.part4_user_merchant_features um USING (source_row_id)
JOIN analytics.part4_card_merchant_features cm USING (source_row_id)
JOIN analytics.part4_user_mcc_features umcc USING (source_row_id)
JOIN analytics.part4_card_mcc_features cmcc USING (source_row_id)
JOIN analytics.part4_channel_features ch USING (source_row_id);

