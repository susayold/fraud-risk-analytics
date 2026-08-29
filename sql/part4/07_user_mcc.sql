/* User–MCC familiarity. */
CREATE OR REPLACE TABLE analytics.part4_user_mcc_features AS
SELECT source_row_id,
       COALESCE(COUNT(*) OVER w, 0)::BIGINT AS user_mcc_prior_txn_count,
       CASE WHEN COUNT(*) OVER w = 0 THEN 1 ELSE 0 END::INTEGER AS user_mcc_is_new
FROM analytics.part4_behavior_source
WINDOW w AS (PARTITION BY user_id, merchant_category_code ORDER BY transaction_timestamp RANGE BETWEEN UNBOUNDED PRECEDING AND INTERVAL '1 microsecond' PRECEDING);
