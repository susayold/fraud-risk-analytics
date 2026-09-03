SELECT COUNT(*) AS mart_rows,
       SUM(window_count) AS assigned_window_rows
FROM window_reconciliation;

