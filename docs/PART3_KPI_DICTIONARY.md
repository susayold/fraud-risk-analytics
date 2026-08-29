# Part 3 — KPI Dictionary

All detailed portfolio discovery uses `DEVELOPMENT_DISCOVERY` and the locked `analytics.part3_development` view. These are descriptive portfolio measures, not probability of default, causal effects, realized loss, loss prevented or production performance.

| KPI | Definition | Interpretation |
|---|---|---|
| Transaction Count | `COUNT(*)` | Population volume in the scope. |
| Fraud Transaction Count | `SUM(fraud_label)` | Count of synthetic rows labeled fraud. |
| Fraud Rate | `fraud_transactions / transactions` | Observed prevalence in the scope or segment. |
| Transaction Amount | `SUM(amount)` | Signed source amount; negative and zero values are retained. |
| Fraud-Labeled Amount | `SUM(amount) FILTER (fraud_label=1)` | Signed amount on fraud-labeled rows. |
| Fraud Amount Share | `fraud_amount / total_amount` | Signed amount share; not realized fraud loss. |
| Average Amount | `AVG(amount)` | Mean signed transaction amount. |
| Average Fraud Amount | `AVG(amount) FILTER (fraud_label=1)` | Mean signed amount on fraud-labeled rows. |
| Segment Fraud Lift | `segment_fraud_rate / development_fraud_rate` | Relative observed prevalence versus Development baseline. |
| Fraud Capture Share | `segment_fraud_transactions / development_fraud_transactions` | Share of Development fraud rows in the segment. |
| Amount Capture Share | `segment_fraud_amount / development_fraud_amount` | Share of signed fraud-labeled amount in the segment. |
| Top-N Concentration Share | `fraud rows among top-N entities / all Development fraud rows` | Retrospective concentration statistic. |

Support threshold for MCC, geography and priority interpretation is **1,000 Development transactions**. Rows below the threshold remain in raw aggregate reports as `LOW_SUPPORT` and are not allowed to dominate public ranking.
