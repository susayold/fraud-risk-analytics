# Part 4 — Cold-start policy

Cold start is explicit and family-specific. At the first observed user, card or merchant event, the corresponding `*_cold_start` flag is `1`, prior count is `0`, recency is `NULL`, and velocity is `0`. A first relationship (user–merchant, card–merchant, user–MCC, card–MCC or user/card–channel) has prior count `0` and `is_new = 1`.

The policy does not impute a synthetic prior event, backfill future history or use labels. For missing state, comparability is unavailable; the state familiarity feature remains `NULL` rather than treating missingness as a new state.

The left edge of the 1991 source period is left-censored: a transaction may be “first observed” without proving it is the first real-world transaction.

