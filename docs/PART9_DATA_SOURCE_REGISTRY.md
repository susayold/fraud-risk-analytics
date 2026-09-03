# Part 9 Data Source Registry

The builder at `src/part9/build_part9_assets.py` is the single presentation data layer. It reads governed, compact artifacts already in the repository and never downloads raw transaction or graph data into the browser.

| Presentation surface | Source artifact | Claim class | Current state |
|---|---|---|---|
| Hero totals and class imbalance | `assets/data/part2_summary.json` | OBSERVED | AVAILABLE |
| Chronological split charts | `reports/split_summary.csv` | OBSERVED | AVAILABLE |
| Monthly / channel / amount / MCC portfolio charts | `reports/part3/*.csv` | OBSERVED | AVAILABLE |
| Behavioral feature family count | `docs/PART4_FEATURE_REGISTRY.csv` | DERIVED | AVAILABLE |
| Model metrics and curves | Part 5 executed reports | DERIVED | INPUT_BLOCKED until available |
| Graph novelty and incremental value | Part 6 governed aggregate reports | DERIVED | INPUT_BLOCKED until available |
| Decision mix, review capacity and economics | Part 7 final evidence | SIMULATED / DERIVED | INPUT_BLOCKED until available |
| Monitoring drift and matured performance | Part 8 final replay evidence | GOVERNANCE | INPUT_BLOCKED until available |

Each resolved artifact is hashed into `reports/part9/source_manifest.csv`. Conditional missing sources remain registered so the website can explain the dependency without inventing a result.
