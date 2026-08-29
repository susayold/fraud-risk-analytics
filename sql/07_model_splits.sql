/* Part 2 — Chronological splits. Input: analytics.transaction_base and audit.split_policy. Output: analytics.model_splits. Grain: one row per transaction. Claim: DERIVED. */
CREATE OR REPLACE TABLE analytics.model_splits AS
SELECT *, CASE WHEN transaction_date <= (SELECT development_end FROM audit.split_policy) THEN 'DEVELOPMENT' WHEN transaction_date <= (SELECT validation_end FROM audit.split_policy) THEN 'VALIDATION' ELSE 'OUT_OF_TIME_OOT' END AS split
FROM analytics.transaction_base_pit;
