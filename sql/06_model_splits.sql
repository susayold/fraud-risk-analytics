-- Boundaries are generated from observed date coverage, not hard-coded in advance.
-- The OOT period must be chronologically after development and validation.
CREATE OR REPLACE TABLE analytics.model_splits AS
SELECT *, CASE
  WHEN transaction_date < :validation_start THEN 'DEVELOPMENT'
  WHEN transaction_date < :oot_start THEN 'VALIDATION'
  ELSE 'OUT_OF_TIME_OOT'
END AS split
FROM analytics.transaction_base_pit;
