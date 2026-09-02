SELECT CASE
         WHEN split_name IN ('DEVELOPMENT','P7_POLICY_TUNE') THEN 'P7_POLICY_TUNE'
         WHEN split_name IN ('VALIDATION','P7_POLICY_CONFIRM') THEN 'P7_POLICY_CONFIRM'
         WHEN split_name IN ('OUT_OF_TIME_OOT','FINAL_OOT') THEN 'FINAL_OOT'
       END AS policy_scope,
       MIN(transaction_timestamp) AS start_at,
       MAX(transaction_timestamp) AS end_at,
       COUNT(*) AS rows
FROM decision_input
GROUP BY 1;
