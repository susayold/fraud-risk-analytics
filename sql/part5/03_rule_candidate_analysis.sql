/* Rules are deliberately a later sprint. This query exposes Development-only aggregates for auditable threshold design. */
SELECT
  COUNT(*) FILTER (WHERE fraud_label = 1) AS development_fraud_rows,
  COUNT(*) FILTER (WHERE fraud_label = 0) AS development_legitimate_rows,
  AVG(fraud_label) AS development_fraud_rate
FROM part5_source
WHERE split_name = 'DEVELOPMENT';
