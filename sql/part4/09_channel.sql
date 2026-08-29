/* User/card channel familiarity. NULL channel is kept as an unseen-safe category. */
CREATE OR REPLACE TABLE analytics.part4_channel_features AS
SELECT source_row_id,
       COALESCE(COUNT(*) OVER u, 0)::BIGINT AS user_channel_prior_txn_count,
       CASE WHEN COUNT(*) OVER u = 0 THEN 1 ELSE 0 END::INTEGER AS user_channel_is_new,
       COALESCE(COUNT(*) OVER c, 0)::BIGINT AS card_channel_prior_txn_count,
       CASE WHEN COUNT(*) OVER c = 0 THEN 1 ELSE 0 END::INTEGER AS card_channel_is_new
FROM analytics.part4_behavior_source
WINDOW u AS (PARTITION BY user_id, use_chip ORDER BY transaction_timestamp RANGE BETWEEN UNBOUNDED PRECEDING AND INTERVAL '1 microsecond' PRECEDING),
       c AS (PARTITION BY card_key, use_chip ORDER BY transaction_timestamp RANGE BETWEEN UNBOUNDED PRECEDING AND INTERVAL '1 microsecond' PRECEDING);

