/* Part 2 — Entity key audit. Input: analytics.transaction_standardized. Output: audit.entity_key_audit. Grain: one row per observed key. Claim: OBSERVED_WITH_LIMITATION. */
CREATE OR REPLACE TABLE audit.entity_key_audit AS
SELECT 'User' AS key_name, COUNT(DISTINCT user_id)::BIGINT AS distinct_values, 'synthetic user identifier' AS interpretation FROM analytics.transaction_standardized
UNION ALL SELECT 'User + Card', COUNT(DISTINCT card_key)::BIGINT, 'composite card entity key; Card alone is not global' FROM analytics.transaction_standardized
UNION ALL SELECT 'Merchant Name', COUNT(DISTINCT merchant_id_raw)::BIGINT, 'distinct merchant identifier values, not a validated dimension' FROM analytics.transaction_standardized;
