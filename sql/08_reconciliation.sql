/* Part 2 — Reconciliation. Input: audit.pipeline_counts and analytics.model_splits. Output: audit.reconciliation. Grain: one row per pipeline layer. Claim: OBSERVED / DERIVED. */
CREATE OR REPLACE TABLE audit.reconciliation AS
SELECT layer, row_count, distinct_source_row_id, min_source_row_id, max_source_row_id, fraud_rows FROM audit.pipeline_counts
UNION ALL SELECT 'STANDARDIZED', COUNT(*), COUNT(DISTINCT source_row_id), MIN(source_row_id), MAX(source_row_id), COUNT(*) FILTER (WHERE fraud_label=1) FROM analytics.transaction_standardized
UNION ALL SELECT 'TRANSACTION_BASE', COUNT(*), COUNT(DISTINCT source_row_id), MIN(source_row_id), MAX(source_row_id), COUNT(*) FILTER (WHERE fraud_label=1) FROM analytics.transaction_base
UNION ALL SELECT 'MODEL_SPLITS', COUNT(*), COUNT(DISTINCT source_row_id), MIN(source_row_id), MAX(source_row_id), COUNT(*) FILTER (WHERE fraud_label=1) FROM analytics.model_splits;
