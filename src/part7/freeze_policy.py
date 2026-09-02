from __future__ import annotations

from pathlib import Path

from .io import REPORT_DIR, sha256_file, utc_now, write_json, git_metadata


def freeze_policy(selected: dict, config_paths: list[Path], score_version: str, model_version: str, calibration_version: str | None) -> Path:
    commit, dirty = git_metadata()
    if dirty:
        raise RuntimeError("Policy freeze requires a clean Git worktree")
    freeze = {"policy_version": selected["policy_version"], "selected_profile": selected["profile"], "priority_method": selected.get("priority_method", "SCORE_ONLY"), "selected_on_scope": "P7_POLICY_CONFIRM", "score_version": score_version, "model_version": model_version, "calibration_version": calibration_version, "review_threshold": selected["review_threshold"], "block_threshold": selected["block_threshold"], "review_capacity": selected["review_capacity"], "economic_assumption_sha256": sha256_file(config_paths[0]), "graph_routing_sha256": sha256_file(config_paths[1]), "reason_code_sha256": sha256_file(config_paths[2]), "code_commit": commit, "freeze_created_at_utc": utc_now(), "oot_not_globally_unseen": True, "working_tree_clean": not dirty}
    path = REPORT_DIR / "PART7_POLICY_FREEZE.json"
    write_json(path, freeze)
    return path
