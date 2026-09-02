from __future__ import annotations

from dataclasses import replace

import pandas as pd

from .economics import EconomicAssumptions, evaluate_economics
from .decision_runtime import decide
from .evaluation_runtime import evaluate_decisions


def scenarios(base: EconomicAssumptions) -> list[tuple[str, EconomicAssumptions]]:
    return [
        ("FRAUD_LOSS_LOW", replace(base, fraud_loss_fraction=0.50)), ("FRAUD_LOSS_BASE", base), ("FRAUD_LOSS_HIGH", replace(base, fraud_loss_fraction=0.90)),
        ("REVIEW_COST_HALF", replace(base, review_cost_per_case=base.review_cost_per_case * 0.5)), ("REVIEW_COST_DOUBLE", replace(base, review_cost_per_case=base.review_cost_per_case * 2)),
        ("FRICTION_HALF", replace(base, false_block_fixed_friction_cost=base.false_block_fixed_friction_cost * 0.5, false_block_amount_friction_rate=base.false_block_amount_friction_rate * 0.5)),
        ("FRICTION_DOUBLE", replace(base, false_block_fixed_friction_cost=base.false_block_fixed_friction_cost * 2, false_block_amount_friction_rate=base.false_block_amount_friction_rate * 2)),
        ("REVIEW_DETECTION_70", replace(base, review_fraud_detection_rate=0.70)), ("REVIEW_DETECTION_90", replace(base, review_fraud_detection_rate=0.90)), ("REVIEW_DETECTION_95", replace(base, review_fraud_detection_rate=0.95)),
        ("REVIEW_FALSE_REJECT_0.5", replace(base, review_legitimate_false_reject_rate=0.005)), ("REVIEW_FALSE_REJECT_2", replace(base, review_legitimate_false_reject_rate=0.02)), ("REVIEW_FALSE_REJECT_5", replace(base, review_legitimate_false_reject_rate=0.05)),
    ]


def run_sensitivity(frame: pd.DataFrame, config, base: EconomicAssumptions, calibrated_probability: bool, queue_config: dict | None = None, precedence_config: dict | None = None) -> pd.DataFrame:
    rows = []
    decision_frame = frame.drop(columns=["fraud_label"], errors="ignore")
    labels = frame[["source_row_id", "fraud_label"]]
    for scenario_id, assumption in scenarios(base):
        actions = decide(decision_frame, config, calibrated_probability, queue_config=queue_config, precedence_config=precedence_config)
        metrics = evaluate_decisions(actions, labels, assumption)
        rows.append({"scenario_id": scenario_id, "assumption_version": "PART7_ECONOMICS_v1.0", **{key: metrics[key] for key in ("review_rate", "block_rate", "fraud_capture", "fraud_exposure_capture", "legitimate_blocked", "legitimate_intervention_rate", "simulated_total_cost")}})
    for capacity in (0.001, 0.0025, 0.005, 0.01, 0.02, 0.05):
        actions = decide(decision_frame, replace(config, review_capacity=capacity), calibrated_probability, queue_config=queue_config, precedence_config=precedence_config)
        metrics = evaluate_decisions(actions, labels, base)
        rows.append({"scenario_id": f"CAPACITY_{capacity:.4f}", "assumption_version": "PART7_ECONOMICS_v1.0", "review_capacity": capacity, **{key: metrics[key] for key in ("review_rate", "block_rate", "fraud_capture", "fraud_exposure_capture", "legitimate_blocked", "legitimate_intervention_rate", "simulated_total_cost")}})
    for multiplier in (0.5, 1.0, 1.5, 2.0):
        # Prevalence stress is explicitly a retrospective reweighting diagnostic;
        # it never changes score thresholds or the decision API.
        stressed_actions = decide(decision_frame, config, calibrated_probability, queue_config=queue_config, precedence_config=precedence_config)
        evaluated = stressed_actions.merge(labels, on="source_row_id", how="left", validate="one_to_one")
        metrics = evaluate_economics(evaluated, base, prevalence_weight=multiplier)
        rows.append({"scenario_id": f"SIMULATED_PREVALENCE_STRESS_{multiplier:.1f}X", "assumption_version": "PART7_ECONOMICS_v1.0", "prevalence_multiplier": multiplier, **{key: metrics[key] for key in ("review_rate", "block_rate", "fraud_capture", "fraud_exposure_capture", "legitimate_blocked", "legitimate_intervention_rate", "simulated_total_cost")}})
    return pd.DataFrame(rows)
