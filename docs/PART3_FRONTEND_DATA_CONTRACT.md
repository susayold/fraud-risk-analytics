# Part 3 — Frontend Data Contract

The public website reads only `assets/data/part3_summary.json`. The JSON is generated from aggregate Part 3 reports and is validated before it is written. Full aggregate CSVs remain in `reports/part3/`; row-level identifiers and raw data are not public artifacts.

## Required top-level objects

The summary must contain:

`status`, `analysis_scope`, `development`, `portfolio_metrics`, `monthly_trend`, `yearly_trend`, `channel`, `amount_bands`, `amount_distribution`, `mcc`, `geography`, `concentration`, `priority_segments`, `stability`, `findings`, `governance`, `artifact_counts`.

`status` is `PORTFOLIO_READY` and detailed discovery objects use `DEVELOPMENT_DISCOVERY`. `stability` alone uses `SPLIT_STABILITY`.

## Render contracts

| Renderer | Required fields |
|---|---|
| `renderTrend` | `month`, `fraud_rate`, `fraud_transactions`, `transactions` |
| `renderChannels` | `segment_value`, `fraud_rate`, `fraud_lift`, `fraud_capture_share` |
| `renderAmount` | `segment_value`, `transaction_share`, `fraud_lift`, `fraud_transactions`, `fraud_amount_capture_share` |
| `renderMcc` | `segment_value`, `fraud_lift`, `fraud_rate`, `fraud_transactions`, `priority_class` |
| `renderGeography` | `segment_value`, `fraud_capture_share`, `fraud_lift`, `transactions` |
| `renderConcentration` | `top_1pct_fraud_share`, `top_100_fraud_share`, `fraud_affected_entities`, `repeat_fraud_entities` |
| `renderPriority` | `segment_type`, `segment_value`, `transaction_share`, `fraud_lift`, `fraud_transactions`, `priority_class`, `fraud_capture_share`, `fraud_amount_capture_share` |

## Priority schema

Every `priority_segments` row contains `analysis_scope`, `segment_type`, `segment_value`, `transactions`, `transaction_share`, `fraud_transactions`, `fraud_rate`, `fraud_lift`, `fraud_capture_share`, `fraud_amount_capture_share`, `support_status` and `priority_class`.

Public material MCC rows carry the same risk fields plus the real `priority_class` from the matching `mcc` row in `segment_priority.csv`. Missing priority mapping is a build-time error; the frontend does not silently convert it to `MONITOR`.

`transaction_share`, `fraud_transactions`, `fraud_rate`, `fraud_lift` and `fraud_capture_share` are finite and bounded as appropriate. Signed `fraud_amount_capture_share` may be negative for refund-like bands and may be null where a segment has no fraud amount denominator.

## Stability boundary

Validation and Out-of-Time data are used only in the aggregate split-stability summary. No detailed OOT segment rows are included in the frontend summary.
