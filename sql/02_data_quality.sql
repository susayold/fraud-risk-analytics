/* Part 2 — Data quality. Input: analytics.transaction_standardized. Output: audit.data_quality. Grain: one row per check. Claim: OBSERVED. */
CREATE OR REPLACE TABLE audit.data_quality AS
SELECT 'row_count' AS check_name, COUNT(*)::DOUBLE AS metric_value, 'PASS' AS status FROM analytics.transaction_standardized
UNION ALL SELECT 'source_row_id_nulls', COUNT(*) FILTER (WHERE source_row_id IS NULL)::DOUBLE, CASE WHEN COUNT(*) FILTER (WHERE source_row_id IS NULL)=0 THEN 'PASS' ELSE 'FAIL' END FROM analytics.transaction_standardized
UNION ALL SELECT 'source_row_id_duplicates', (COUNT(*) - COUNT(DISTINCT source_row_id))::DOUBLE, CASE WHEN COUNT(*)=COUNT(DISTINCT source_row_id) THEN 'PASS' ELSE 'FAIL' END FROM analytics.transaction_standardized
UNION ALL SELECT 'timestamp_nulls', COUNT(*) FILTER (WHERE transaction_timestamp IS NULL)::DOUBLE, CASE WHEN COUNT(*) FILTER (WHERE transaction_timestamp IS NULL)=0 THEN 'PASS' ELSE 'FAIL' END FROM analytics.transaction_standardized
UNION ALL SELECT 'amount_nulls', COUNT(*) FILTER (WHERE amount IS NULL)::DOUBLE, CASE WHEN COUNT(*) FILTER (WHERE amount IS NULL)=0 THEN 'PASS' ELSE 'FAIL' END FROM analytics.transaction_standardized
UNION ALL SELECT 'fraud_label_nulls', COUNT(*) FILTER (WHERE fraud_label IS NULL)::DOUBLE, CASE WHEN COUNT(*) FILTER (WHERE fraud_label IS NULL)=0 THEN 'PASS' ELSE 'FAIL' END FROM analytics.transaction_standardized;
