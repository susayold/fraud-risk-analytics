from __future__ import annotations

from dataclasses import replace

import pandas as pd

from .economics import EconomicAssumptions, evaluate_economics
from .decision_runtime import decide
from .evaluation_runtime import evaluate_decisions


def scenarios(base: EconomicAssumptions) -> list[tuple[str, EconomicAssumptions]]:
    # FAST FINAL: retain representative downside/upside economic stresses.
    return [
        ("FRAUD_LOSS_LOW", replace(base, fraud_loss_fraction=0.50)),
        ("FRAUD_LOSS_BASE", base),
        ("FRAUD_LOSS_HIGH", replace(base, fraud_loss_fraction=0.90)),
        ("REVIEW_COST_DOUBLE", replace(base, review_cost_per_case=base.review_cost_per_case * 2)),
        (
            "FRICTION_DOUBLE",
            replace(
                base,
                false_block_fixed_friction_cost=base.false_block_fixed_friction_cost * 2,
                false_block_amount_friction_rate=base.false_block_amount_friction_rate * 2,
            ),
        ),
    ]


def run_sensitivity(
    frame: pd.DataFrame,
    config,
    base: EconomicAssumptions,
    calibrated_probability: bool,
    queue_config: dict | None = None,
    precedence_config: dict | None = None,
    graph_weights: dict[str, float] | None = None,
) -> pd.DataFrame:
    rows = []
    decision_frame = frame.drop(columns=["fraud_label"], errors="ignore")
    labels = frame[["source_row_id", "fraud_label"]]

    for scenario_id, assumption in scenarios(base):
        actions = decide(
            decision_frame,
            config,
            calibrated_probability,
            queue_config=queue_config,
            precedence_config=precedence_config,
            graph_weights=graph_weights,
        )
        metrics = evaluate_decisions(actions, labels, assumption)
        rows.append(
            {
                "scenario_id": scenario_id,
                "assumption_version": "PART7_ECONOMICS_v1.0_FAST_FINAL",
                **{
                    key: metrics[key]
                    for key in (
                        "review_rate",
                        "block_rate",
                        "fraud_capture",
                        "fraud_exposure_capture",
                        "legitimate_blocked",
                        "legitimate_intervention_rate",
                        "simulated_total_cost",
                    )
                },
            }
        )

    for capacity in (0.005, 0.01):
        actions = decide(
            decision_frame,
            replace(config, review_capacity=capacity),
            calibrated_probability,
            queue_config=queue_config,
            precedence_config=precedence_config,
            graph_weights=graph_weights,
        )
        metrics = evaluate_decisions(actions, labels, base)
        rows.append(
            {
                "scenario_id": f"CAPACITY_{capacity:.4f}",
                "assumption_version": "PART7_ECONOMICS_v1.0_FAST_FINAL",
                "review_capacity": capacity,
                **{
                    key: metrics[key]
                    for key in (
                        "review_rate",
                        "block_rate",
                        "fraud_capture",
                        "fraud_exposure_capture",
                        "legitimate_blocked",
                        "legitimate_intervention_rate",
                        "simulated_total_cost",
                    )
                },
            }
        )

    for multiplier in (0.5, 1.5):
        stressed_actions = decide(
            decision_frame,
            config,
            calibrated_probability,
            queue_config=queue_config,
            precedence_config=precedence_config,
            graph_weights=graph_weights,
        )
        evaluated = stressed_actions.merge(
            labels, on="source_row_id", how="left", validate="one_to_one"
        )
        metrics = evaluate_economics(evaluated, base, prevalence_weight=multiplier)
        rows.append(
            {
                "scenario_id": f"SIMULATED_PREVALENCE_STRESS_{multiplier:.1f}X",
                "assumption_version": "PART7_ECONOMICS_v1.0_FAST_FINAL",
                "prevalence_multiplier": multiplier,
                **{
                    key: metrics[key]
                    for key in (
                        "review_rate",
                        "block_rate",
                        "fraud_capture",
                        "fraud_exposure_capture",
                        "legitimate_blocked",
                        "legitimate_intervention_rate",
                        "simulated_total_cost",
                    )
                },
            }
        )

    return pd.DataFrame(rows)
