/*
Part 3 — Fraud Portfolio Analytics
Purpose: establish the authoritative Development discovery view and portfolio baselines.
Analytical scope: DEVELOPMENT_DISCOVERY plus FULL_HISTORY_DESCRIPTIVE baseline.
Input: analytics.model_splits
Target: fraud_label
Claim class: OBSERVED / DERIVED
OOT policy: no detailed OOT discovery.
*/
CREATE OR REPLACE VIEW analytics.part3_development AS
SELECT * FROM analytics.model_splits WHERE split = 'DEVELOPMENT';

CREATE OR REPLACE TABLE analytics.part3_portfolio_summary AS
SELECT
  'DEVELOPMENT_DISCOVERY' AS analysis_scope,
  COUNT(*)::BIGINT AS transactions,
  SUM(fraud_label)::BIGINT AS fraud_transactions,
  AVG(fraud_label) AS fraud_rate,
  SUM(amount) AS total_amount,
  SUM(amount) FILTER (WHERE fraud_label=1) AS fraud_amount,
  SUM(amount) FILTER (WHERE fraud_label=1) / NULLIF(SUM(amount), 0) AS fraud_amount_share,
  AVG(amount) AS avg_amount,
  AVG(amount) FILTER (WHERE fraud_label=1) AS avg_fraud_amount,
  MEDIAN(amount) AS median_amount,
  MEDIAN(amount) FILTER (WHERE fraud_label=1) AS median_fraud_amount
FROM analytics.part3_development
UNION ALL
SELECT
  'FULL_HISTORY_DESCRIPTIVE', COUNT(*)::BIGINT, SUM(fraud_label)::BIGINT, AVG(fraud_label), SUM(amount),
  SUM(amount) FILTER (WHERE fraud_label=1), SUM(amount) FILTER (WHERE fraud_label=1) / NULLIF(SUM(amount), 0),
  AVG(amount), AVG(amount) FILTER (WHERE fraud_label=1), MEDIAN(amount), MEDIAN(amount) FILTER (WHERE fraud_label=1)
FROM analytics.model_splits;
