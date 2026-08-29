# Part 2 — Source Contract

The project uses the IBM TabFormer synthetic credit-card transaction archive. The exact source file is `card_transaction.v1.csv`; one row represents one transaction event and the package contains no standalone users, cards or merchants dimensions.

The contract is enforced by `src/run_part2_pipeline.py` before conversion. The expected 15 columns are recorded in `config/source_contract.json`. The source does not supply a business `transaction_id`; `source_row_id` is a derived analytical surrogate that follows source-file scan order.

Canonical mapping is implemented in `sql/01_standardize_raw.sql`. `Zip` is stored as a string code, `MCC` is categorical, `Merchant Name` is an identifier-like value, and `Is Fraud?` is target-only.
