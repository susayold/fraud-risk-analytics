-- Public SQL contract only. Execute against the private monitoring mart.
SELECT source_row_id, transaction_timestamp, amount, risk_score, split_name
FROM private_monitoring_mart;

