from __future__ import annotations

import pandas as pd

from .contracts import PolicyConfig
from .economics import EconomicAssumptions, evaluate_economics
from .review_queue import apply_policy


def run_policy(frame: pd.DataFrame, config: PolicyConfig, assumptions: EconomicAssumptions, calibrated_probability: bool, label_column: str = "fraud_label", emit_reason_codes: bool = True) -> tuple[pd.DataFrame, dict]:
    actions = apply_policy(frame, config.review_threshold, config.block_threshold, config.review_capacity, config.priority_method, calibrated_probability, emit_reason_codes=emit_reason_codes)
    metrics = evaluate_economics(actions.assign(**{label_column: frame[label_column].to_numpy()}), assumptions, label_column)
    metrics.update({"policy_version": config.policy_version, "priority_method": config.priority_method, "review_threshold": config.review_threshold, "block_threshold": config.block_threshold, "review_capacity": config.review_capacity, "feasible": True})
    return actions, metrics
