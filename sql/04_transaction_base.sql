-- One row per card transaction. Add card/user context only after join explosion checks.
CREATE OR REPLACE TABLE analytics.transaction_base AS
SELECT t.transaction_id,
       CAST(t.transaction_timestamp AS TIMESTAMP) AS transaction_timestamp,
       CAST(t.transaction_timestamp AS DATE) AS transaction_date,
       EXTRACT(YEAR FROM t.transaction_timestamp) AS transaction_year,
       EXTRACT(MONTH FROM t.transaction_timestamp) AS transaction_month,
       t.user_id, t.card_id, t.merchant_id, t.amount, t.fraud_label
FROM raw.transactions t;

SELECT (SELECT COUNT(*) FROM raw.transactions) AS raw_rows,
       (SELECT COUNT(*) FROM analytics.transaction_base) AS analytical_rows;
