/* Evaluation label join is allowed only here, after feature construction. No historical label is used. */
CREATE OR REPLACE VIEW analytics.part4_evaluation_v1 AS
SELECT f.*, b.fraud_label
FROM analytics.behavioral_features_v1 f
JOIN analytics.model_splits b USING (source_row_id);
