-- Part 7 input discovery. Run against a private mounted source; never publish raw rows.
SELECT source_row_id, transaction_timestamp, risk_score, amount, split_name
FROM part5_frozen_score_input;
