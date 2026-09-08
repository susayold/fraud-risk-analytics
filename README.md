# Financial Fraud Risk Analytics & Transaction Decisioning

Interactive fraud-risk portfolio built on the **IBM Synthetic Credit Card Transactions** dataset. The project connects audited transaction data to point-in-time behavioral features, fraud scoring, graph context, a frozen `ALLOW / REVIEW / BLOCK` decision policy, and offline monitoring/governance.

## Live Website

https://susayold.github.io/fraud-risk-analytics/

## Final Project Status

| Part | Chapter | Status |
|---|---|---|
| 1 | Business Scope & Governance | ✅ Ready |
| 2 | Data & SQL Foundation | ✅ Locked |
| 3 | Fraud Portfolio Analytics | ✅ Locked |
| 4 | Behavioral Fraud Analytics | ✅ Locked |
| 5 | Fraud Rules & Machine Learning | ✅ `FRAUD_CHAMPION_v1` locked |
| 6 | Network & Graph Analytics | ✅ Locked, research-bound |
| 7 | Fraud Risk Decision Engine | ✅ `DECISION_POLICY_LOCKED` — **64/64 PASS** |
| 8 | Monitoring, Drift & Governance | ✅ `MONITORING_GOVERNANCE_LOCKED` — **72/72 PASS** |
| 9 | Evidence & Audit | ✅ Presentation ready |

## Final Decision Evidence

Frozen balanced policy:

- Policy: `PART7_P4_0.014730_0.184344_0.0100_EXPOSURE_WEIGHTED_PROBABILITY`
- Review threshold: **1.4730%**
- Block threshold: **18.4344%**
- Review capacity: **1.00%**
- Final OOT rows: **1,782,241**
- Review rate: **0.6784%**
- Block rate: **0.0231%**
- Fraud transaction capture: **29.22%**
- Fraud exposure capture: **39.71%**
- Legitimate block rate: **0.0168%**
- Simulated total cost: **84,087.43** vs **103,934.50** for `ALLOW_ALL` (**~19.1% lower simulated cost**)

All economics are simulated and assumption-dependent; they are not actual bank savings.

## Model Generalization

The project intentionally preserves unfavorable evidence:

- Validation Selection PR-AUC: **0.8723**
- Final OOT PR-AUC: **0.06784**
- Final OOT ROC-AUC: **0.9423**
- Final OOT Brier: **0.000935**
- Final OOT Log Loss: **0.006074**

The model still ranks risk meaningfully, but temporal precision deteriorates sharply. Part 7 therefore evaluates whether a constrained policy can still create useful retrospective business outcomes rather than hiding the degradation.

## Monitoring & Governance

Part 8 is locked at **72/72 PASS** and separates two evidence clocks:

- `OPERATIONS_NOW` — label-free quality, drift, action mix, capacity and graph-novelty monitoring.
- `OUTCOMES_MATURED` — retrospective PR-AUC, ROC-AUC, KS, calibration and policy outcome evidence.

Matured calibration on the final observation set:

- Support: **1,782,241**
- Brier: **0.000935**
- Log Loss: **0.006074**
- ECE: **0.000490**

Unsupported monthly windows remain `INSUFFICIENT_SUPPORT`. Monitoring does **not** automatically retrain the model or mutate the frozen policy.

## Dataset

- 24,386,900 transactions
- 29,757 fraud transactions
- 2,000 users
- 6,139 cards
- 100,343 merchants
- Fraud rate ≈ 0.122%
- Synthetic financial data only

## Public / Private Boundary

GitHub and the website contain **aggregate evidence only**. Row-level source IDs, fraud labels, model scores, `ALLOW / REVIEW / BLOCK` decisions, raw graph edges, embeddings, model binaries and private decision marts are not published.

## Tech Stack

Python · SQL · DuckDB · Pandas · scikit-learn · XGBoost · CatBoost · AutoGluon · NetworkX / GraphSAGE · HTML / CSS / JavaScript

## Limitations

- Synthetic data; not evidence of real-bank prevalence or customer behavior.
- No production deployment or live scoring infrastructure.
- Monitoring is offline and retrospective, not live production monitoring.
- No claim of actual losses prevented, booked savings, regulatory validation or real customer impact.
- Graph evidence is supplementary and cannot independently auto-BLOCK.
