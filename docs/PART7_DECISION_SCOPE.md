# Part 7 — Decision scope

Block E converts a frozen fraud-risk score into exactly one transaction-level action: `ALLOW`, `REVIEW`, or `BLOCK`. It is a policy layer, not a new classifier.

## Locked boundaries

- Parts 1–6 remain upstream evidence and are not retrained or retuned here.
- The primary score must be the exact frozen Part 5 calibrated champion score, aliased as `PRIMARY_FRAUD_SCORE`.
- Part 6 graph signals are complementary review-routing context. Graph evidence cannot auto-block by default.
- The IBM TabFormer data is synthetic. Costs, capacity, reviewer performance, savings, and loss are simulated scenarios only.
- `oot_not_globally_unseen: true`: upstream Parts 5–6 already evaluated the same OOT period. The Part 7 claim is only that the policy is frozen before the Part 7 replay.

## Current execution status

The repository audit found no frozen Part 5 row-level score artifact in this public project. Therefore the executable pipeline fails closed at `P7-01 INPUT_BLOCKED`; it does not retrain, manufacture scores, or publish policy metrics.

Provide the approved score artifact through `--input` to continue with the same code path.
