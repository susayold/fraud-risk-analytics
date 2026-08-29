# Part 4 — Point-in-time policy

Part 4 builds behavioral features from the transaction history available strictly before the current event timestamp `T0`.

## Locked rule

```text
history_timestamp < current_timestamp
```

The strict less-than rule excludes the current row, future rows and all peer rows with the same timestamp. There is no deterministic event ordering within a timestamp in this v1 contract, so same-timestamp peers are intentionally excluded.

History is continuous across the Development, Validation and Out-of-Time boundaries. The split changes the evaluation label context; it does not reset customer, card or merchant history.

## Label governance

The source contains `fraud_label`, but it has no `label_available_timestamp`. Therefore labels are excluded from the behavior source and all feature-family SQL. The label is joined only after feature construction for Development-only signal profiling and aggregate validation.

## Null semantics

- no prior event: prior count and velocity are `0`; recency is `NULL`; cold-start is `1`;
- no positive amount history: amount ratios are `NULL`;
- insufficient amount history or zero standard deviation: z-score is `NULL`;
- missing current state: geography familiarity is `NULL`, not `is_new = 1`;
- unseen categorical value: prior count `0`, `is_new = 1`, no pipeline failure.

This is an offline analytical contract. It is not a production latency or deployment claim.
