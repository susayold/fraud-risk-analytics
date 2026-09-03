# Financial Fraud Risk Analytics & Transaction Decisioning

Interactive Fraud Risk portfolio built around the IBM Synthetic Credit Card Transactions dataset. The project is designed as a nine-part case study covering business framing, Data & SQL, fraud analytics, behavioral risk, rules & ML, graph analytics, decisioning, monitoring, and final portfolio delivery.

## Live Website

https://susayold.github.io/fraud-risk-analytics/

## Dataset

**IBM Synthetic Credit Card Transactions**

- Approximately 24.4 million transactions
- Customer/card/merchant transaction context
- Fraud labels and temporal transaction history
- Synthetic financial data only

> This project does not represent real production bank data.

## Project Status

| Part | Chapter | Status |
|---|---|---|
| 1 | Business Scope & Project Governance | ✅ Complete |
| 2 | Data & SQL Foundation | ✅ Locked |
| 3 | Fraud Portfolio Analytics | ✅ Locked |
| 4 | Behavioral Fraud Analytics | ✅ Locked — PIT + entity-complete QA validated; full-population signal not claimed |
| 5 | Fraud Rules & Machine Learning | 🟠 In progress — metrics remain source-driven |
| 6 | Network & Graph Fraud Analytics | ✅ Locked — aggregate Card–Merchant graph evidence and governance boundary |
| 7 | Fraud Risk Decision Engine | 🟠 Implemented — INPUT_BLOCKED pending frozen Part 5 row-level score |
| 8 | Monitoring, Drift & Governance | 🟢 Framework ready — INPUT_BLOCKED pending genuine upstream score/policy mart |
| 9 | Final Product & Portfolio | ✅ Final portfolio ready — conditional upstream stages remain source-driven |

## Business Problem

Design a transaction-level fraud risk framework that can rank suspicious card transactions and support three actions: **ALLOW / REVIEW / BLOCK**, while balancing fraud capture, fraud amount capture, false positives, customer friction, review capacity, and simulated business cost.

## Analytical Philosophy

The project separates:

- **OBSERVED** — directly calculated from IBM synthetic data
- **DERIVED** — analytical and model outputs
- **SIMULATED** — business-policy outcomes dependent on explicit assumptions

## Tech Stack

HTML / CSS / JavaScript · GSAP / ScrollTrigger / Lenis · Python / SQL / DuckDB · XGBoost / SHAP / NetworkX / Plotly

## Current Deliverable

Part 1 defines business context, fraud use case, KPI framework, validation questions, decision architecture, scope boundary, claim boundary, and governance principles. Part 2 adds the reproducible data inventory, streaming audit, executed Parquet/DuckDB and SQL-foundation pipeline. Part 3 adds Development-only portfolio discovery: time trends, channel/amount/MCC/geography risk, aggregate entity concentration, materiality-based segment priority and split-stability boundaries. Observed metrics are sourced from the IBM TabFormer transaction archive stored on Google Drive; the raw archive is not committed to GitHub.

## Part 4 — Behavioral Fraud Analytics

Part 4 implements a governed point-in-time behavioral feature layer with 43 primary behavioral features across entity history, velocity, amount deviation and relationship familiarity. Historical labels are excluded from feature construction. Public evidence is aggregate-only. The implementation is locked after SQL-backed PIT fixtures, semantic invariants, live-mart artifact reconciliation, true cross-split truth audits, provenance checks, report hashes and entity-complete QA. The full 24.4M-row feature mart is not retained or published because of local resource constraints, so full-population behavioral signal statistics are not claimed.

## Part 5 — Fraud Rules & Machine Learning

Part 5 is locked from the Drive-backed C00–C10 final checkpoint: point-in-time feature governance, natural-prevalence Validation selection, calibrated `FRAUD_CHAMPION_v1`, final OOT replay, Top-K diagnostics and temporal degradation. Only aggregate public evidence is published; final ALLOW / REVIEW / BLOCK policy belongs to Part 7.

## Part 7 — Fraud Risk Decision Engine

