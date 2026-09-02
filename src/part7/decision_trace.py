"""Schema for the private, row-level decision trace.

The trace is opt-in because materialising it for a 24.4M-row population is a
heavy operation. It is always git-ignored and is never copied to public web
reports.
"""
from __future__ import annotations

import pandas as pd


TRACE_COLUMNS = [
    "source_row_id", "transaction_timestamp", "risk_score", "score_version", "calibration_version",
    "positive_exposure", "pair_new", "cold_card", "new_merchant", "cross_community",
    "candidate_action", "capacity_bucket", "review_priority", "review_rank", "bucket_capacity",
    "bucket_selected", "final_action", "primary_reason_code", "secondary_reason_codes",
    "policy_version", "policy_profile", "priority_method", "model_version", "graph_version",
    "economics_version", "freeze_id", "config_bundle_hash", "code_commit",
]


def build_trace(actions: pd.DataFrame, *, score_version: str, calibration_version: str | None,
                policy_version: str, policy_profile: str, model_version: str,
                graph_version: str, economics_version: str, freeze_id: str,
                config_bundle_hash: str, code_commit: str) -> pd.DataFrame:
    result = actions.copy()
    result["final_action"] = result["action"]
    reasons = result["reason_codes"] if "reason_codes" in result else pd.Series("", index=result.index)
    result["primary_reason_code"] = reasons.fillna("").astype(str).str.split(";").str[0].replace("", pd.NA)
    result["secondary_reason_codes"] = reasons.fillna("").astype(str).str.split(";").str[1:].map(lambda values: ";".join(values))
    for key, value in {"score_version": score_version, "calibration_version": calibration_version,
                       "policy_version": policy_version, "policy_profile": policy_profile,
                       "model_version": model_version, "graph_version": graph_version,
                       "economics_version": economics_version, "freeze_id": freeze_id,
                       "config_bundle_hash": config_bundle_hash, "code_commit": code_commit,
                       "priority_method": result.get("priority_method", "SCORE_ONLY")}.items():
        result[key] = value
    return result.reindex(columns=TRACE_COLUMNS)
