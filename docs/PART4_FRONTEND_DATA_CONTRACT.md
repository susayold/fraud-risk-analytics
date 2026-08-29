# Part 4 — frontend data contract

`assets/data/part4_summary.json` is aggregate-only. It may contain feature-family counts, PIT policy, fixture status, aggregate Development signal profiles and governance notes. It must not contain transaction rows, user/card/merchant identifiers, raw CSV content, Parquet, DuckDB or model artifacts.

Critical fields are explicit: `status`, `feature_contract_version`, `pit_rule`, `base`, `feature_families`, `cold_start`, `velocity_signal`, `amount_signal`, `merchant_familiarity`, `channel_familiarity`, `dependency`, `pit_lab`, `validation`, `findings` and `governance`. When a full signal profile has not been executed, the renderer shows the governed offline-build state rather than fallback numbers.
