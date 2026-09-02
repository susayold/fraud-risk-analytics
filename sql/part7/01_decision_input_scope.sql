-- Label firewall: labels are not selected into the decision mart.
CREATE OR REPLACE TABLE decision_input AS
SELECT source_row_id, transaction_timestamp, risk_score, amount, split_name,
       pair_new, cold_card, new_merchant, cross_community, channel
FROM source_input;
