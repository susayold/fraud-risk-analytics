# Part 8 Monitoring Card

| Field | Contract |
|---|---|
| Purpose | Offline fraud-risk monitoring and governance |
| Input | Private row-level monitoring mart from governed upstream artifacts |
| Reference | Natural-prevalence Validation / P7 confirmation, never final OOT for tuning |
| Cadence | Daily operations, weekly drift, monthly matured outcomes |
| Early signals | Data quality, category novelty, feature/score drift, action mix, review capacity, graph context |
| Mature signals | PR-AUC, ROC-AUC, KS, Brier, log loss, ECE, fraud/exposure capture |
| Alert method | Empirical pre-OOT thresholds + support + persistence + corroboration |
| Label timing | No observed arrival timestamp; matured outputs are retrospective only |
| Limitations | Synthetic IBM TabFormer data, simulated economics, no human investigator operation |
| Escalation | OBSERVE → INVESTIGATE → owner review recommendation |
| Ownership | Fraud Risk Owner, Model Owner, Data Owner, Policy Owner, Independent Reviewer |

Part 8 emits recommendations only. Retraining returns to Part 5, graph changes
to Part 6 and decision-policy changes to Part 7.

