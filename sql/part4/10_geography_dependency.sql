/* Geography is extended-only. Missing current state remains NULL, not new. */
CREATE OR REPLACE TABLE analytics.part4_channel_state_dependency AS
WITH cells AS (
  SELECT COALESCE(use_chip, '<NULL>') AS channel, CASE WHEN merchant_state IS NULL THEN '<MISSING>' ELSE '<PRESENT>' END AS state_status, COUNT(*) AS transactions
  FROM analytics.part4_behavior_source GROUP BY 1, 2
), totals AS (SELECT SUM(transactions) AS total_transactions FROM cells)
SELECT channel, state_status, transactions, transactions * 1.0 / NULLIF(total_transactions, 0) AS share
FROM cells CROSS JOIN totals ORDER BY transactions DESC, channel, state_status;

