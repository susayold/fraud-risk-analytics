# Part 5 sampling and weighting policy

- Keep every Development fraud row in the training target population.
- Sample legitimate Development rows deterministically using `md5(source_row_id
  || seed)` and calendar-quarter strata.
- Use a maximum initial ratio of 20 legitimate rows per retained fraud row in
  each quarter. The executed report, not this policy default, is authoritative
  for the final count.
- Apply negative sample weight `N_legitimate_full / N_legitimate_sample` during
  model fitting. Validation and OOT are natural-prevalence evaluation windows
  and are never case-control sampled.
- SMOTE, ADASYN and synthetic oversampling are not used as the primary strategy.
- The private target manifest is hashed for reproducibility; row IDs and
  predictions are not published.
