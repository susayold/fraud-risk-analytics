/* Part 2 — Fraud label audit. Input: analytics.transaction_standardized. Output: audit.fraud_label_audit. Grain: one row per label. Claim: OBSERVED. */
CREATE OR REPLACE TABLE audit.fraud_label_audit AS
SELECT fraud_label, COUNT(*)::BIGINT AS rows, COUNT(*) * 1.0 / SUM(COUNT(*)) OVER () AS rate FROM analytics.transaction_standardized GROUP BY fraud_label ORDER BY fraud_label;
