-- Run after raw table names and audited columns are known.
-- Keep abnormal values for classification; do not silently delete them.
SELECT COUNT(*) AS row_count,
       COUNT(*) FILTER (WHERE transaction_timestamp IS NULL) AS timestamp_nulls,
       COUNT(*) FILTER (WHERE amount IS NULL) AS amount_nulls,
       MIN(transaction_timestamp) AS min_ts,
       MAX(transaction_timestamp) AS max_ts
FROM raw.transactions;

SELECT CAST(transaction_timestamp AS DATE) AS transaction_date,
       COUNT(*) AS transactions,
       SUM(CASE WHEN fraud_label = 1 THEN 1 ELSE 0 END) AS fraud_transactions,
       AVG(CASE WHEN fraud_label = 1 THEN 1.0 ELSE 0.0 END) AS fraud_rate
FROM raw.transactions
GROUP BY 1 ORDER BY 1;
