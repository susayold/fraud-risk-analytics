/* Part 4 — behavior source. Outcome field is deliberately absent. Strict PIT is history_timestamp < current_timestamp. */
CREATE OR REPLACE VIEW analytics.part4_behavior_source AS
SELECT source_row_id, transaction_timestamp, split AS split_name, user_id, card_key, merchant_id_raw,
       merchant_category_code, use_chip, merchant_state, amount
FROM analytics.part4_input;

CREATE OR REPLACE TABLE audit.part4_timestamp_precision AS
WITH ordered AS (
  SELECT transaction_timestamp, LAG(transaction_timestamp) OVER (ORDER BY transaction_timestamp, source_row_id) AS previous_timestamp
  FROM analytics.part4_behavior_source
), stats AS (
  SELECT COUNT(*) AS rows_checked,
         COUNT(*) FILTER (WHERE transaction_timestamp IS NULL) AS null_timestamp_rows,
         COUNT(*) FILTER (WHERE transaction_timestamp = previous_timestamp) AS same_timestamp_adjacent_rows,
         MIN(date_diff('microsecond', previous_timestamp, transaction_timestamp)) FILTER (WHERE previous_timestamp IS NOT NULL AND transaction_timestamp > previous_timestamp) AS minimum_positive_delta_microseconds
  FROM ordered
)
SELECT 'timestamp_nulls' AS metric, null_timestamp_rows::DOUBLE AS value, CASE WHEN null_timestamp_rows = 0 THEN 'PASS' ELSE 'FAIL' END AS status, 'Canonical event timestamp must be present.' AS notes FROM stats
UNION ALL SELECT 'rows_checked', rows_checked, 'PASS', 'Part 4 behavior source rows audited.' FROM stats
UNION ALL SELECT 'same_timestamp_adjacent_rows', same_timestamp_adjacent_rows, 'PASS', 'Same timestamp peers remain excluded by strict upper frame bound.' FROM stats
UNION ALL SELECT 'minimum_positive_delta_microseconds', COALESCE(minimum_positive_delta_microseconds, 0), 'PASS', 'Microsecond interval is used only as an exclusion guard; logical policy remains timestamp < T0.' FROM stats;

