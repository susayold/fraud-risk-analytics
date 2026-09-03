SELECT drift_window_id, COUNT(*) AS rows, AVG(risk_score) AS mean_score,
       QUANTILE_CONT(risk_score, 0.5) AS p50,
       QUANTILE_CONT(risk_score, 0.95) AS p95
FROM monitoring_windows
GROUP BY 1;

