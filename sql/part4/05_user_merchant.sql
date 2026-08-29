/* User–merchant familiarity. */
CREATE OR REPLACE TABLE analytics.part4_user_merchant_features AS
SELECT source_row_id,
       COALESCE(COUNT(*) OVER w, 0)::BIGINT AS user_merchant_prior_txn_count,
       CASE WHEN COUNT(*) OVER w = 0 THEN 1 ELSE 0 END::INTEGER AS user_merchant_is_new,
       date_diff('second', MAX(transaction_timestamp) OVER w, transaction_timestamp)::BIGINT AS user_merchant_seconds_since_prev_txn
FROM analytics.part4_behavior_source
WINDOW w AS (PARTITION BY user_id, merchant_id_raw ORDER BY transaction_timestamp RANGE BETWEEN UNBOUNDED PRECEDING AND INTERVAL '1 microsecond' PRECEDING);

