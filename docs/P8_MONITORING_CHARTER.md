# Block F / Part 8 — Monitoring Charter

## Purpose

Part 8 is an offline, retrospective monitoring and governance layer for the
frozen fraud score and decision policy. It answers whether the monitored
population, score, decision operations, graph context or matured outcomes are
changing enough to investigate.

## Scope

The framework covers data quality, feature and category drift, score drift,
matured model performance, calibration, fraud/outcome drift, policy and review
operations, graph novelty, segment stability, alert persistence and governance
recommendations.

## Non-goals

Part 8 does not train or recalibrate a model, retune Part 7 thresholds, change
review capacity, enable graph BLOCK, claim production deployment, claim real
bank losses or claim regulatory compliance.

## Two clocks

`OPERATIONS_NOW` is label-free and covers volume, schema, missingness, drift,
scores, actions, queue health and graph context. `OUTCOMES_MATURED` is a
separate retrospective branch for fraud prevalence, PR-AUC, calibration,
capture and simulated economics. The source does not provide observed label
arrival timestamps, so no operational latency is invented.

## Lock rule

The final lifecycle status is allowed only at `72 PASS / 0 BLOCKED / 0 FAIL`.
Before genuine Part 5 and Part 7 inputs are available, the public status is
`MONITORING_FRAMEWORK_READY / INPUT_BLOCKED`.

