/* Part 2 — Canonical mapping. Input: raw.card_transactions. Output: analytics.transaction_standardized. Grain: one row per transaction. Claim: DERIVED. */
CREATE OR REPLACE VIEW analytics.transaction_standardized AS
SELECT
  source_row_id,
  CAST("User" AS BIGINT) AS user_id,
  CAST("Card" AS INTEGER) AS card_index,
  CONCAT(CAST("User" AS VARCHAR), ':', CAST("Card" AS VARCHAR)) AS card_key,
  TRY_STRPTIME(CAST("Year" AS VARCHAR) || '-' || LPAD(CAST("Month" AS VARCHAR), 2, '0') || '-' || LPAD(CAST("Day" AS VARCHAR), 2, '0') || ' ' || TRIM(CAST("Time" AS VARCHAR)), '%Y-%m-%d %H:%M:%S') AS transaction_timestamp,
  TRY_CAST(REPLACE(REPLACE(TRIM("Amount"), '$', ''), ',', '') AS DOUBLE) AS amount,
  NULLIF(TRIM("Use Chip"), '') AS use_chip,
  NULLIF(TRIM(CAST("Merchant Name" AS VARCHAR)), '') AS merchant_id_raw,
  NULLIF(TRIM("Merchant City"), '') AS merchant_city,
  NULLIF(TRIM("Merchant State"), '') AS merchant_state,
  NULLIF(TRIM(CAST("Zip" AS VARCHAR)), '') AS merchant_zip,
  CAST("MCC" AS VARCHAR) AS merchant_category_code,
  NULLIF(TRIM("Errors?"), '') AS errors_raw,
  CASE WHEN LOWER(TRIM(CAST("Is Fraud?" AS VARCHAR))) IN ('yes', 'true') THEN 1 WHEN LOWER(TRIM(CAST("Is Fraud?" AS VARCHAR))) IN ('no', 'false') THEN 0 ELSE NULL END AS fraud_label
FROM raw.card_transactions;
