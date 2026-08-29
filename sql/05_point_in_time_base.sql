-- Every feature timestamp must be <= the current transaction timestamp (T0).
CREATE OR REPLACE TABLE analytics.transaction_base_pit AS
SELECT t.*
FROM analytics.transaction_base t;

-- Example history join: strict prior history, never the current/future row.
-- SELECT t.transaction_id, COUNT(h.transaction_id) AS prior_txn_count
-- FROM analytics.transaction_base t
-- LEFT JOIN analytics.transaction_base h
--   ON h.card_id = t.card_id
--  AND h.transaction_timestamp < t.transaction_timestamp
-- GROUP BY t.transaction_id;
