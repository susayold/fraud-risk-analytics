# Part 5 frontend data contract

The frontend consumes `assets/data/part5_summary.json`. It must render
`MODEL VALIDATION REVIEW` when `validation.status` is not `PASS`, and it must
never turn missing metrics into zeros. `MODEL READY · LOCKED` is displayed only
when `status=MODEL_READY`, `lock_status=LOCKED` and validation is `PASS`.

Required public fields are `status`, `lock_status`,
`model_contract_version`, `execution`, `splits`, `feature_sets`, `models`,
`validation_metrics`, `calibration`, `topk`, `incremental_value`,
`oot_metrics`, `subgroups`, `feature_importance`, `champion`, `validation`,
`governance` and `findings`. Public arrays contain aggregate values only; no
row-level scores, IDs, matrices or SHAP observations are allowed.
