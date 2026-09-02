"""Config-driven precedence contract for policy actions."""
from __future__ import annotations

import numpy as np
import pandas as pd


DEFAULT_PRECEDENCE = [
    "INPUT_CONTRACT_FAILURE",
    "GOVERNED_ALLOW_OVERRIDE",
    "GOVERNED_HARD_BLOCK",
    "FROZEN_SCORE_BLOCK_BAND",
    "REVIEW_ELIGIBILITY_BAND",
    "REVIEW_QUEUE_CAPACITY",
    "REVIEW_OVERFLOW",
    "DEFAULT_ALLOW",
]


def candidate_actions(frame: pd.DataFrame, review_threshold: float, block_threshold: float, *, hard_block_enabled: bool = False) -> pd.Series:
    if hard_block_enabled:
        raise ValueError("Hard block is disabled in the default research boundary")
    return pd.Series(np.select([frame.risk_score >= block_threshold, frame.risk_score >= review_threshold], ["BLOCK", "REVIEW"], default="ALLOW"), index=frame.index)
