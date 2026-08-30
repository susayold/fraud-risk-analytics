SELECT split_name, COUNT(*) AS rows, SUM(fraud_label) AS fraud_rows,
       COUNT(*) - SUM(fraud_label) AS legitimate_rows,
       MIN(transaction_timestamp) AS date_start,
       MAX(transaction_timestamp) AS date_end,
       AVG(fraud_label) AS natural_prevalence
FROM part5_source
WHERE split_name IN ('VALIDATION','OUT_OF_TIME_OOT')
GROUP BY 1
ORDER BY 1;
