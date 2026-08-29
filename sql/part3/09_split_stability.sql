/* Part 3 — predefined split stability. Scope: SPLIT_STABILITY. No detailed Validation/OOT segment ranking. */
CREATE OR REPLACE TABLE analytics.part3_split_stability AS
SELECT 'SPLIT_STABILITY' AS analysis_scope, split AS split_name, COUNT(*)::BIGINT AS transactions, SUM(fraud_label)::BIGINT AS fraud_transactions, AVG(fraud_label) AS fraud_rate,
  SUM(amount) FILTER (WHERE fraud_label=1) / NULLIF(SUM(amount),0) AS fraud_amount_share,
  COUNT(*) FILTER (WHERE LOWER(TRIM(use_chip))='online transaction') * 1.0 / COUNT(*) AS online_share,
  COUNT(*) FILTER (WHERE LOWER(TRIM(use_chip))='chip transaction') * 1.0 / COUNT(*) AS chip_share,
  COUNT(*) FILTER (WHERE LOWER(TRIM(use_chip))='swipe transaction') * 1.0 / COUNT(*) AS swipe_share
FROM analytics.model_splits GROUP BY 2;
