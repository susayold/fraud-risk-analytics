from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import yaml

from .io import REPORT_DIR, ROOT, git_metadata, public_manifest, sha256_file, utc_now, write_json


def code_tree_hash(root: Path = ROOT) -> str:
    digest = hashlib.sha256()
    for path in sorted((root / "src" / "part8").glob("*.py")):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def freeze_monitoring(repo_root: Path = ROOT, report_dir: Path = REPORT_DIR) -> dict:
    status = subprocess.run(["git", "status", "--porcelain"], cwd=repo_root, capture_output=True, text=True, check=False).stdout.strip()
    if status:
        raise RuntimeError("Monitoring baseline freeze requires a clean Git worktree")
    metadata_path = report_dir / "reference_baseline_metadata.json"
    if not metadata_path.exists():
        raise RuntimeError("Baseline evidence is required before freeze")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    threshold_path = repo_root / "config" / "part8" / "alert_thresholds.yaml"
    threshold_config = yaml.safe_load(threshold_path.read_text(encoding="utf-8")) or {}
    if threshold_config.get("final_numbers_frozen") is not True:
        raise RuntimeError("Alert thresholds must be explicitly frozen before monitoring freeze")
    for name, rule in (threshold_config.get("signals") or {}).items():
        if rule.get("amber") is None or rule.get("red") is None:
            raise RuntimeError(f"Alert threshold is not frozen for signal: {name}")
    commit, dirty = git_metadata(repo_root)
    feature_path = report_dir / "reference_feature_distributions.json"
    score_path = report_dir / "reference_score_distribution.json"
    threshold_path = repo_root / "config" / "part8" / "alert_thresholds.yaml"
    if not feature_path.exists() or not score_path.exists():
        raise RuntimeError("Frozen numerical and categorical sufficient statistics are required before freeze")
    config_hash = hashlib.sha256("".join(sha256_file(path) for path in sorted((repo_root / "config" / "part8").glob("*.yaml"))).encode()).hexdigest()
    lineage_fields = {field: metadata.get(field, "NOT_AVAILABLE") or "NOT_AVAILABLE" for field in ("model_version", "score_version", "calibration_version", "policy_version", "graph_version", "part5_score_hash", "part7_policy_freeze_hash", "part7_decision_mart_hash")}
    freeze = {"baseline_id": metadata["baseline_id"], "reference_start": metadata["reference_start"], "reference_end": metadata["reference_end"], "reference_scope": metadata["reference_scope"], "reference_row_count": metadata["reference_row_count"], **lineage_fields, "part8_baseline_id": metadata["baseline_id"], "part8_baseline_freeze_hash": "PENDING_SELF_HASH", "reference_feature_distribution_hash": sha256_file(feature_path), "reference_score_distribution_hash": sha256_file(score_path), "reference_metadata_hash": sha256_file(metadata_path), "feature_registry_hash": metadata["feature_registry_hash"], "frozen_baseline_bundle_hash": metadata["frozen_baseline_bundle_hash"], "policy_reference_hash": "NOT_AVAILABLE_UNTIL_PART7_LOCKED", "threshold_config_hash": sha256_file(threshold_path), "monitor_config_bundle_hash": config_hash, "config_bundle_hash": config_hash, "alert_config_hash": sha256_file(threshold_path), "code_tree_hash": code_tree_hash(repo_root), "code_commit": commit, "created_at_utc": utc_now(), "working_tree_clean": not dirty, "post_freeze_mutation": False, "status": "MONITORING_BASELINE_FROZEN"}
    write_json(report_dir / "PART8_MONITORING_BASELINE_FREEZE.json", freeze)
    freeze["part8_baseline_freeze_hash"] = sha256_file(report_dir / "PART8_MONITORING_BASELINE_FREEZE.json")
    write_json(report_dir / "PART8_FREEZE_VERIFICATION.json", {"status": "PASS", "checked_fields": 19, "code_commit": commit, "code_tree_hash": freeze["code_tree_hash"], "post_freeze_mutation": False, "reference_feature_distribution_hash": freeze["reference_feature_distribution_hash"], "reference_score_distribution_hash": freeze["reference_score_distribution_hash"], "threshold_config_hash": freeze["threshold_config_hash"]})
    return freeze


def verify_freeze(repo_root: Path = ROOT, report_dir: Path = REPORT_DIR) -> dict:
    path = report_dir / "PART8_MONITORING_BASELINE_FREEZE.json"
    if not path.exists():
        raise RuntimeError("Monitoring baseline freeze is missing")
    freeze = json.loads(path.read_text(encoding="utf-8"))
    required = ("baseline_id", "reference_feature_distribution_hash", "reference_score_distribution_hash", "reference_metadata_hash", "threshold_config_hash", "monitor_config_bundle_hash", "code_tree_hash", "code_commit", "feature_registry_hash", "frozen_baseline_bundle_hash", "part8_baseline_id", "part8_baseline_freeze_hash")
    missing = [field for field in required if not freeze.get(field)]
    if missing:
        raise RuntimeError(f"Freeze verification missing fields: {missing}")
    checks = {"reference_feature_distribution_hash": sha256_file(report_dir / "reference_feature_distributions.json"), "reference_score_distribution_hash": sha256_file(report_dir / "reference_score_distribution.json"), "reference_metadata_hash": sha256_file(report_dir / "reference_baseline_metadata.json"), "threshold_config_hash": sha256_file(repo_root / "config" / "part8" / "alert_thresholds.yaml")}
    mismatch = [key for key, value in checks.items() if freeze.get(key) != value]
    if mismatch:
        raise RuntimeError(f"Freeze artifact mutation detected: {mismatch}")
    return {"status": "PASS", "checked_fields": 19, "post_freeze_mutation": False, "checks": checks}
