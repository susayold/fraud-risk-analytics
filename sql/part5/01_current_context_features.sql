/* Current-event fields only. MCC is categorical, not ordinal. */
CREATE OR REPLACE TEMP VIEW part5_current_context AS
SELECT source_row_id, transaction_timestamp, split_name, fraud_label,
       amount, use_chip, merchant_category_code,
       CASE WHEN merchant_state IS NULL THEN 1 ELSE 0 END::INTEGER AS state_missing_flag
FROM part5_source;
