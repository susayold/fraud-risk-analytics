/* Part 3 — MCC risk. Scope: DEVELOPMENT_DISCOVERY. MCC code is categorical; minimum support = 1,000 transactions. */
CREATE OR REPLACE TABLE analytics.part3_mcc_risk AS
WITH baseline AS (SELECT COUNT(*) AS txns, SUM(fraud_label) AS fraud_txns, SUM(amount) FILTER (WHERE fraud_label=1) AS fraud_amount FROM analytics.part3_development),
segments AS (
  SELECT COALESCE(NULLIF(TRIM(merchant_category_code), ''), '<UNKNOWN>') AS segment_value, COUNT(*) AS transactions,
    SUM(fraud_label) AS fraud_transactions, SUM(amount) AS total_amount, SUM(amount) FILTER (WHERE fraud_label=1) AS fraud_amount
  FROM analytics.part3_development GROUP BY 1
)
SELECT 'DEVELOPMENT_DISCOVERY' AS analysis_scope, 'mcc' AS segment_type, segment_value, transactions,
  transactions * 1.0 / baseline.txns AS transaction_share, fraud_transactions, fraud_transactions * 1.0 / NULLIF(transactions,0) AS fraud_rate,
  (fraud_transactions * 1.0 / NULLIF(transactions,0)) / NULLIF(baseline.fraud_txns * 1.0 / baseline.txns,0) AS fraud_lift,
  fraud_transactions * 1.0 / NULLIF(baseline.fraud_txns,0) AS fraud_capture_share, segments.total_amount, segments.fraud_amount,
  segments.fraud_amount * 1.0 / NULLIF(segments.total_amount,0) AS fraud_amount_share, segments.fraud_amount * 1.0 / NULLIF(baseline.fraud_amount,0) AS fraud_amount_capture_share,
  CASE WHEN transactions >= 1000 THEN 'SUFFICIENT' ELSE 'LOW_SUPPORT' END AS support_status
FROM segments CROSS JOIN baseline;
