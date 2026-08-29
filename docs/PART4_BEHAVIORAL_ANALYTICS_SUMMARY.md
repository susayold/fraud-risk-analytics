# Part 4 — Behavioral Fraud Analytics

Part 4 converts the audited IBM synthetic transaction base into point-in-time behavioral features. It asks how the current transaction differs from the user, card, merchant and relationship history available strictly before `T0`.

The implementation is contract-first. The public repository contains SQL, Python, registry, fixtures, documentation and aggregate JSON only. The 24.4M-row feature mart, raw CSV, Parquet and DuckDB files are temporary offline artifacts and are not published.

## Current implementation status

The feature contract and deterministic PIT fixture are validated. Full-population feature signal profiles are produced only when the offline runner completes against the Drive-staged raw source; the website deliberately does not substitute proxy or invented feature-performance numbers.

## Primary feature families

There are 43 primary features across entity history, velocity, positive-amount baselines/deviation, merchant familiarity, MCC familiarity and channel familiarity. Geography is extended-only because missing state is a comparability issue rather than an automatic new-state signal.

## Governance boundary

The source label is not available with a label-availability timestamp. It is therefore excluded from behavior construction and appended only after feature construction for Development-only aggregate signal profiling. Part 4 does not claim incremental model value, AUC improvement, loss reduction, causality or production deployment.
