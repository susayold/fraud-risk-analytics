# Data

This project uses the IBM Synthetic Credit Card Transactions dataset. Raw and processed transaction files are intentionally not committed to GitHub because of size and because the public portfolio should publish aggregates, schemas and audit outputs rather than raw rows.

Expected local structure:

```text
data/raw/       # acquired source CSV/Parquet files
data/interim/   # temporary normalized extracts
data/processed/ # compressed Parquet outputs
```

To reproduce Part 2, place the source files in `data/raw/`, run `python src/ingest.py`, then run the audit SQL and storage/build scripts from the repository root. The pipeline derives metrics from the actual files; it does not hard-code transaction counts, dates or fraud rates. All public claims identify the data as synthetic.
