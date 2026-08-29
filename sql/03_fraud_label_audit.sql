SELECT fraud_label, COUNT(*) AS rows
FROM raw.transactions GROUP BY fraud_label ORDER BY fraud_label;

SELECT COUNT(*) AS total_transactions,
       COUNT(*) FILTER (WHERE fraud_label = 1) AS fraud_transactions,
       COUNT(*) FILTER (WHERE fraud_label = 0) AS legitimate_transactions,
       COUNT(*) FILTER (WHERE fraud_label IS NULL) AS null_labels,
       SUM(CASE WHEN fraud_label = 1 THEN amount ELSE 0 END) AS fraud_amount,
       SUM(amount) AS total_amount
FROM raw.transactions;
