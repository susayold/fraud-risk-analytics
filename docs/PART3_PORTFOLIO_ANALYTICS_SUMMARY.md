# Part 3 — Fraud Portfolio Analytics Summary

Status: `PORTFOLIO_READY` after all Part 3 fail-closed validation checks passed.

Part 3 consumes the locked Part 2 transaction base and quantifies Development-period fraud exposure before feature engineering. Detailed discovery is Development-only; Validation and OOT are protected except for predefined split-stability context.

## Data products

- `reports/part3/portfolio_summary.csv` — Development and full-history descriptive baselines.
- `reports/part3/monthly_fraud_trend.csv` and `yearly_fraud_trend.csv` — Development time trend.
- `reports/part3/channel_risk.csv`, `amount_band_risk.csv`, `mcc_risk.csv`, `state_risk.csv`, `merchant_city_risk.csv` — aggregate segment risk with support and lift.
- `reports/part3/user_concentration.csv`, `card_concentration.csv`, `merchant_concentration.csv` — aggregate entity concentration without IDs.
- `reports/part3/segment_priority.csv` — transparent risk/scale/impact priority classes.
- `reports/part3/split_stability_summary.csv` — predefined aggregate context across frozen splits.
- `reports/part3/part3_validation_report.csv` — fail-closed validation evidence.

## Handoff to Part 4

Part 3 supplies questions, not precomputed behavioral features. Potential questions include prior card velocity, channel-specific amount deviation, merchant novelty and customer–merchant history. Any later implementation must reconstruct history using the Part 2 rule `history.transaction_timestamp < current.transaction_timestamp`.

The split-stability context also shows a channel-mix shift: Chip Transaction is absent in Development, then appears in Validation and becomes dominant in OOT. Part 4/5 categorical preprocessing must therefore handle unseen channel values safely and monitor channel-mix drift without mining OOT subsegments.
