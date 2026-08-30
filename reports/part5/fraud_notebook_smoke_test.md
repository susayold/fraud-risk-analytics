# `fraud.ipynb` smoke-test report

**Run date:** 2026-08-30 13:53 UTC  
**Notebook:** `fraud.ipynb`  
**Scope:** cells 0–7 only: dependency setup, repository pin, resource check, Drive download and source fingerprint validation.

## Result

`SOURCE_VALIDATION_FAIL` — the notebook stopped before the Part 2 DuckDB rebuild, Part 4 PIT feature construction, Logistic Regression, calibration and model metrics.

| Check | Observed |
|---|---:|
| Download size | 278,576,638 bytes (~279 MB) |
| Download time | ~15.4 seconds |
| Smoke-test elapsed time | ~42.1 seconds |
| Expected locked source size | 2,354,626,737 bytes |
| Expected source rows | 24,386,900 |
| Expected source SHA-256 | `68c438319cf27614…` |
| Observed source SHA-256 | `e9f589a0958f40ff…` |
| Resulting error | `SOURCE SIZE MISMATCH` |

## Resource observation

At the start of the local smoke test, the notebook reported approximately **6.89 GB free disk** and **5.17 GB available RAM**. Its configuration allows up to **10 GB DuckDB memory** and warns when free disk is below 12 GB. Therefore a full local run is not considered safe: it may lag or run out of disk during the foundation/feature stages.

## Storage and publication boundary

- The downloaded test file was placed in a temporary directory and deleted after the run.
- No raw CSV, DuckDB, Parquet, model binary, prediction file or row-level output was uploaded.
- This report is aggregate diagnostic evidence only.
- A valid Part 5 model result cannot be published until the Drive source matches the locked size and SHA-256 contract.

## Next action

Restore or provide the correct locked IBM source, then execute the notebook in a compute environment with at least 12 GB free disk (preferably more). Publish only aggregate reports after the notebook completes all validation gates.
