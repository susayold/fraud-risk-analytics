from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

from .io import sha256_file
from .freeze_monitoring import code_tree_hash


def _canonical_hash(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def load_frozen_thresholds(config_path: Path) -> dict:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if config.get("final_numbers_frozen") is not True:
        raise RuntimeError("Replay requires final_numbers_frozen=true")
    signals = config.get("signals") or {}
    if not signals or any(rule.get("amber") is None or rule.get("red") is None for rule in signals.values()):
        raise RuntimeError("Replay requires complete frozen alert thresholds")
    for name, rule in signals.items():
        if float(rule["red"]) < float(rule["amber"]):
            raise RuntimeError(f"Frozen threshold ordering invalid for {name}")
        if int(rule.get("min_support", 0)) <= 0:
            raise RuntimeError(f"Frozen threshold support invalid for {name}")
    return {str(name): dict(rule) for name, rule in signals.items()}


def verify_replay_contract(report_dir: Path, repo_root: Path, freeze_path: Path, frame=None) -> dict:
    if not freeze_path.exists():
        raise RuntimeError("Frozen baseline artifact is missing")
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    required = {"baseline_id", "reference_feature_distribution_hash", "reference_score_distribution_hash", "threshold_config_hash", "code_tree_hash", "code_commit", "frozen_baseline_bundle_hash"}
    missing = sorted(required - set(freeze))
    if missing:
        raise RuntimeError(f"Frozen baseline metadata missing: {missing}")
    feature_path = report_dir / "reference_feature_distributions.json"
    score_path = report_dir / "reference_score_distribution.json"
    threshold_path = repo_root / "config" / "part8" / "alert_thresholds.yaml"
    for path in (feature_path, score_path, threshold_path):
        if not path.exists():
            raise RuntimeError(f"Frozen replay artifact is missing: {path.name}")
    checks = {
        "reference_feature_distribution_hash": sha256_file(feature_path),
        "reference_score_distribution_hash": sha256_file(score_path),
        "threshold_config_hash": sha256_file(threshold_path),
    }
    for key, observed in checks.items():
        if freeze.get(key) != observed:
            raise RuntimeError(f"Frozen replay artifact hash mismatch: {key}")
    if freeze.get("code_tree_hash") != code_tree_hash(repo_root):
        raise RuntimeError("Frozen replay code tree hash mismatch")
    if frame is not None:
        for field in ("model_version", "score_version", "calibration_version", "policy_version", "graph_version"):
            values = frame[field].dropna().astype(str).unique().tolist() if field in frame else []
            expected = str(freeze.get(field, "NOT_AVAILABLE"))
            if values and expected not in {"", "NOT_AVAILABLE", "NOT_AVAILABLE_UNTIL_PART7_LOCKED"} and any(value != expected for value in values):
                raise RuntimeError(f"Lineage mismatch for {field}")
    return {"status": "PASS", "baseline_id": freeze["baseline_id"], "checks": checks, "lineage_checked": frame is not None}
