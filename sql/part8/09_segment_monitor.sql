SELECT drift_window_id, channel, COUNT(*) AS support,
       AVG(positive_exposure) AS mean_exposure, AVG(risk_score) AS mean_score
FROM monitoring_windows
GROUP BY 1, 2;

