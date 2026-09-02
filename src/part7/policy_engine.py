from __future__ import annotations

import pandas as pd

from .contracts import PolicyConfig
from .economics import EconomicAssumptions, evaluate_economics
from .decision_runtime import decide
from .evaluation_runtime import evaluate_decisions


def run_policy(frame: pd.DataFrame, config: PolicyConfig, assumptions: EconomicAssumptions, calibrated_probability: bool, label_column: str = "fraud_label", emit_reason_codes: bool = True, evaluation_labels: pd.DataFrame | None = None, queue_config: dict | None = None) -> tuple[pd.DataFrame, dict]:
    """Compatibility facade; labels must be passed in a separate frame."""
    actions = decide(frame, config, calibrated_probability, emit_reason_codes=emit_reason_codes, queue_config=queue_config)
    if evaluation_labels is None:
        return actions, {}
    metrics = evaluate_decisions(actions, evaluation_labels, assumptions, label_column=label_column)
    metrics.update({"policy_version": config.policy_version, "priority_method": config.priority_method, "review_threshold": config.review_threshold, "block_threshold": config.block_threshold, "review_capacity": config.review_capacity, "feasible": True})
    return actions, metrics
