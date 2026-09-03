SELECT drift_window_id, channel, COUNT(*) AS rows, AVG(amount) AS mean_amount,
       AVG(CASE WHEN state_missing_flag THEN 1 ELSE 0 END) AS state_missing_rate
FROM monitoring_windows
GROUP BY 1, 2;

