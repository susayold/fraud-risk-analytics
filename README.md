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
| 2 | Data & SQL Foundation | ✅ Complete |
| 3 | Fraud Portfolio Analytics | ⬜ Planned |
| 4 | Behavioral Fraud Analytics | ⬜ Planned |
| 5 | Fraud Rules & Machine Learning | ⬜ Planned |
| 6 | Network & Graph Fraud Analytics | ⬜ Planned |
| 7 | Fraud Risk Decision Engine | ⬜ Planned |
| 8 | Monitoring, Drift & Governance | ⬜ Planned |
| 9 | Final Product & Portfolio | ⬜ Planned |

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

Part 1 defines business context, fraud use case, KPI framework, validation questions, decision architecture, scope boundary, claim boundary, and governance principles. Part 2 adds the reproducible data inventory, streaming audit, Parquet/DuckDB and SQL-foundation scaffolding. Observed metrics are sourced from the IBM TabFormer transaction archive stored on Google Drive; the raw archive is not committed to GitHub.

## Part 2 — Data & SQL Foundation

The Part 2 experience documents the transaction grain, entity keys, quality gates, fraud-label audit, leakage policy, storage boundary, point-in-time feature rule, and chronological development/validation/OOT split. The verified source archive is stored in the private Google Drive `Fraud Risk` folder. To reproduce the audit without committing raw data, stage the extracted CSV in a temporary directory and run `python src/audit.py --raw-dir <temporary-source-dir>`, then run `python src/validate_outputs.py`. Raw data, processed Parquet, and the local DuckDB database are ignored by Git.

## Limitations

- Synthetic financial transaction data
- No real device/IP fraud signals
- No production deployment or live scoring infrastructure
- No claims about real bank losses, customer impact, or regulatory validation

## Repository Structure

`index.html` and `part-1.html` contain the locked Part 1 experience. `part-2.html` contains the Data & SQL Foundation chapter; `part-3.html` through `part-9.html` provide the standardized chapter shell for subsequent work. Shared motion lives in `js/`, visual tokens and responsive styling live in `css/`, and supplied artwork lives in `assets/`.
