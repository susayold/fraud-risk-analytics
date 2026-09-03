# Part 8 Source Audit

## Reviewed dependencies

- Part 2 data contract and natural-prevalence validation boundary.
- Part 4 point-in-time behavioral feature contract (`history_timestamp < current_timestamp`).
- Part 5 frozen-score and PR-AUC metric hierarchy.
- Part 6 graph context and no-label graph feature boundary.
- Part 7 `ALLOW / REVIEW / BLOCK` policy and review-capacity contract.

## Current input boundary

No genuine frozen Part 5 row-level score or Part 7 locked decision mart is
copied into this repository. Part 8 can be built and tested with temporary
fixtures, but the real baseline and final replay remain `INPUT_BLOCKED` until
the governed upstream artifact is supplied through `--input`.

## Known limitations carried forward

The source is synthetic IBM TabFormer data, fraud is rare, channel mix changes
over time, structural missingness is known, and observed label arrival times
are unavailable. Part 8 records these facts rather than treating them as
production observations.

