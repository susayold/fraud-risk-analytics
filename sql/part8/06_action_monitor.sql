SELECT operational_window_id, action, COUNT(*) AS rows
FROM monitoring_windows
GROUP BY 1, 2;

