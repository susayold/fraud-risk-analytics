from __future__ import annotations

from pathlib import Path

import hashlib

from .io import REPORT_DIR, ROOT, sha256_file, utc_now, write_json, git_metadata


def _bundle_hash(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.relative_to(ROOT).as_posix().encode())
        digest.update(sha256_file(path).encode())
    return digest.hexdigest()


def _code_tree_hash() -> str:
    return _bundle_hash([p for p in (ROOT / "src" / "part7").rglob("*.py") if "__pycache__" not in p.parts])


def freeze_policy(selected: dict, config_paths: list[Path], score_version: str, model_version: str, calibration_version: str | None, *, score_path: Path | None = None, graph_version: str | None = None, part6_artifact_version: str | None = None, part6_artifact_hash: str | None = None, confirmation_scope_hash: str | None = None) -> Path:
    commit, dirty = git_metadata()
    if dirty:
        raise RuntimeError("Policy freeze requires a clean Git worktree")
    all_configs = [p for p in (ROOT / "config" / "part7").glob("*.yaml") if p.is_file()]
    score_hash = sha256_file(score_path) if score_path and score_path.exists() else None
    freeze = {"policy_version": selected["policy_version"], "selected_profile": selected["profile"], "priority_method": selected.get("priority_method", "SCORE_ONLY"), "selected_on_scope": "P7_POLICY_CONFIRM", "score_version": score_version, "score_file_sha256": score_hash, "score_row_count": selected.get("score_row_count"), "model_version": model_version, "calibration_version": calibration_version, "graph_version": graph_version or "UNSPECIFIED", "part6_artifact_version": part6_artifact_version or "UNSPECIFIED", "part6_artifact_sha256": part6_artifact_hash, "review_threshold": selected["review_threshold"], "block_threshold": selected["block_threshold"], "review_capacity": selected["review_capacity"], "economic_assumption_sha256": sha256_file(config_paths[0]), "graph_routing_sha256": sha256_file(config_paths[1]), "reason_code_sha256": sha256_file(config_paths[2]), "review_queue_config_sha256": sha256_file(ROOT / "config" / "part7" / "review_queue.yaml"), "action_precedence_sha256": sha256_file(ROOT / "config" / "part7" / "action_precedence.yaml"), "config_bundle_sha256": _bundle_hash(all_configs), "code_tree_hash": _code_tree_hash(), "confirmation_scope_hash": confirmation_scope_hash, "code_commit": commit, "freeze_created_at_utc": utc_now(), "oot_not_globally_unseen": True, "working_tree_clean": not dirty, "post_freeze_mutation": False}
    path = REPORT_DIR / "PART7_POLICY_FREEZE.json"
    write_json(path, freeze)
    return path
