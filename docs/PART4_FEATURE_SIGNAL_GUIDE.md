# Part 4 — Feature signal guide

Feature signal profiles are descriptive Development-only associations. Numeric bin edges are frozen in `config/part4_signal_bins.yml` from Development and applied unchanged for reporting. A signal is not incremental model value, a causal effect, a production threshold or a loss estimate.

Public interpretation requires support of at least 1,000 transactions. Lower-support rows remain in the aggregate report with `LOW_SUPPORT` so that coverage is not hidden. The public chart mutes those bins and labels them descriptive-only; automated findings only use `INTERPRETABLE` rows. No SHAP, feature importance or AUC claim belongs in Part 4.

Bins are feature-specific: velocity counts use `0, 1, 2–4, 5–9, 10–19, 20+`; recency uses time units; amount ratios use multiplicative bands; z-scores preserve direction instead of using `ABS(z)`.

The primary contract is intentionally narrow: 1-hour, 24-hour and 7-day history windows; prior counts and recency; positive-purchase amount baselines and deviations; merchant/MCC/channel familiarity; and explicit cold-start flags.
