# Part 9 Presentation Contract

Part 9 is the executive overview of the Fraud Risk Analytics case study. It is a presentation layer, not a replacement for Parts 1–8.

## Evidence contract

Every metric must be defined in `reports/part9/part9_metric_registry.csv` and include a value, source artifact, source part, claim class and status. Every chart must be defined in `reports/part9/part9_chart_registry.csv` and must render only when its status is `AVAILABLE`.

`INPUT_BLOCKED` and `NOT_AVAILABLE` charts render an intentional evidence-state panel with no fabricated dataset. `OBSERVED`, `DERIVED`, `SIMULATED`, `GOVERNANCE` and `DEFINITION` remain visually distinct.

## Public boundary

Public JSON and charts contain aggregate counts, rates, time-window aggregates, category aggregates, statuses, versions and hashes only. They do not contain source row identifiers, row-level timestamps, row-level scores, labels, actions, reason codes, customer/card/merchant identifiers or raw graph edges.

## Status contract

The controlled vocabulary is `LOCKED`, `READY`, `FRAMEWORK_READY`, `IN_PROGRESS`, `INPUT_BLOCKED`, `NOT_RUN` and `NOT_APPLICABLE`. Part 9 may be `FINAL_PORTFOLIO_READY` while conditional upstream execution remains blocked, provided the blocked states are visible.
