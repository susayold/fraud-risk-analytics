from __future__ import annotations

import pandas as pd

from .contracts import ACTION_DOMAIN


def monitor_policy(frame: pd.DataFrame, window_id: str = "") -> dict:
    if "action" not in frame:
        return {"window_id": window_id, "status": "BLOCKED", "reason": "Part 7 action evidence unavailable"}
    actions = frame.action.astype(str).str.upper()
    invalid = sorted(set(actions) - ACTION_DOMAIN)
    if invalid:
        return {"window_id": window_id, "status": "FAIL", "reason": f"Invalid actions: {invalid}"}
    versions = frame.policy_version.dropna().astype(str).unique().tolist() if "policy_version" in frame else []
    if len(versions) > 1:
        return {"window_id": window_id, "status": "FAIL", "reason": "Multiple policy versions in one window", "policy_versions": versions}
    counts = actions.value_counts()
    total = len(frame)
    return {"window_id": window_id, "status": "PASS", "policy_version": versions[0] if versions else None, "allow_rate": float(counts.get("ALLOW", 0) / total) if total else None, "review_rate": float(counts.get("REVIEW", 0) / total) if total else None, "block_rate": float(counts.get("BLOCK", 0) / total) if total else None, "action_counts": {key: int(counts.get(key, 0)) for key in sorted(ACTION_DOMAIN)}}

