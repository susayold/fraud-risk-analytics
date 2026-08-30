# Part 5 model card — P5.1 Logistic baseline

## Purpose

Rank future card-transaction fraud risk using information available at T0.
Part 5 stops at predictive risk scores and diagnostic operating curves. It does
not set ALLOW, REVIEW or BLOCK policy thresholds.

## Current status

P5.1 is a governed implementation sprint. The public summary must remain
`MODELING_IN_PROGRESS` or `CHAMPION_SELECTED` until an executed run produces
real Validation metrics. It may become `MODEL_READY / LOCKED` only after the
frozen OOT evaluation and all validation gates pass.

## Inputs

F0 contains current amount, channel, MCC as categorical context and the
state-missing flag. F1 contains the 43 Part 4 behavioral features. F2 combines
F0 and F1. Raw identifiers, split name, fraud label, future information and
historical fraud-label aggregates are forbidden predictors.

Numeric NULLs use median imputation plus missingness indicators fitted on
Development only. Categorical encoding uses `handle_unknown=ignore`, so an
unseen OOT category such as Chip cannot crash scoring.

## Metrics and limitations

PR-AUC is primary; ROC-AUC, KS, Brier, log loss and Top-K capture are secondary
diagnostics. Accuracy is not a headline metric under rare fraud prevalence.
Metrics must state split, evaluation window, support and model version. No
causality, loss-prevented, production or full-population behavioral signal
claim is implied by a model score.
