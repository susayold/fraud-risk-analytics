# Part 3 — Segment Definitions

## Amount bands

Development uses mutually exclusive, exhaustive fixed bands after inspecting the signed amount distribution:

`NEGATIVE / REFUND-LIKE`, `ZERO`, `>0–25`, `25–50`, `50–100`, `100–250`, `250–500`, `500+`.

Negative and zero amounts are retained as diagnostic segments. They are not silently mixed with positive purchase bands.

## Support and missing categories

`SUFFICIENT` means at least 1,000 Development transactions. Otherwise the row is `LOW_SUPPORT`; it remains in the report but is excluded from priority interpretation.

Null or blank categorical values become `<UNKNOWN>` for portfolio grouping. The state report must therefore include the missing geography segment.

## Channel mapping

Raw `Use Chip` labels are retained without renaming. Current observed values include `Swipe Transaction`, `Chip Transaction` and `Online Transaction`; blanks would be grouped as `<UNKNOWN>`. No canonical label is substituted for the source value.

## MCC and geography

MCC remains the authoritative categorical code; no unofficial MCC description is added. State is the primary public geography view, with merchant city as a secondary aggregate report. `Merchant Name` is an identifier-like value, not a validated merchant master.

## Entity concentration

User, card and merchant concentration reports publish aggregate entity counts and top-N shares without exposing entity IDs. A repeat-fraud entity is an entity with at least two retrospective fraud-labeled transactions. This is descriptive only and cannot be used directly as a model feature.

## Priority classes

`PRIORITY_1` requires sufficient support, lift ≥ 2.0x and either ≥5% fraud capture or ≥5% signed fraud-amount capture. `PRIORITY_2` requires sufficient support and lift ≥1.25x, ≥3% fraud capture or ≥3% signed fraud-amount capture. Other sufficient segments are `MONITOR`; low-support segments are `LOW_PRIORITY`. These are transparent investigation priorities, not rules.
