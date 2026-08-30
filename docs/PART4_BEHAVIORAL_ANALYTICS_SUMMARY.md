# Part 4 — Behavioral Fraud Analytics

Part 4 converts the audited IBM synthetic transaction base into point-in-time behavioral features. It asks how the current transaction differs from the user, card, merchant and relationship history available strictly before `T0`.

The implementation is contract-first. The public repository contains SQL, Python, registry, fixtures, documentation and aggregate JSON only. The 24.4M-row feature mart, raw CSV, Parquet and DuckDB files are temporary offline artifacts and are not published.

## Current implementation status

The locked contract is `PART4_v1.1`. The public evidence is `BEHAVIOR_READY / LOCKED`: the clean 100,000-row deterministic QA execution slice passed SQL-backed PIT fixtures, semantic invariants, live-mart artifact consistency, relationship and recency audits, true cross-split truth recomputation, report hashes, provenance checks and entity-complete QA. It is not a representative sample and no full-population behavioral signal claim is made.

Every run records a UTC run ID, separately resolved `code_commit` and `artifact_commit`, working-tree status, contract versions, execution scope and validation status in `reports/part4/runtime_manifest.json` and `assets/data/part4_summary.json`. `reports/part4/report_manifest.csv` records SHA256 and run provenance for the stable public reports.

## Primary feature families

There are 43 primary features across entity history, velocity, positive-amount baselines/deviation, merchant familiarity, MCC familiarity and channel familiarity. Geography is extended-only because missing state is a comparability issue rather than an automatic new-state signal.

## Governance boundary

The source label is not available with a label-availability timestamp. It is therefore excluded from behavior construction and appended only after feature construction for Development-only aggregate signal profiling. Part 4 does not claim incremental model value, AUC improvement, loss reduction, causality or production deployment.

## Validation and limitations

- PIT edge cases are executed by the same SQL feature family implementation used by the pipeline, then compared exactly with `tests/fixtures/part4_pit_expected.csv`.
- Semantic invariant output is published in `reports/part4/semantic_invariant_report.csv`; all current violations are zero.
- Family row reconciliation and registry-to-mart audits are published in `feature_family_reconciliation.csv` and `feature_registry_audit.csv`.
- Signal bins are frozen by `config/part4_signal_bins.yml`: counts, seconds, ratios and directional z-scores use different units. Support below 1,000 is marked `LOW_SUPPORT` and excluded from headline findings.
- The deterministic prefix slice is a QA execution slice. `sample_history_coverage.csv` records temporal non-closure and an actual 100-row entity-level external-history audit; it does not publish a fabricated affected-row count. The entity-complete cohort validates full observed user/card/relationship history for deterministic users, while merchant-global history remains outside that completeness claim. Full 24.4M feature mart retention and full-population signal profiling were not required or claimed because of local resource constraints.

## Publication boundary and final status

Only aggregate reports, metadata, SQL, Python, fixtures and the static website are public. Raw CSV, row-level behavioral features, DuckDB and Parquet remain outside GitHub. Current status: `BEHAVIOR_READY / LOCKED`; full-population behavioral signal is not claimed.
