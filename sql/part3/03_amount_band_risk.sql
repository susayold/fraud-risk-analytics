/* Part 3 — amount bands. Scope: DEVELOPMENT_DISCOVERY. Signed negative and zero amounts remain separate. */
CREATE OR REPLACE TABLE analytics.part3_amount_band_risk AS
WITH labeled AS (
  SELECT *, CASE
    WHEN amount < 0 THEN 'NEGATIVE / REFUND-LIKE'
    WHEN amount = 0 THEN 'ZERO'
    WHEN amount > 0 AND amount <= 25 THEN '>0–25'
    WHEN amount > 25 AND amount <= 50 THEN '25–50'
    WHEN amount > 50 AND amount <= 100 THEN '50–100'
    WHEN amount > 100 AND amount <= 250 THEN '100–250'
    WHEN amount > 250 AND amount <= 500 THEN '250–500'
    ELSE '500+'
  END AS segment_value FROM analytics.part3_development
), baseline AS (SELECT COUNT(*) AS txns, SUM(fraud_label) AS fraud_txns, SUM(amount) FILTER (WHERE fraud_label=1) AS fraud_amount FROM labeled), segments AS (
  SELECT segment_value, COUNT(*) AS transactions, SUM(fraud_label) AS fraud_transactions, SUM(amount) AS total_amount, SUM(amount) FILTER (WHERE fraud_label=1) AS fraud_amount
  FROM labeled GROUP BY 1
)
SELECT 'DEVELOPMENT_DISCOVERY' AS analysis_scope, 'amount_band' AS segment_type, segment_value, transactions,
  transactions * 1.0 / baseline.txns AS transaction_share, fraud_transactions, fraud_transactions * 1.0 / NULLIF(transactions,0) AS fraud_rate,
  (fraud_transactions * 1.0 / NULLIF(transactions,0)) / NULLIF(baseline.fraud_txns * 1.0 / baseline.txns,0) AS fraud_lift,
  fraud_transactions * 1.0 / NULLIF(baseline.fraud_txns,0) AS fraud_capture_share, segments.total_amount, segments.fraud_amount,
  segments.fraud_amount * 1.0 / NULLIF(segments.total_amount,0) AS fraud_amount_share, segments.fraud_amount * 1.0 / NULLIF(baseline.fraud_amount,0) AS fraud_amount_capture_share,
  CASE WHEN transactions >= 1000 THEN 'SUFFICIENT' ELSE 'LOW_SUPPORT' END AS support_status
FROM segments CROSS JOIN baseline;

CREATE OR REPLACE TABLE analytics.part3_amount_distribution AS
SELECT 'DEVELOPMENT_DISCOVERY' AS analysis_scope, 'LEGITIMATE' AS label_group,
  MEDIAN(amount) AS median_amount, QUANTILE_CONT(amount, 0.75) AS p75_amount, QUANTILE_CONT(amount, 0.90) AS p90_amount,
  QUANTILE_CONT(amount, 0.95) AS p95_amount, QUANTILE_CONT(amount, 0.99) AS p99_amount
FROM analytics.part3_development WHERE fraud_label=0
UNION ALL
SELECT 'DEVELOPMENT_DISCOVERY', 'FRAUD_LABELED', MEDIAN(amount), QUANTILE_CONT(amount, 0.75), QUANTILE_CONT(amount, 0.90), QUANTILE_CONT(amount, 0.95), QUANTILE_CONT(amount, 0.99)
FROM analytics.part3_development WHERE fraud_label=1;
