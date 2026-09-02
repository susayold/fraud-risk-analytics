from __future__ import annotations

from pathlib import Path

import pandas as pd

from .contracts import PolicyConfig
from .economics import EconomicAssumptions
from .replay_contract import config_map, verify_freeze
from .decision_runtime import decide
from .evaluation_runtime import evaluate_decisions


def load_and_verify_freeze(path: Path, config_paths: list[Path] | None = None, *, score_path: Path | None = None, part6_artifact_path: Path | None = None) -> dict:
    """Verify explicit config paths from config/part7, never reports/part7."""
    freeze, _ = verify_freeze(path, score_path=score_path, part6_artifact_path=part6_artifact_path)
    return freeze


def replay(frame: pd.DataFrame, freeze: dict, assumptions: EconomicAssumptions, calibrated_probability: bool, queue_config: dict | None = None, precedence_config: dict | None = None) -> tuple[pd.DataFrame, dict]:
    config = PolicyConfig(freeze["policy_version"], float(freeze["review_threshold"]), float(freeze["block_threshold"]), float(freeze["review_capacity"]), freeze.get("priority_method", "SCORE_ONLY"))
    decision_frame = frame.drop(columns=["fraud_label"], errors="ignore")
    actions = decide(decision_frame, config, calibrated_probability, queue_config=queue_config, precedence_config=precedence_config)
    labels = frame[["source_row_id", "fraud_label"]] if "fraud_label" in frame else None
    if labels is None:
        raise ValueError("Final replay requires a separate evaluation label frame")
    return actions, evaluate_decisions(actions, labels, assumptions)
