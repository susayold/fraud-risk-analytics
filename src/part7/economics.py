from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class EconomicAssumptions:
    fraud_loss_fraction: float
    block_effectiveness: float
    review_cost_per_case: float
    review_fraud_detection_rate: float
    review_legitimate_false_reject_rate: float
    false_block_fixed_friction_cost: float
    false_block_amount_friction_rate: float
    review_delay_cost: float


def evaluate_economics(frame: pd.DataFrame, assumptions: EconomicAssumptions, label_column: str = "fraud_label", prevalence_weight: float = 1.0) -> dict[str, float | int | None]:
    if label_column not in frame:
        raise ValueError("Outcome labels are evaluation-only and must be joined after policy actions")
    y = frame[label_column].astype(int).to_numpy()
    x = frame.positive_exposure.astype(float).to_numpy()
    action = frame.action.astype(str).to_numpy()
    fraud = y == 1
    legit = ~fraud
    allow = action == "ALLOW"
    review = action == "REVIEW"
    block = action == "BLOCK"
    missed = x * assumptions.fraud_loss_fraction * float(prevalence_weight)
    allow_cost = np.where(allow & fraud, missed, 0.0)
    block_cost = np.where(block & fraud, missed * (1 - assumptions.block_effectiveness), 0.0) + np.where(block & legit, assumptions.false_block_fixed_friction_cost + x * assumptions.false_block_amount_friction_rate, 0.0)
    review_cost = np.where(review, assumptions.review_cost_per_case + assumptions.review_delay_cost, 0.0)
    review_cost += np.where(review & fraud, missed * (1 - assumptions.review_fraud_detection_rate), 0.0)
    review_cost += np.where(review & legit, assumptions.review_legitimate_false_reject_rate * (assumptions.false_block_fixed_friction_cost + x * assumptions.false_block_amount_friction_rate), 0.0)
    total = allow_cost + block_cost + review_cost
    total_fraud = int(fraud.sum())
    total_exposure = float(x[fraud].sum())
    def rate(mask: np.ndarray) -> float:
        return float(mask.mean()) if len(mask) else 0.0
    def capture(mask: np.ndarray) -> float | None:
        return float(mask[fraud].sum() / total_fraud) if total_fraud else None
    return {
        "transactions": int(len(frame)), "fraud_rows": total_fraud,
        "allow_count": int(allow.sum()), "review_count": int(review.sum()), "block_count": int(block.sum()),
        "allow_rate": rate(allow), "review_rate": rate(review), "block_rate": rate(block),
        "fraud_allowed": int((allow & fraud).sum()), "fraud_reviewed": int((review & fraud).sum()), "fraud_blocked": int((block & fraud).sum()),
        "fraud_capture": float(1 - (allow & fraud).sum() / total_fraud) if total_fraud else None,
        "review_fraud_capture": capture(review), "block_fraud_capture": capture(block),
        "legitimate_reviewed": int((review & legit).sum()), "legitimate_blocked": int((block & legit).sum()),
        "legitimate_block_rate": float((block & legit).sum() / legit.sum()) if legit.sum() else 0.0,
        "legitimate_intervention_rate": rate((review | block) & legit), "false_block_rate": rate(block & legit),
        "total_positive_exposure": float(x.sum()), "fraud_positive_exposure": total_exposure,
        "allowed_fraud_exposure": float(x[allow & fraud].sum()), "reviewed_fraud_exposure": float(x[review & fraud].sum()), "blocked_fraud_exposure": float(x[block & fraud].sum()),
        "fraud_exposure_capture": float(1 - x[allow & fraud].sum() / total_exposure) if total_exposure else None,
        "simulated_missed_fraud_cost": float(allow_cost.sum()), "simulated_review_cost": float(review_cost.sum()), "simulated_false_block_cost": float(block_cost[legit & block].sum()),
        "simulated_total_cost": float(total.sum()),
    }
