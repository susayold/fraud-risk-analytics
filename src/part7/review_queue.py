from __future__ import annotations

import numpy as np
import pandas as pd

from .graph_routing import graph_overlay_priority
from .reason_codes import reason_codes
from .action_precedence import candidate_actions


DEFAULT_QUEUE_CONFIG = {
    "bucket": {"type": "DAY", "timezone": "UTC"},
    "capacity": {"mode": "FRACTION", "fraction": 0.01, "fixed_cases": None},
    "priority": {"deterministic": True},
    "overflow": {"action": "ALLOW", "reason_code": "RC011"},
    "carryover": {"enabled": False},
}


def _merge_queue_config(queue_config: dict | None) -> dict:
    config = {key: value.copy() if isinstance(value, dict) else value for key, value in DEFAULT_QUEUE_CONFIG.items()}
    for key, value in (queue_config or {}).items():
        if isinstance(value, dict) and isinstance(config.get(key), dict):
            config[key].update(value)
        else:
            config[key] = value
    return config


def time_bucket(timestamps: pd.Series, bucket_type: str = "DAY", timezone: str = "UTC") -> pd.Series:
    """Return deterministic operational buckets without using future rows."""
    parsed = pd.to_datetime(timestamps, errors="raise", utc=True)
    bucket = str(bucket_type).upper()
    if bucket == "DAY":
        return parsed.dt.strftime("%Y-%m-%d")
    if bucket == "SHIFT":
        hour = parsed.dt.hour
        shift = np.select([hour < 8, hour < 16], ["00-08", "08-16"], default="16-24")
        return parsed.dt.strftime("%Y-%m-%d") + "T" + pd.Series(shift, index=parsed.index)
    if bucket == "WEEK":
        return parsed.dt.to_period("W").astype(str)
    if bucket == "HOUR":
        return parsed.dt.strftime("%Y-%m-%dT%H")
    raise ValueError(f"Unsupported review queue bucket: {bucket_type}")


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
        # Average rank is invariant to input row order. The final sort below
        # still supplies the explicit source_row_id tie-break.
        return score.rank(method="average", pct=True) * exposure
    if method == "GRAPH_NOVELTY":
        return graph_overlay_priority(frame, score)
    if method == "AMOUNT_GRAPH":
        return graph_overlay_priority(frame, score * exposure)
    raise ValueError(f"Unknown review priority method: {method}")


def apply_policy(
    frame: pd.DataFrame,
    review_threshold: float,
    block_threshold: float,
    review_capacity: float,
    priority_method: str = "SCORE_ONLY",
    calibrated_probability: bool = False,
    high_amount_cutoff: float | None = None,
    emit_reason_codes: bool = True,
    queue_config: dict | None = None,
) -> pd.DataFrame:
    """Generate actions without reading a label/outcome column."""
    required = {"source_row_id", "risk_score", "positive_exposure"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Policy input missing: {missing}")
    result = frame.copy()
    config = _merge_queue_config(queue_config)
    result["priority_method"] = priority_method
    result["overflow_action"] = str(config["overflow"].get("action", "ALLOW")).upper()
    overflow_action = str(config["overflow"].get("action", "ALLOW")).upper()
    if overflow_action not in {"ALLOW", "REVIEW"}:
        raise ValueError("Review overflow action must be ALLOW or REVIEW")
    if bool(config.get("carryover", {}).get("enabled", False)):
        raise ValueError("Review queue carryover is not supported; use explicit bucket capacity")
    # Legacy callers without timestamps are kept deterministic in one explicit
    # bucket; the governed Part 7 input contract still requires timestamps.
    result["capacity_bucket"] = time_bucket(result["transaction_timestamp"], config["bucket"].get("type", "DAY"), config["bucket"].get("timezone", "UTC")) if "transaction_timestamp" in result else "LEGACY_SINGLE_BUCKET"
    result["high_amount_cutoff"] = float(high_amount_cutoff) if high_amount_cutoff is not None else float("inf")
    result["candidate_action"] = candidate_actions(result, review_threshold, block_threshold).to_numpy()
    result["action"] = result["candidate_action"]
    eligible = result["candidate_action"].eq("REVIEW")
    priority = _priority(result.loc[eligible], priority_method, calibrated_probability)
    candidate_columns = ["source_row_id", "risk_score", "positive_exposure", "capacity_bucket"]
    if "transaction_timestamp" in result:
        candidate_columns.append("transaction_timestamp")
    candidates = result.loc[eligible, candidate_columns].copy()
    candidates["review_priority"] = priority
    sort_columns = ["capacity_bucket", "review_priority", "risk_score", "positive_exposure"]
    ascending = [True, False, False, False]
    if "transaction_timestamp" in candidates:
        sort_columns.append("transaction_timestamp"); ascending.append(True)
    sort_columns.append("source_row_id"); ascending.append(True)
    candidates = candidates.sort_values(sort_columns, ascending=ascending, kind="mergesort")
    capacity_mode = str(config["capacity"].get("mode", "FRACTION")).upper()
    capacity_fraction = float(review_capacity if capacity_mode == "FRACTION" else config["capacity"].get("fraction", review_capacity))
    fixed_cases = config["capacity"].get("fixed_cases")
    if capacity_mode == "FIXED_CASES_PER_BUCKET":
        if fixed_cases is None:
            raise ValueError("fixed_cases is required for FIXED_CASES_PER_BUCKET")
        capacity_fraction = None
    elif not 0 <= capacity_fraction <= 1:
        raise ValueError("review capacity fraction must be within [0, 1]")
    selected_ids: set[int] = set()
    rank_map: dict[int, int] = {}
    bucket_capacity: dict[str, int] = {}
    for bucket, group in candidates.groupby("capacity_bucket", sort=True):
        cap = int(fixed_cases) if capacity_mode == "FIXED_CASES_PER_BUCKET" else int(np.floor(capacity_fraction * len(result.loc[result.capacity_bucket.eq(bucket)])))
        bucket_capacity[str(bucket)] = max(cap, 0)
        selected = group.head(max(cap, 0))
        selected_ids.update(selected.source_row_id.astype(int).tolist())
        rank_map.update({int(row.source_row_id): index for index, (_, row) in enumerate(group.iterrows(), start=1)})
    result["review_priority"] = np.nan
    result.loc[eligible, "review_priority"] = priority
    result["review_rank"] = result.source_row_id.map(rank_map).astype("Int64")
    result["bucket_capacity"] = result.capacity_bucket.map(bucket_capacity).fillna(0).astype(int)
    result["bucket_selected"] = result.source_row_id.isin(selected_ids)
    result["overflow"] = eligible & ~result["bucket_selected"]
    result.loc[result["overflow"], "action"] = overflow_action
    result.loc[eligible & result["bucket_selected"], "action"] = "REVIEW"
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
    append_code(result["overflow"], str(config["overflow"].get("reason_code", "RC011")))
    if priority_method in {"EXPOSURE_WEIGHTED_PROBABILITY", "EXPOSURE_WEIGHTED_RANK", "AMOUNT_GRAPH"}:
        append_code(result.candidate_action.eq("REVIEW"), "RC003")
    if priority_method in {"GRAPH_NOVELTY", "AMOUNT_GRAPH"}:
        append_code(result.candidate_action.eq("REVIEW"), "RC012")
    return result
