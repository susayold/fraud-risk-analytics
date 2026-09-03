-- Outcome branch only. Never expose this row-level result publicly.
SELECT performance_window_id, COUNT(*) AS transactions,
       SUM(fraud_label) AS fraud_count,
       SUM(CASE WHEN fraud_label = 1 THEN positive_exposure ELSE 0 END) AS fraud_exposure
FROM matured_outcomes
GROUP BY 1;

