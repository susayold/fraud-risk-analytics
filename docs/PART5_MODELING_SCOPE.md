# Part 5 modeling scope

Part 5 measures future fraud ranking under the frozen chronological splits from
Part 2 and the point-in-time behavioral contract from Part 4. The first sprint
uses a resource-safe execution mode: all Development fraud rows are retained,
legitimate Development rows are sampled deterministically at up to 20:1 within
calendar quarters, and Validation/OOT target rows are selected by fixed final
365-day windows without label-based sampling.

The full source history remains the history population required by Part 4 PIT
feature construction. It is separate from the smaller target modeling rows.
The pipeline reads `analytics.part4_evaluation_v1`, selects only target rows
needed for the current run, and writes private manifests/model matrices to a
caller-provided temporary directory. Raw data, row-level predictions, target
IDs, model matrices and serialized models are never public artifacts.

The first implementation sprint trains only Logistic Regression for F0
(current context) and F2 (current context plus the 43 governed Part 4
behavioral features). Rules, tree challengers, calibration comparison and OOT
scoring remain explicitly gated until the logistic pipeline has passed its
structural checks. No Part 5 `MODEL_READY` claim is valid before the final
frozen OOT evaluation.
