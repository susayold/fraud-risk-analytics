# Part 3 — Discovery Governance

## Development is the discovery population

Detailed segment discovery is restricted to `DEVELOPMENT` (1991-01-02 through 2011-06-15). Channel, amount-band, MCC, geography, interaction, concentration and priority outputs are therefore labeled `DEVELOPMENT_DISCOVERY`.

## Validation and OOT are protected

Validation (2011-06-16 through 2015-10-22) is reserved for later model comparison, threshold and policy selection. Out-of-Time (2015-10-23 through 2020-02-28) is reserved for the final temporal assessment. Part 3 does not rank detailed Validation/OOT segments or use OOT findings to choose Part 4 features.

The only cross-split output is the predefined `SPLIT_STABILITY` summary: transactions, fraud prevalence, signed fraud amount share and audited channel mix. This is descriptive context, not model tuning.

## What Part 3 may and may not do

- May quantify portfolio exposure, concentration, lift, support and temporal context.
- May identify questions for Part 4, such as card velocity, merchant novelty and channel-specific amount deviation.
- Must not train models, finalize ALLOW/REVIEW/BLOCK rules, or create production thresholds.
- Must not treat retrospective fraud concentration as a point-in-time feature.
- Must preserve Part 2 grain, target, strict history `< T0` policy and frozen split boundaries.

## Claim boundary

Findings are associations in IBM synthetic transaction data. They do not state that a channel, MCC, geography or entity causes fraud. Signed fraud amount is not realized economic loss.

## Downstream channel handoff

Chip Transaction is absent from Development but appears later in the frozen Validation/OOT channel-mix summary. Part 4 and Part 5 must use unknown-safe categorical preprocessing and monitor channel-mix drift. This is a preprocessing requirement, not permission to mine OOT Chip subsegments for feature design.
