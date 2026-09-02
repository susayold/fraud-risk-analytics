# Part 7 economic assumptions

`config/part7/economic_assumptions.yaml` is a transparent simulation register. The base/low/high values are normalized scenario parameters, not bank facts, observed losses, or staffing commitments. All entries have `claim_type: SIMULATED` and `source_type: PROJECT_ASSUMPTION`.

Exposure bases are explicit:

- E0 `signed_amount`: source reconciliation only.
- E1 `positive_exposure = max(amount, 0)`: primary simulation basis.
- E2 `absolute_exposure = abs(amount)`: sensitivity only.

No signed amount is called realized fraud loss. The cost engine decomposes missed-fraud cost, residual blocked/reviewed fraud cost, review handling cost, false-block friction, simulated false rejection, and review delay.
