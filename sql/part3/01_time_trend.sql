/* Part 3 — time trend. Scope: DEVELOPMENT_DISCOVERY. Detailed Validation/OOT mining is prohibited. */
CREATE OR REPLACE TABLE analytics.part3_monthly_fraud_trend AS
SELECT
  'DEVELOPMENT_DISCOVERY' AS analysis_scope,
  STRFTIME(transaction_timestamp, '%Y-%m') AS month,
  'DEVELOPMENT' AS split_name,
  COUNT(*)::BIGINT AS transactions,
  SUM(fraud_label)::BIGINT AS fraud_transactions,
  AVG(fraud_label) AS fraud_rate,
  SUM(amount) AS total_amount,
  SUM(amount) FILTER (WHERE fraud_label=1) AS fraud_amount,
  SUM(amount) FILTER (WHERE fraud_label=1) / NULLIF(SUM(amount), 0) AS fraud_amount_share,
  AVG(fraud_label) / NULLIF((SELECT AVG(fraud_label) FROM analytics.part3_development), 0) AS fraud_lift_vs_development_baseline
FROM analytics.part3_development
GROUP BY 2;

CREATE OR REPLACE TABLE analytics.part3_yearly_fraud_trend AS
SELECT
  'DEVELOPMENT_DISCOVERY' AS analysis_scope,
  CAST(transaction_year AS INTEGER) AS year,
  COUNT(*)::BIGINT AS transactions,
  SUM(fraud_label)::BIGINT AS fraud_transactions,
  AVG(fraud_label) AS fraud_rate,
  SUM(amount) AS total_amount,
  SUM(amount) FILTER (WHERE fraud_label=1) AS fraud_amount,
  SUM(amount) FILTER (WHERE fraud_label=1) / NULLIF(SUM(amount), 0) AS fraud_amount_share
FROM analytics.part3_development
GROUP BY 2;
