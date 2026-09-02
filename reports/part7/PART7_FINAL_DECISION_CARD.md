# Block E / Part 7 — Final decision card

## Current status

`INPUT_BLOCKED` in the checked-in evidence snapshot. The public repository does not contain the approved frozen Part 5 row-level champion score, so no Part 7 threshold, action rate, fraud capture, exposure capture, or simulated cost is claimed here.

## Implemented decision contract

The executable policy layer maps each transaction to exactly one of `ALLOW`, `REVIEW`, or `BLOCK`. Review eligibility is separated from capacity allocation; review overflow has an explicit `ALLOW` fallback. Thresholds live in configuration and are selected chronologically on `P7_POLICY_TUNE`/`P7_POLICY_CONFIRM` before any final replay.

## Claim boundary

IBM TabFormer is synthetic. Economic, reviewer-performance, capacity, savings, and loss outcomes are simulated. This is not production execution, observed bank-loss prevention, regulatory approval, or globally unseen OOT. The defensible Part 7 claim, after a verified run, is only that the policy was frozen before the Part 7 replay.

## Required next step

Supply the exact frozen Part 5 score artifact and its calibration metadata to `src/part7/run_part7_pipeline.py`. The pipeline will fail closed if the score, calibration status, chronology, hashes, or mandatory gates are not valid.
