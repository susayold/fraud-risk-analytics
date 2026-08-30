# Part 4 — frontend data contract (P4_FRONTEND_v1.1)

`assets/data/part4_summary.json` is aggregate-only. It may contain feature-family counts, PIT policy, fixture status, aggregate Development signal profiles and governance notes. It must not contain transaction rows, user/card/merchant identifiers, raw CSV content, Parquet, DuckDB or model artifacts.

Required fields are: `status`, `feature_contract_version`, `pit_rule`, `execution.scope`, `execution.rows`, `execution.source_population_rows`, `validation.status`, `feature_families`, `findings`, `claim_boundary` and `run`. The `run` object carries the run ID, commit and contract versions so a reader can trace the evidence.

The renderer is fail-closed. If `validation.status` is not `PASS`, it shows `VALIDATION REVIEW` and never shows a READY claim. If the summary cannot be fetched, it shows `Summary unavailable` and renders no fallback analytics. Low-support rows remain visible with muted styling and a “Low support — descriptive only” tooltip; they are never used in headline findings.

