# Part 7 score and decision-input contract

Required input columns are `source_row_id`, `transaction_timestamp`, `risk_score` (or `PRIMARY_FRAUD_SCORE`), `amount`, and `split_name`. Optional routing context includes `pair_new`, `cold_card`, `new_merchant`, `cross_community`, `use_chip`, and `merchant_category_code`.

The decision API never accepts `fraud_label`, `target`, chargeback, investigation outcomes, or future outcomes. A label may be joined only in the retrospective evaluation layer after actions are generated.

Scores must be finite and within the declared `[0, 1]` range. The score metadata must state whether it is a calibrated probability or ranking-only score. Expected-value priority (`probability × exposure`) is disabled for ranking-only scores; the permitted fallback is `EXPOSURE_WEIGHTED_RANK`.

Required split labels are chronological. Threshold search may use `P7_POLICY_TUNE`; policy selection may use `P7_POLICY_CONFIRM`; final OOT is never opened before a policy freeze.

Example invocation:

```text
python -m src.part7.run_part7_pipeline --input <private-score-file> --score-status PROBABILITY_USABLE --score-version <frozen-score-version> --model-version <frozen-model-version> --calibration-version <calibration-version>
```

If the artifact is ranking-only, use `--score-status RANKING_ONLY`; the pipeline will use `EXPOSURE_WEIGHTED_RANK` and will not label that priority as expected fraud value.
