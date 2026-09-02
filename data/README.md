# Data

This project uses the IBM Synthetic Credit Card Transactions dataset. Raw and processed transaction files are intentionally not committed to GitHub because of size and because the public portfolio should publish aggregates, schemas and audit outputs rather than raw rows.

Expected local structure:

```text
data/raw/       # acquired source CSV/Parquet files
data/interim/   # temporary normalized extracts
data/processed/ # compressed Parquet outputs
```

To reproduce Parts 2–6, place the source files in `data/raw/` and run the corresponding pipeline. The pipeline derives metrics from actual files; it does not hard-code transaction counts, dates or fraud rates. All public claims identify the data as synthetic.

## Part 7 data boundary

Raw transaction data, row-level scores, private decisions, models, and temporary arrays are intentionally excluded from Git. Use a private Drive/project location and pass its local mounted/downloaded path to the Part 7 pipeline at execution time. Public reports contain aggregates and hashes only.
