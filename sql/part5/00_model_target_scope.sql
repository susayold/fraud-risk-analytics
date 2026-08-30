/* Part 5 target population. Labels select training rows only; they never enter model features. */
CREATE OR REPLACE TEMP VIEW part5_source AS
SELECT * FROM analytics.part4_evaluation_v1;

CREATE OR REPLACE TEMP VIEW part5_development_quarter_counts AS
SELECT date_trunc('quarter', transaction_timestamp) AS quarter_start,
       COUNT(*) FILTER (WHERE fraud_label = 1) AS fraud_rows,
       COUNT(*) FILTER (WHERE fraud_label = 0) AS legitimate_rows
FROM part5_source
WHERE split_name = 'DEVELOPMENT'
GROUP BY 1;

CREATE OR REPLACE TEMP VIEW part5_target_scope AS
WITH ranked_legitimate AS (
  SELECT s.*,
         date_trunc('quarter', s.transaction_timestamp) AS quarter_start,
         ROW_NUMBER() OVER (
           PARTITION BY date_trunc('quarter', s.transaction_timestamp)
           ORDER BY md5(CAST(s.source_row_id AS VARCHAR) || ':20260830')
         ) AS quarter_hash_rank
  FROM part5_source s
  WHERE s.split_name = 'DEVELOPMENT' AND s.fraud_label = 0
), development_training AS (
  SELECT s.source_row_id, 'DEVELOPMENT_TRAIN' AS modeling_scope
  FROM part5_source s
  WHERE s.split_name = 'DEVELOPMENT' AND s.fraud_label = 1
  UNION ALL
  SELECT r.source_row_id, 'DEVELOPMENT_TRAIN' AS modeling_scope
  FROM ranked_legitimate r
  JOIN part5_development_quarter_counts q USING (quarter_start)
  WHERE r.quarter_hash_rank <= 20 * GREATEST(q.fraud_rows, 1)
), evaluation_windows AS (
  SELECT source_row_id, 'VALIDATION_CALIBRATION' AS modeling_scope
  FROM part5_source
  WHERE split_name = 'VALIDATION'
    AND transaction_timestamp >= (
      SELECT MAX(transaction_timestamp) - INTERVAL '365 days'
      FROM part5_source WHERE split_name = 'VALIDATION'
    )
    AND transaction_timestamp < (
      SELECT MIN(transaction_timestamp) + INTERVAL '182 days'
      FROM part5_source WHERE split_name = 'VALIDATION'
    )
  UNION ALL
  SELECT source_row_id, 'VALIDATION_SELECTION' AS modeling_scope
  FROM part5_source
  WHERE split_name = 'VALIDATION'
    AND transaction_timestamp >= (
      SELECT MAX(transaction_timestamp) - INTERVAL '365 days'
      FROM part5_source WHERE split_name = 'VALIDATION'
    )
    AND transaction_timestamp >= (
      SELECT MIN(transaction_timestamp) + INTERVAL '182 days'
      FROM part5_source WHERE split_name = 'VALIDATION'
    )
  UNION ALL
  SELECT source_row_id, 'OOT_EVALUATION_WINDOW' AS modeling_scope
  FROM part5_source
  WHERE split_name = 'OUT_OF_TIME_OOT'
    AND transaction_timestamp >= (
      SELECT MAX(transaction_timestamp) - INTERVAL '365 days'
      FROM part5_source WHERE split_name = 'OUT_OF_TIME_OOT'
    )
)
SELECT * FROM development_training
UNION ALL
SELECT * FROM evaluation_windows;
