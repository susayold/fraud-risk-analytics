from __future__ import annotations

from pathlib import Path

import hashlib
import json

from .io import REPORT_DIR, ROOT, sha256_file, utc_now, write_json, git_metadata
from .replay_contract import bundle_hash, code_tree_hash


def freeze_policy(selected: dict, config_paths: list[Path], score_version: str, model_version: str, calibration_version: str | None, *, score_status: str | None = None, score_path: Path | None = None, graph_version: str | None = None, part6_artifact_version: str | None = None, part6_artifact_hash: str | None = None, confirmation_scope_hash: str | None = None, selected_policy_path: Path | None = None, confirmation_manifest_path: Path | None = None, repo_root: Path = ROOT, report_dir: Path = REPORT_DIR) -> Path:
    commit, dirty = git_metadata(repo_root)
    if dirty:
        raise RuntimeError("Policy freeze requires a clean Git worktree")
    all_configs = [p for p in (ROOT / "config" / "part7").glob("*.yaml") if p.is_file()]
    score_hash = sha256_file(score_path) if score_path and score_path.exists() else None
    score_status = score_status or selected.get("score_status")
    if score_status not in {"PROBABILITY_USABLE", "RANKING_ONLY"}:
        raise ValueError("score_status must be PROBABILITY_USABLE or RANKING_ONLY")
    if score_status == "PROBABILITY_USABLE" and not calibration_version:
        raise ValueError("Probability-usable scores require calibration_version")
    if score_status == "RANKING_ONLY" and selected.get("priority_method") == "EXPOSURE_WEIGHTED_PROBABILITY":
        raise ValueError("Ranking-only scores cannot use expected-value priority")
    if not confirmation_scope_hash:
        raise ValueError("confirmation_scope_hash is required for an immutable policy freeze")
    if selected_policy_path is None or confirmation_manifest_path is None or not selected_policy_path.exists() or not confirmation_manifest_path.exists():
        raise ValueError("selected policy and confirmation manifest artifacts are required for freeze")
    created_at = utc_now()
    freeze = {"policy_version": selected["policy_version"], "selected_profile": selected["profile"], "priority_method": selected.get("priority_method", "SCORE_ONLY"), "selected_on_scope": "P7_POLICY_CONFIRM", "score_status": score_status, "score_version": score_version, "score_file_sha256": score_hash, "score_row_count": selected.get("score_row_count"), "model_version": model_version, "calibration_version": calibration_version, "graph_version": graph_version or "UNSPECIFIED", "part6_artifact_version": part6_artifact_version or "UNSPECIFIED", "part6_artifact_sha256": part6_artifact_hash, "review_threshold": selected["review_threshold"], "block_threshold": selected["block_threshold"], "review_capacity": selected["review_capacity"], "economic_assumption_sha256": sha256_file(config_paths[0]), "graph_routing_sha256": sha256_file(config_paths[1]), "reason_code_sha256": sha256_file(config_paths[2]), "review_queue_config_sha256": sha256_file(ROOT / "config" / "part7" / "review_queue.yaml"), "action_precedence_sha256": sha256_file(ROOT / "config" / "part7" / "action_precedence.yaml"), "config_bundle_sha256": bundle_hash(all_configs), "code_tree_hash": code_tree_hash(), "selected_policy_sha256": sha256_file(selected_policy_path), "confirmation_manifest_sha256": sha256_file(confirmation_manifest_path), "confirmation_scope_hash": confirmation_scope_hash, "code_commit": commit, "freeze_created_at_utc": created_at, "oot_not_globally_unseen": True, "working_tree_clean": not dirty, "post_freeze_mutation": False}
    freeze["freeze_id"] = "PART7_POLICY_FREEZE_" + hashlib.sha256(json.dumps(freeze, sort_keys=True).encode()).hexdigest()[:12]
    path = report_dir / "PART7_POLICY_FREEZE.json"
    write_json(path, freeze)
    return path
