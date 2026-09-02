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


def load_precedence_config(path) -> dict:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML is required to load action precedence") from exc
    config = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    steps = config.get("ordered_steps", [])
    unknown = sorted(set(steps) - set(DEFAULT_PRECEDENCE))
    if unknown or steps != DEFAULT_PRECEDENCE:
        raise ValueError(f"Unsupported or incomplete action precedence: {unknown or steps}")
    return config


def candidate_actions(frame: pd.DataFrame, review_threshold: float, block_threshold: float, *, precedence_config: dict | None = None) -> pd.Series:
    config = precedence_config or {"hard_block": {"enabled": False}, "allow_override": {"enabled": False}}
    if config.get("allow_override", {}).get("enabled", False):
        raise ValueError("Allow override is declared but no governed override predicate is configured")
    if config.get("hard_block", {}).get("enabled", False):
        raise ValueError("Hard block is disabled in the default research boundary")
    return pd.Series(np.select([frame.risk_score >= block_threshold, frame.risk_score >= review_threshold], ["BLOCK", "REVIEW"], default="ALLOW"), index=frame.index)
