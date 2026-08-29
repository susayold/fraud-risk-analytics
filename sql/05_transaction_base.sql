/* Part 2 — Transaction base. Input: analytics.transaction_standardized. Output: analytics.transaction_base. Grain: one row per transaction. Claim: DERIVED. */
CREATE OR REPLACE TABLE analytics.transaction_base AS
SELECT source_row_id, user_id, card_index, card_key, transaction_timestamp, CAST(transaction_timestamp AS DATE) AS transaction_date, EXTRACT(YEAR FROM transaction_timestamp) AS transaction_year, EXTRACT(MONTH FROM transaction_timestamp) AS transaction_month, amount, use_chip, merchant_id_raw, merchant_city, merchant_state, merchant_zip, merchant_category_code, errors_raw, fraud_label
FROM analytics.transaction_standardized;
