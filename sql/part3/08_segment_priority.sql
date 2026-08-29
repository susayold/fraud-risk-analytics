/* Part 3 — segment priority and limited interactions. Scope: DEVELOPMENT_DISCOVERY. No rules or model features are created. */
CREATE OR REPLACE TABLE analytics.part3_segment_priority AS
WITH candidates AS (
  SELECT segment_type, segment_value, transactions, transaction_share, fraud_transactions, fraud_rate, fraud_lift, fraud_capture_share, fraud_amount_capture_share, support_status FROM analytics.part3_channel_risk
  UNION ALL SELECT segment_type, segment_value, transactions, transaction_share, fraud_transactions, fraud_rate, fraud_lift, fraud_capture_share, fraud_amount_capture_share, support_status FROM analytics.part3_amount_band_risk
  UNION ALL SELECT segment_type, segment_value, transactions, transaction_share, fraud_transactions, fraud_rate, fraud_lift, fraud_capture_share, fraud_amount_capture_share, support_status FROM analytics.part3_mcc_risk
  UNION ALL SELECT segment_type, segment_value, transactions, transaction_share, fraud_transactions, fraud_rate, fraud_lift, fraud_capture_share, fraud_amount_capture_share, support_status FROM analytics.part3_state_risk
)
SELECT 'DEVELOPMENT_DISCOVERY' AS analysis_scope, segment_type, segment_value, transactions, transaction_share, fraud_transactions, fraud_rate, fraud_lift, fraud_capture_share, fraud_amount_capture_share, support_status,
  CASE WHEN support_status='LOW_SUPPORT' THEN 'LOW_PRIORITY' WHEN fraud_lift>=2 AND (fraud_capture_share>=.05 OR fraud_amount_capture_share>=.05) THEN 'PRIORITY_1' WHEN fraud_lift>=1.25 OR fraud_capture_share>=.03 OR fraud_amount_capture_share>=.03 THEN 'PRIORITY_2' ELSE 'MONITOR' END AS priority_class
FROM candidates
ORDER BY CASE WHEN support_status='LOW_SUPPORT' THEN 4 WHEN fraud_lift>=2 AND (fraud_capture_share>=.05 OR fraud_amount_capture_share>=.05) THEN 1 WHEN fraud_lift>=1.25 OR fraud_capture_share>=.03 OR fraud_amount_capture_share>=.03 THEN 2 ELSE 3 END, fraud_capture_share DESC, fraud_lift DESC, segment_type, segment_value;

CREATE OR REPLACE TABLE analytics.part3_interaction_risk AS
WITH baseline AS (SELECT SUM(fraud_label) AS fraud_txns, COUNT(*) AS txns FROM analytics.part3_development), cells AS (
  SELECT COALESCE(NULLIF(TRIM(use_chip), ''), '<UNKNOWN>') AS channel, CASE WHEN amount<0 THEN 'NEGATIVE / REFUND-LIKE' WHEN amount=0 THEN 'ZERO' WHEN amount<=25 THEN '>0–25' WHEN amount<=50 THEN '25–50' WHEN amount<=100 THEN '50–100' WHEN amount<=250 THEN '100–250' WHEN amount<=500 THEN '250–500' ELSE '500+' END AS amount_band, COUNT(*) AS transactions, SUM(fraud_label) AS fraud_transactions FROM analytics.part3_development GROUP BY 1,2)
SELECT 'DEVELOPMENT_DISCOVERY' AS analysis_scope, 'channel_x_amount_band' AS interaction_type, channel || ' × ' || amount_band AS segment_value, transactions, transactions*1.0/baseline.txns AS transaction_share, fraud_transactions, fraud_transactions*1.0/NULLIF(transactions,0) AS fraud_rate, (fraud_transactions*1.0/NULLIF(transactions,0))/NULLIF(baseline.fraud_txns*1.0/baseline.txns,0) AS fraud_lift, fraud_transactions*1.0/NULLIF(baseline.fraud_txns,0) AS fraud_capture_share, CASE WHEN transactions>=1000 THEN 'SUFFICIENT' ELSE 'LOW_SUPPORT' END AS support_status FROM cells CROSS JOIN baseline;
