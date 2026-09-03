# Part 8 Limitations

- This is an offline retrospective framework, not a deployed monitoring service.
- IBM TabFormer is synthetic and does not establish real bank behavior or real losses.
- `fraud_label` is not available with an observed operational arrival timestamp.
- Score drift is an early warning, not proof of model-performance degradation.
- Rare-event performance is marked `INSUFFICIENT_SUPPORT` when fraud support is low.
- Review metrics are policy simulations; no human investigator SLA or productivity is observed.
- Graph novelty is context shift and cannot autonomously change BLOCK eligibility.
- Final OOT is not used to tune alert thresholds.
- No fairness claim is made because protected-attribute governance is not established in the source.

