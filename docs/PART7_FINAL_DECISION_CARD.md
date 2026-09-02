# Part 7 final decision card

## Status

`INPUT_BLOCKED` — this card is intentionally not a final recommendation. The public repo does not yet contain the approved frozen Part 5 row-level score artifact required to evaluate a Part 7 policy.

## Intended decision

The eventual policy will map each transaction to `ALLOW`, `REVIEW`, or `BLOCK`, with review capacity, amount-aware economics, imperfect human review, and graph-routing challengers evaluated chronologically.

## Claim boundary

IBM TabFormer is synthetic; economic and operational results are simulated; this is not production deployment, observed bank loss prevention, regulatory approval, or globally unseen OOT. The Part 7-specific claim will be that a policy was frozen before the Part 7 final replay.

## Required next input

Run `python src/part7/run_part7_pipeline.py --input <frozen-part5-score-file> --score-status PROBABILITY_USABLE` after the upstream artifact and its calibration metadata have been approved. The pipeline will write a decision card only after the corresponding gates pass.