Block E is implemented as a separate, config-first policy layer. It consumes the exact frozen Part 5 champion score, keeps the Part 6 graph evidence as review-routing context, enforces `ALLOW / REVIEW / BLOCK`, deterministic review capacity, explicit positive-exposure economics, reason codes, sensitivity, shadow replay, freeze, final replay and 64 mandatory gates. The current public snapshot is intentionally `INPUT_BLOCKED` because the approved frozen Part 5 row-level score artifact is not in this repository; the 10/10 target `DECISION_POLICY_LOCKED` is not claimed, and no thresholds or policy metrics are invented.

## Part 8 — Monitoring, Drift & Governance

Block F is implemented as an offline, research-grounded monitoring framework. It uses two clocks: label-free operational early warning (`OPERATIONS_NOW`) and retrospective matured-outcome validation (`OUTCOMES_MATURED`). The implementation covers UTC windows, structural-missingness and category-novelty checks, frozen-bin drift metrics, score/policy/review/graph/segment monitoring, alert persistence, governance recommendations, 72 evidence gates, CI and an aggregate-only website chapter. The public snapshot is intentionally `MONITORING_FRAMEWORK_READY / INPUT_BLOCKED`; the 10/10 target `MONITORING_GOVERNANCE_LOCKED` is not claimed, and no production monitoring, raw row-level data or synthetic monitoring metrics are claimed.

The hardened CLI is explicit: `python -m src.part8.run_part8_pipeline audit-input --input <private.csv>`, `baseline --input <private.csv>`, `calibrate-thresholds --input <private.csv>`, `freeze`, `verify-freeze`, `replay --input <private.csv>`, and `matured-outcomes --input <private.csv>`. Replay loads the governed input contract, verifies frozen artifact hashes, uses frozen sufficient statistics, and reads thresholds from the frozen configuration; caller-injected thresholds are not used for final replay.

## Part 9 — Final Product & Portfolio Delivery

Part 9 is the flagship recruiter-facing overview. It is built from a deterministic source/metric/status/chart registry, surfaces real Part 2–4 aggregate evidence plus locked Part 6 graph aggregates, and keeps Part 5/7/8 conditional outputs visibly `INPUT_BLOCKED` when the required governed artifacts are unavailable. The page is `FINAL_PORTFOLIO_RELEASE_LOCKED`; this describes presentation completeness and claim-boundary lock, not enterprise deployment or completion of every upstream execution.

## Part 2 — Data & SQL Foundation

The Part 2 experience documents the transaction grain, entity keys, quality gates, fraud-label audit, leakage policy, Drive-only storage boundary, point-in-time feature rule, row reconciliation and chronological development/validation/OOT split. The verified source archive is stored in Google Drive. To reproduce the complete foundation without committing raw data, stage the extracted CSV in a temporary directory and run `python src/run_part2_pipeline.py --source-file <temporary-source.csv> --work-dir <temporary-work-dir>`, then run `python src/validate_outputs.py`. Raw data, processed Parquet, and the local DuckDB database are ignored by Git and should be deleted after the run.

## Limitations

- Synthetic financial transaction data
- No real device/IP fraud signals
- No production deployment or live scoring infrastructure
- No claims about real bank losses, customer impact, or regulatory validation

## Repository Structure

`index.html` and `part-1.html` contain the locked Part 1 experience. `part-2.html` contains the locked Data & SQL Foundation chapter, `part-3.html` contains the locked Fraud Portfolio Analytics chapter, `part-4.html` contains the locked Behavioral Fraud Analytics chapter, `part-5.html` contains the governed P5.1 modeling sprint, `part-7.html` contains the Block E decision-engine experience, and `part-8.html` contains the Block F monitoring chapter. Part 7 code lives in `src/part7/`; Part 8 code lives in `src/part8/`, with config in `config/part8/`, SQL in `sql/part8/`, docs in `docs/PART8_*.md`, and public-safe outputs in `reports/part8/`. Row-level source data, scores, labels and decisions are never copied into this repository; only public-safe aggregate evidence and lineage hashes are retained.
