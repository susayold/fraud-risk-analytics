# Part 2 — Data Audit Summary

## Observed source

The audited IBM source contains 24,386,900 rows and 15 columns. It has 2,000 distinct `User` values, 6,139 distinct `User + Card` composite keys and 100,343 distinct `Merchant Name` identifier values. Fraud labels are `Yes`/`No`; 29,757 rows are fraud-labeled (0.122%).

## Accepted limitations

- No source business transaction ID is supplied; `source_row_id` is an analytical surrogate.
- The package is denormalized. User, card and merchant views are derived from observed identifiers; standalone dimension-table join validation is not applicable.
- `Merchant State`, `Zip` and `Errors?` have structural missingness that is retained and documented rather than silently imputed.
- `Errors?` timing/semantics require conservative EDA treatment.

## Reproducibility

Run `python src/run_part2_pipeline.py --source-file <temporary-source-csv> --work-dir <temporary-work-dir>`. The raw archive and intermediate Parquet/DuckDB files stay outside Git; only compact reports and the evidence-backed website summary are committed.
