# Block E / Part 7 — Final decision card

## Final status

`DECISION_POLICY_LOCKED` — **64 / 64 mandatory gates PASS, 0 BLOCKED, 0 FAIL**.

The final governed policy is `PART7_P4_0.014730_0.184344_0.0100_EXPOSURE_WEIGHTED_PROBABILITY` using frozen `FRAUD_CHAMPION_v1` probability scores.

## Frozen policy

- Review threshold: **0.0147300097** (~1.473%)
- Block threshold: **0.1843441516** (~18.434%)
- Review capacity: **1.0%**
- Priority method: **exposure-weighted probability**
- Action domain: **ALLOW / REVIEW / BLOCK**
- Graph-only automatic BLOCK: **forbidden**

## Final chronological OOT replay

Population: **1,782,241 transactions**, including **1,728 fraud transactions**.

- ALLOW rate: **99.2985%**
- REVIEW rate: **0.6784%**
- BLOCK rate: **0.0231%**
- Fraud transaction capture: **29.22%**
- Fraud exposure capture: **39.71%**
- Legitimate block rate: **0.0168%**
- Selected-policy simulated total cost: **84,087.43**
- ALLOW_ALL simulated total cost: **103,934.50**
- Simulated cost delta vs ALLOW_ALL: **-19.10%**

## Generalization evidence

The pre-OOT Confirmation scope was materially stronger than final OOT (Confirmation fraud capture ~93.61% vs final OOT ~29.22%). That degradation is intentionally retained as model/policy-risk evidence; final OOT was not used for policy retuning.

## Claim boundary

IBM TabFormer source data are synthetic. Economic assumptions, review effectiveness, intervention cost and loss prevention are simulated. The cost result is **not actual bank savings**. The final OOT is a chronological project holdout, not globally unseen production traffic. This repository is a portfolio case study, not a deployed fraud platform or regulatory validation.

## Public / private boundary

Only aggregate evidence is published. Row-level scores, labels and decision marts remain private. The final-run commit recorded in the execution artifacts is preserved as run provenance; later GitHub commits reconcile the public repository without rewriting that provenance.
