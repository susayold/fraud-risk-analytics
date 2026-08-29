/* Card–MCC familiarity. */
CREATE OR REPLACE TABLE analytics.part4_card_mcc_features AS
SELECT source_row_id,
       COALESCE(COUNT(*) OVER w, 0)::BIGINT AS card_mcc_prior_txn_count,
       CASE WHEN COUNT(*) OVER w = 0 THEN 1 ELSE 0 END::INTEGER AS card_mcc_is_new
FROM analytics.part4_behavior_source
WINDOW w AS (PARTITION BY card_key, merchant_category_code ORDER BY transaction_timestamp RANGE BETWEEN UNBOUNDED PRECEDING AND INTERVAL '1 microsecond' PRECEDING);
