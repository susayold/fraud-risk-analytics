"""Immutable verification contract for a frozen Part 7 replay."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .io import ROOT, sha256_file, git_metadata, write_json, REPORT_DIR


def config_map() -> dict[str, Path]:
    base = ROOT / "config" / "part7"
    return {
        "economic_assumption_sha256": base / "economic_assumptions.yaml",
        "graph_routing_sha256": base / "graph_routing_policy.yaml",
        "reason_code_sha256": base / "reason_codes.yaml",
        "review_queue_config_sha256": base / "review_queue.yaml",
        "action_precedence_sha256": base / "action_precedence.yaml",
    }


def bundle_hash(paths: list[Path] | None = None) -> str:
    paths = paths or sorted((ROOT / "config" / "part7").glob("*.yaml"))
    digest = hashlib.sha256()
    for item in sorted(paths):
        digest.update(item.relative_to(ROOT).as_posix().encode())
        digest.update(sha256_file(item).encode())
    return digest.hexdigest()


def code_tree_hash() -> str:
    return bundle_hash([p for p in (ROOT / "src" / "part7").rglob("*.py") if "__pycache__" not in p.parts])


def verify_freeze(path: Path, *, score_path: Path | None = None, part6_artifact_path: Path | None = None, selected_policy_path: Path | None = None, confirmation_manifest_path: Path | None = None, write_report: bool = True) -> tuple[dict, dict]:
    freeze = json.loads(path.read_text(encoding="utf-8"))
    checks: dict[str, object] = {"freeze_id": freeze.get("freeze_id"), "post_freeze_mutation": freeze.get("post_freeze_mutation")}
    for key, expected_path in config_map().items():
        if not freeze.get(key):
            raise RuntimeError(f"Frozen field {key} is missing")
        observed = sha256_file(expected_path)
        checks[key.replace("_sha256", "_hash_match")] = observed == freeze[key]
        if observed != freeze[key]:
            raise RuntimeError(f"Frozen config hash mismatch: {key}")
    if freeze.get("config_bundle_sha256") != bundle_hash():
        raise RuntimeError("Frozen config bundle hash mismatch")
    checks["config_bundle_match"] = True
    if freeze.get("code_tree_hash") != code_tree_hash():
        raise RuntimeError("Frozen code tree hash mismatch")
    checks["code_tree_match"] = True
    current_commit, _ = git_metadata()
    if freeze.get("code_commit") not in {current_commit, "UNKNOWN"}:
        raise RuntimeError("Final replay code commit does not match the policy freeze")
    checks["commit_match"] = True
    score_status = freeze.get("score_status")
    if not freeze.get("score_version") or not freeze.get("model_version") or score_status not in {"PROBABILITY_USABLE", "RANKING_ONLY"}:
        raise RuntimeError("Frozen score/model/calibration versions are incomplete")
    if score_status == "PROBABILITY_USABLE" and not freeze.get("calibration_version"):
        raise RuntimeError("Probability-usable scores require calibration_version")
    if score_status == "RANKING_ONLY" and freeze.get("priority_method") == "EXPOSURE_WEIGHTED_PROBABILITY":
        raise RuntimeError("Ranking-only scores cannot use expected-value priority")
    checks["score_status_valid"] = True
    checks["calibration_requirement_pass"] = True
    if score_path is not None:
        if not freeze.get("score_file_sha256") or sha256_file(score_path) != freeze["score_file_sha256"]:
            raise RuntimeError("Frozen score hash mismatch")
        checks["score_hash_match"] = True
    else:
        checks["score_hash_match"] = False
    selected_path = selected_policy_path or (REPORT_DIR / "PART7_SELECTED_POLICY.json")
    if not freeze.get("selected_policy_sha256") or not selected_path.exists() or sha256_file(selected_path) != freeze["selected_policy_sha256"]:
        raise RuntimeError("Frozen selected-policy artifact hash mismatch or missing")
    checks["selected_policy_hash_match"] = True
    if freeze.get("part6_artifact_sha256"):
        if part6_artifact_path is None or sha256_file(part6_artifact_path) != freeze["part6_artifact_sha256"]:
            raise RuntimeError("Frozen Part 6 graph artifact hash mismatch")
        checks["graph_artifact_hash_match"] = True
    else:
        checks["graph_artifact_hash_match"] = None
    if not freeze.get("confirmation_scope_hash"):
        raise RuntimeError("Frozen confirmation_scope_hash is missing")
    manifest_path = confirmation_manifest_path or (REPORT_DIR / "P7_CONFIRMATION_SCOPE_MANIFEST.json")
    if not manifest_path.exists() or sha256_file(manifest_path) != freeze.get("confirmation_manifest_sha256"):
        raise RuntimeError("Confirmation manifest hash mismatch or missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("confirmation_scope_hash") != freeze.get("confirmation_scope_hash"):
        raise RuntimeError("Confirmation scope hash does not match committed manifest")
    checks["confirmation_scope_hash_match"] = True
    if freeze.get("working_tree_clean") is not True:
        raise RuntimeError("Freeze was not created from a clean worktree")
    if freeze.get("post_freeze_mutation") is not False:
        raise RuntimeError("Post-freeze mutation is not explicitly false")
    checks["working_tree_clean"] = True
    checks["post_freeze_mutation"] = False
    checks["status"] = "PASS"
    if write_report:
        write_json(REPORT_DIR / "PART7_REPLAY_VERIFICATION.json", checks)
    return freeze, checks
