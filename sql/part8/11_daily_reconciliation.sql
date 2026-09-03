SELECT operational_window_id, COUNT(*) AS assigned_rows,
       SUM(CASE WHEN operational_window_id IS NULL THEN 1 ELSE 0 END) AS unassigned_rows
FROM monitoring_windows
GROUP BY 1;

