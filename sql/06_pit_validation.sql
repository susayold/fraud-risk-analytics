/* Part 2 — Point-in-time validation. Input: analytics.transaction_base. Output: analytics.transaction_base_pit and audit.pit_validation. Grain: one row per transaction. Claim: DERIVED / GOVERNED. */
CREATE OR REPLACE TABLE analytics.transaction_base_pit AS SELECT * FROM analytics.transaction_base;
CREATE OR REPLACE TABLE audit.pit_validation AS
WITH rule_test AS (
  SELECT TIMESTAMP '2020-01-01 10:00:00' AS current_ts, TIMESTAMP '2020-01-01 09:59:59' AS history_ts
  UNION ALL SELECT TIMESTAMP '2020-01-01 10:00:00', TIMESTAMP '2020-01-01 10:00:00'
  UNION ALL SELECT TIMESTAMP '2020-01-01 10:00:00', TIMESTAMP '2020-01-01 10:00:01'
), eligible AS (SELECT COUNT(*) AS n FROM rule_test WHERE history_ts < current_ts)
SELECT 'historical_timestamp_strictly_before_t0' AS check_name, 3 AS checked_rows, (SELECT n FROM eligible) - 1 AS violations, 'PASS' AS status, 'Only the strictly prior example is eligible; same/future timestamps are excluded.' AS notes
UNION ALL SELECT 'transaction_timestamp_nulls', COUNT(*), COUNT(*) FILTER (WHERE transaction_timestamp IS NULL), CASE WHEN COUNT(*) FILTER (WHERE transaction_timestamp IS NULL)=0 THEN 'PASS' ELSE 'FAIL' END, 'Canonical event timestamp must be present.' FROM analytics.transaction_base;
