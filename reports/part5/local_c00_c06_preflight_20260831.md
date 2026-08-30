# Part 5 Local C00–C06 preflight report

**Run date:** 2026-08-31  
**Bundle:** `PART5_LOCAL_C00_C06_FULL_BUNDLE.zip`  
**Execution root:** `D:\data\FraudRisk\Part5\C00_C06_bundle_20260831`

## Outcome

`BLOCKED_BEFORE_DATA_READ`.

The bundle environment check completed. Stage `C00_SOURCE_FOUNDATION.py` then stopped before extracting or reading any transaction data because the expected raw archive was not present:

```text
FileNotFoundError: Raw archive not found:
D:\data\FraudRisk\Part5\C00_C06_bundle_20260831\data\raw\ibm-tabformer-transactions-20260829.tgz
```

No C01–C06 stage was started. Consequently, there is no valid ML metric or model result to publish from this run.

## Resource guard

| Resource | Observed | Bundle guidance |
|---|---:|---:|
| Project-drive free space | 44.68 GB | Prefer approximately 80–100 GB before C00 |
| Available RAM | 3.00 GB | DuckDB cap is 10 GB |
| GPU | NVIDIA GeForce GTX 1660 Ti, 6 GB | GPU fallback is supported |

Even after the archive is supplied, this machine is currently below the recommended disk headroom and has very low available RAM. A full C00–C06 run is therefore not safe to start now; it may thrash, lag, or run out of disk during foundation/feature construction.

## Storage boundary

- The bundle was extracted under `D:\data\FraudRisk\Part5\C00_C06_bundle_20260831`.
- No raw CSV/TGZ, DuckDB, Parquet, model binary or prediction file was created by this run.
- No invalid ML result was uploaded.
- Only this small diagnostic report is public evidence.

## Required next step

Provide the expected TGZ archive in the bundle's `data\raw` folder or set `FRAUD_P5_ARCHIVE` to its path, then run in a compute environment with at least 80–100 GB free disk and sufficient RAM. Keep private checkpoints on D/Drive; publish only the aggregate `Cxx_RESULT.zip` evidence after each stage passes.
