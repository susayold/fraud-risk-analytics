SELECT COUNT(*) AS row_count,
       COUNT(DISTINCT source_row_id) AS unique_source_row_id,
       AVG(CASE WHEN source_row_id IS NULL THEN 1 ELSE 0 END) AS null_source_row_rate,
       AVG(CASE WHEN risk_score IS NULL OR risk_score NOT BETWEEN 0 AND 1 THEN 1 ELSE 0 END) AS score_contract_error_rate
FROM private_monitoring_mart;

