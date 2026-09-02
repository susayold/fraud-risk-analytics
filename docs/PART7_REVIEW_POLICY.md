# Part 7 review policy

Review is two-stage: (A) score-band eligibility, then (B) deterministic capacity allocation. If eligible rows exceed `floor(capacity × population_rows)`, the highest-priority rows are selected and the overflow receives explicit `ALLOW`.

Priority challengers are `SCORE_ONLY`, `EXPOSURE_WEIGHTED_PROBABILITY` when calibration passes, `EXPOSURE_WEIGHTED_RANK` for ranking-only scores, `GRAPH_NOVELTY`, and `AMOUNT_GRAPH`. Graph modifiers can re-rank review candidates only; they cannot alter block eligibility in the base policy.
