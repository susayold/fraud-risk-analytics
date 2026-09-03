# Part 8 Research Evidence Register

| Source | Principle used | Part 8 implication | Claim boundary | Accessed |
|---|---|---|---|---|
| Microsoft Azure ML Model Monitoring | Multi-signal monitoring and baseline/observation comparisons | Separate data quality, drift, attribution/custom and performance signals | Architecture reference, not Azure deployment | 2026-09-03 |
| AWS SageMaker Model Monitor | Baselines, constraints, scheduled checks and violations | Freeze reference artifacts and report violations | Architecture reference; not AWS deployment | 2026-09-03 |
| Google Vertex AI Model Monitoring | Baseline/target datasets and scheduled sliding windows | Separate reference skew from temporal drift | Architecture reference; not Vertex deployment | 2026-09-03 |
| Stripe Radar Analytics | Payment time differs from fraud-arrival analysis; count and volume views | Two-clock label boundary and count/exposure duality | No observed fraud-arrival timestamp is invented | 2026-09-03 |
| Adyen Risk Management | Rules, review, backtesting and experiments | Backtest alerts before freeze; monitor policy operations | No live payment-system claim | 2026-09-03 |
| PayPal Fraud Protection | Review queue, risk score and triggered filters | Review queue and reason-code monitoring | No observed investigator metrics | 2026-09-03 |
| Mastercard Decision Intelligence | Context, behavior and relationship signals | Monitor graph/cold-start novelty separately | Graph remains non-blocking context | 2026-09-03 |
| Federal Reserve Model Risk Guidance 2026 | Ongoing monitoring, thresholds, limitations and outcomes | Monitoring card, thresholds, escalation and change records | Design reference, not regulatory compliance | 2026-09-03 |
| NIST AI RMF | Govern, Map, Measure, Manage | Ownership, lineage, metrics and response ladder | Design reference, not compliance claim | 2026-09-03 |
| Gama et al. 2014 | Concept drift is a relationship change, not any input shift | Use a drift taxonomy and outcome-qualified concept drift | No causal claim from PSI | 2026-09-03 |
| Dal Pozzolo et al. 2018 | Fraud has imbalance, drift and verification latency | Matured labels and support-aware metrics | Retrospective only for this dataset | 2026-09-03 |
| Carcillo et al. 2018 | Investigator selection creates verification bias | Do not equate reviewed fraud rate with population fraud rate | No real investigator process here | 2026-09-03 |
| Rabanser et al. 2019 | Dataset shift can fail silently | Label-free early warning is separate from failure proof | Warning, not model-failure proof | 2026-09-03 |
| Lipton et al. 2018 | Input shift differs from label shift | Monitor prevalence separately after maturity | No automatic concept-drift label | 2026-09-03 |

Primary URLs are preserved in the source plan supplied with this implementation.

