from __future__ import annotations

import numpy as np
import pandas as pd

from .graph_routing import graph_overlay_priority
from .reason_codes import reason_codes


def _priority(frame: pd.DataFrame, method: str, calibrated_probability: bool) -> pd.Series:
    score = pd.to_numeric(frame.risk_score, errors="raise").astype(float)
    exposure = frame.positive_exposure.astype(float)
    if method == "SCORE_ONLY":
        return score
    if method == "EXPOSURE_WEIGHTED_PROBABILITY":
        if not calibrated_probability:
            raise ValueError("Expected-value priority is disabled for ranking-only scores")
        return score * exposure
    if method == "EXPOSURE_WEIGHTED_RANK":
        return score.rank(method="first", pct=True) * exposure
    if method == "GRAPH_NOVELTY":
        return graph_overlay_priority(frame, score)
    if method == "AMOUNT_GRAPH":
        return graph_overlay_priority(frame, score * exposure)
    raise ValueError(f"Unknown review priority method: {method}")


def apply_policy(frame: pd.DataFrame, review_threshold: float, block_threshold: float, review_capacity: float, priority_method: str = "SCORE_ONLY", calibrated_probability: bool = False, high_amount_cutoff: float | None = None, emit_reason_codes: bool = True) -> pd.DataFrame:
    """Generate actions without reading a label/outcome column."""
    required = {"source_row_id", "risk_score", "positive_exposure"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Policy input missing: {missing}")
    result = frame.copy()
    result["high_amount_cutoff"] = float(high_amount_cutoff) if high_amount_cutoff is not None else float("inf")
    result["candidate_action"] = np.select([result.risk_score >= block_threshold, result.risk_score >= review_threshold], ["BLOCK", "REVIEW"], default="ALLOW")
    result["action"] = result["candidate_action"]
    eligible = result["candidate_action"].eq("REVIEW")
    capacity_n = int(np.floor(float(review_capacity) * len(result)))
    priority = _priority(result.loc[eligible], priority_method, calibrated_probability)
    candidates = result.loc[eligible, ["source_row_id", "risk_score", "positive_exposure"]].copy()
    candidates["review_priority"] = priority
    candidates = candidates.sort_values(["review_priority", "risk_score", "positive_exposure", "source_row_id"], ascending=[False, False, False, True], kind="mergesort")
    selected_ids = set(candidates.head(capacity_n).source_row_id.tolist())
    result["review_priority"] = np.nan
    result.loc[eligible, "review_priority"] = priority
    result.loc[eligible & result.source_row_id.isin(selected_ids), "action"] = "REVIEW"
    result.loc[eligible & ~result.source_row_id.isin(selected_ids), "action"] = "ALLOW"
    # Keep the decision pass vectorized. Row-level reason strings are private-only and
    # are intentionally not materialized by default on a 24.4M-row population.
    result["reason_codes"] = "" if emit_reason_codes else None
    if not emit_reason_codes:
        return result
    def append_code(mask: pd.Series, code: str) -> None:
        current = result.loc[mask, "reason_codes"]
        result.loc[mask, "reason_codes"] = current.where(current.eq(""), current + ";") + code
    append_code(result.candidate_action.eq("BLOCK"), "RC001")
    append_code(result.candidate_action.eq("REVIEW"), "RC002")
    append_code(result.source_row_id.isin(selected_ids), "RC010")
    append_code(result.candidate_action.eq("REVIEW") & ~result.source_row_id.isin(selected_ids), "RC011")
    if priority_method in {"EXPOSURE_WEIGHTED_PROBABILITY", "EXPOSURE_WEIGHTED_RANK", "AMOUNT_GRAPH"}:
        append_code(result.candidate_action.eq("REVIEW"), "RC003")
    if priority_method in {"GRAPH_NOVELTY", "AMOUNT_GRAPH"}:
        append_code(result.candidate_action.eq("REVIEW"), "RC012")
    return result
