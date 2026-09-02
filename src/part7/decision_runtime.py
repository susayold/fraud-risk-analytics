"""Label-free decision runtime for Block E.

This module is intentionally unable to accept a retrospective outcome label.
Evaluation is a separate runtime and joins outcomes only after actions exist.
"""
from __future__ import annotations

import pandas as pd

from .contracts import PolicyConfig, assert_policy_columns
from .review_queue import apply_policy


def decide(
    frame: pd.DataFrame,
    config: PolicyConfig,
    calibrated_probability: bool = False,
    *,
    high_amount_cutoff: float | None = None,
    queue_config: dict | None = None,
    precedence_config: dict | None = None,
    emit_reason_codes: bool = True,
) -> pd.DataFrame:
    """Produce one action per row without labels or future outcomes."""
    assert_policy_columns(frame.columns)
    return apply_policy(
        frame,
        config.review_threshold,
        config.block_threshold,
        config.review_capacity,
        config.priority_method,
        calibrated_probability,
        high_amount_cutoff,
        emit_reason_codes,
        queue_config=queue_config,
        precedence_config=precedence_config,
    )
