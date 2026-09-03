SELECT DATE_TRUNC('day', transaction_timestamp) AS operational_window_id,
       DATE_TRUNC('week', transaction_timestamp) AS drift_window_id,
       DATE_TRUNC('month', transaction_timestamp) AS performance_window_id,
       COUNT(*) AS row_count
FROM private_monitoring_mart
GROUP BY 1, 2, 3;

