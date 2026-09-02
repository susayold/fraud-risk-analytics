/* Merchant history and velocity. Merchant identifiers are source identifiers, not a validated master. */
CREATE OR REPLACE TABLE analytics.part4_merchant_features AS
SELECT source_row_id,
       COALESCE(COUNT(*) OVER w_all, 0)::BIGINT AS merchant_prior_txn_count,
       COALESCE(COUNT(*) OVER w_1h, 0)::BIGINT AS merchant_txn_count_1h,
       COALESCE(COUNT(*) OVER w_24h, 0)::BIGINT AS merchant_txn_count_24h,
       CASE WHEN COUNT(*) OVER w_all = 0 THEN 1 ELSE 0 END::INTEGER AS merchant_cold_start,
       date_diff('second', MAX(transaction_timestamp) OVER w_all, transaction_timestamp)::BIGINT AS merchant_seconds_since_prev_txn
FROM analytics.part4_behavior_source
WINDOW w_all AS (PARTITION BY merchant_id_raw ORDER BY transaction_timestamp RANGE BETWEEN UNBOUNDED PRECEDING AND INTERVAL '1 microsecond' PRECEDING),
       w_1h AS (PARTITION BY merchant_id_raw ORDER BY transaction_timestamp RANGE BETWEEN INTERVAL '1 hour' PRECEDING AND INTERVAL '1 microsecond' PRECEDING),
       w_24h AS (PARTITION BY merchant_id_raw ORDER BY transaction_timestamp RANGE BETWEEN INTERVAL '24 hours' PRECEDING AND INTERVAL '1 microsecond' PRECEDING);

