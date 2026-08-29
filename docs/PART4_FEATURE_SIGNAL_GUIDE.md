# Part 4 — Feature signal guide

Feature signal profiles are descriptive Development-only associations. Numeric bin edges are fit on Development and applied only for reporting. A signal is not incremental model value, a causal effect, a production threshold or a loss estimate.

Public interpretation requires support of at least 1,000 transactions. Lower-support rows remain in the aggregate report with `LOW_SUPPORT` so that coverage is not hidden. No SHAP, feature importance or AUC claim belongs in Part 4.

The primary contract is intentionally narrow: 1-hour, 24-hour and 7-day history windows; prior counts and recency; positive-purchase amount baselines and deviations; merchant/MCC/channel familiarity; and explicit cold-start flags.

