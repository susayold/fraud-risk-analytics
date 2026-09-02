SELECT CAST(transaction_timestamp AS DATE) AS date, action,
       COUNT(*) AS rows, SUM(fraud_label) AS fraud_rows,
       SUM(positive_exposure * fraud_label) AS fraud_exposure
FROM policy_actions_with_evaluation_label
GROUP BY 1, 2
ORDER BY 1, 2;
