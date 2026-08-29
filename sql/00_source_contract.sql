/* Part 2 — Source contract. Input: raw.card_transactions. Output: contract evidence. Grain: one row per source transaction. Claim: OBSERVED. */
DESCRIBE raw.card_transactions;
SELECT COUNT(*) AS raw_rows, COUNT(DISTINCT source_row_id) AS distinct_source_row_ids, MIN(source_row_id) AS min_source_row_id, MAX(source_row_id) AS max_source_row_id FROM raw.card_transactions;
