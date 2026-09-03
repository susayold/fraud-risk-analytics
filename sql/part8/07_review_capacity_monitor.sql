SELECT operational_window_id,
       SUM(CASE WHEN candidate_action = 'REVIEW' THEN 1 ELSE 0 END) AS review_candidates,
       SUM(CASE WHEN review_selected THEN 1 ELSE 0 END) AS review_selected,
       SUM(CASE WHEN review_overflow THEN 1 ELSE 0 END) AS review_overflow
FROM monitoring_windows
GROUP BY 1;

