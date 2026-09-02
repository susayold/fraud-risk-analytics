from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .contracts import PolicyConfig
from .economics import EconomicAssumptions
from .io import git_metadata, sha256_file
from .decision_runtime import decide
from .evaluation_runtime import evaluate_decisions


def load_and_verify_freeze(path: Path, config_paths: list[Path]) -> dict:
    freeze = json.loads(path.read_text(encoding="utf-8"))
    keys = ["economic_assumption_sha256", "graph_routing_sha256", "reason_code_sha256"]
    current = [sha256_file(p) for p in config_paths]
    if [freeze.get(k) for k in keys] != current:
        raise RuntimeError("Frozen config hashes do not match final replay inputs")
    for key, path in (("review_queue_config_sha256", path.parent / "review_queue.yaml"), ("action_precedence_sha256", path.parent / "action_precedence.yaml")):
        if freeze.get(key) and freeze[key] != sha256_file(path):
            raise RuntimeError(f"Frozen config hash does not match {path.name}")
    current_commit, _ = git_metadata()
    if freeze.get("code_commit") not in {current_commit, "UNKNOWN"}:
        raise RuntimeError("Final replay code commit does not match the policy freeze")
    if freeze.get("oot_not_globally_unseen") is not True:
        raise RuntimeError("OOT claim boundary is missing from the freeze")
    return freeze


def replay(frame: pd.DataFrame, freeze: dict, assumptions: EconomicAssumptions, calibrated_probability: bool, queue_config: dict | None = None) -> tuple[pd.DataFrame, dict]:
    config = PolicyConfig(freeze["policy_version"], float(freeze["review_threshold"]), float(freeze["block_threshold"]), float(freeze["review_capacity"]), freeze.get("priority_method", "SCORE_ONLY"))
    decision_frame = frame.drop(columns=["fraud_label"], errors="ignore")
    actions = decide(decision_frame, config, calibrated_probability, queue_config=queue_config)
    labels = frame[["source_row_id", "fraud_label"]] if "fraud_label" in frame else None
    if labels is None:
        raise ValueError("Final replay requires a separate evaluation label frame")
    return actions, evaluate_decisions(actions, labels, assumptions)
