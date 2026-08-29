-- Duplicate and orphan checks. Adapt names only after inventory; never assume cardinality.
SELECT transaction_id, COUNT(*) AS n
FROM raw.transactions GROUP BY transaction_id HAVING COUNT(*) > 1 ORDER BY n DESC;

SELECT COUNT(*) AS orphan_transactions
FROM raw.transactions t LEFT JOIN raw.cards c ON t.card_id = c.card_id
WHERE c.card_id IS NULL;

SELECT COUNT(*) AS orphan_cards
FROM raw.cards c LEFT JOIN raw.users u ON c.user_id = u.user_id
WHERE u.user_id IS NULL;
