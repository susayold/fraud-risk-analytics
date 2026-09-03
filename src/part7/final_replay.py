from __future__ import annotations

from pathlib import Path

import pandas as pd

from .contracts import PolicyConfig
from .economics import EconomicAssumptions
from .replay_contract import config_map, verify_freeze
from .decision_runtime import decide
from .evaluation_runtime import evaluate_decisions
from .review_queue import time_bucket


def _allow_all_actions(frame: pd.DataFrame, queue_config: dict | None = None) -> pd.DataFrame:
    config = queue_config or {}
    result = frame.drop(columns=["fraud_label"], errors="ignore").copy()
    result["priority_method"] = "SCORE_ONLY"
    result["overflow_action"] = str(config.get("overflow", {}).get("action", "ALLOW")).upper()
    result["capacity_bucket"] = time_bucket(result.transaction_timestamp, config.get("bucket", {}).get("type", "DAY"), config.get("bucket", {}).get("timezone", "UTC"))
    result["candidate_action"] = "ALLOW"
    result["action"] = "ALLOW"
    result["review_priority"] = 0.0
    result["review_rank"] = pd.Series(pd.array([pd.NA] * len(result), dtype="Int64"), index=result.index)
    result["bucket_capacity"] = 0
    result["bucket_selected"] = False
    result["overflow"] = False
    result["reason_codes"] = ""
    return result


def load_and_verify_freeze(path: Path, config_paths: list[Path] | None = None, *, score_path: Path | None = None, part6_artifact_path: Path | None = None, selected_policy_path: Path | None = None, confirmation_manifest_path: Path | None = None, repo_root: Path = Path(__file__).resolve().parents[2], report_dir: Path = Path(__file__).resolve().parents[2] / "reports" / "part7", config_dir: Path = Path(__file__).resolve().parents[2] / "config" / "part7", code_root: Path = Path(__file__).resolve().parents[2]) -> dict:
    """Verify explicit config paths from config/part7, never reports/part7."""
    freeze, _ = verify_freeze(path, score_path=score_path, part6_artifact_path=part6_artifact_path, selected_policy_path=selected_policy_path, confirmation_manifest_path=confirmation_manifest_path, repo_root=repo_root, report_dir=report_dir, config_dir=config_dir, code_root=code_root)
    return freeze


def replay(frame: pd.DataFrame, freeze: dict, assumptions: EconomicAssumptions, calibrated_probability: bool, queue_config: dict | None = None, precedence_config: dict | None = None, graph_weights: dict[str, float] | None = None) -> tuple[pd.DataFrame, dict]:
    decision_frame = frame.drop(columns=["fraud_label"], errors="ignore")
    if freeze.get("policy_version") == "PART7_P0_ALLOW_ALL":
        actions = _allow_all_actions(decision_frame, queue_config)
    else:
        config = PolicyConfig(freeze["policy_version"], float(freeze["review_threshold"]), float(freeze["block_threshold"]), float(freeze["review_capacity"]), freeze.get("priority_method", "SCORE_ONLY"))
        actions = decide(decision_frame, config, calibrated_probability, queue_config=queue_config, precedence_config=precedence_config, graph_weights=graph_weights)
    labels = frame[["source_row_id", "fraud_label"]] if "fraud_label" in frame else None
    if labels is None:
        raise ValueError("Final replay requires a separate evaluation label frame")
    return actions, evaluate_decisions(actions, labels, assumptions)
