from __future__ import annotations

import numpy as np
import pandas as pd

from .graph_routing import graph_overlay_priority, load_graph_weights
from .io import ROOT
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


def _priority(frame: pd.DataFrame, method: str, calibrated_probability: bool, graph_weights: dict[str, float] | None) -> pd.Series:
    score = pd.to_numeric(frame.risk_score, errors="raise").astype(float)
    exposure = frame.positive_exposure.astype(float)
    if method == "SCORE_ONLY":
        return score
    if method == "EXPOSURE_WEIGHTED_PROBABILITY":
        if not calibrated_probability:
            raise ValueError("Expected-value priority is disabled for ranking-only scores")
        return score * exposure
    if method == "EXPOSURE_WEIGHTED_RANK":
        return score.rank(method="average", pct=True) * exposure
    if method == "GRAPH_NOVELTY":
        if graph_weights is None:
            raise ValueError("Graph priority requires graph routing weights from config")
        return graph_overlay_priority(frame, score, graph_weights)
    if method == "AMOUNT_GRAPH":
        if graph_weights is None:
            raise ValueError("Graph priority requires graph routing weights from config")
        return graph_overlay_priority(frame, score * exposure, graph_weights)
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
    precedence_config: dict | None = None,
    graph_weights: dict[str, float] | None = None,
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
    result["capacity_bucket"] = time_bucket(result["transaction_timestamp"], config["bucket"].get("type", "DAY"), config["bucket"].get("timezone", "UTC")) if "transaction_timestamp" in result else "LEGACY_SINGLE_BUCKET"
    result["high_amount_cutoff"] = float(high_amount_cutoff) if high_amount_cutoff is not None else float("inf")
    result["candidate_action"] = candidate_actions(result, review_threshold, block_threshold, precedence_config=precedence_config).to_numpy()
    result["action"] = result["candidate_action"]
    eligible = result["candidate_action"].eq("REVIEW")
    if graph_weights is None and priority_method in {"GRAPH_NOVELTY", "AMOUNT_GRAPH"}:
        graph_weights = load_graph_weights(ROOT / "config" / "part7" / "graph_routing_policy.yaml")
    priority = _priority(result.loc[eligible], priority_method, calibrated_probability, graph_weights)
    candidate_columns = ["source_row_id", "risk_score", "positive_exposure", "capacity_bucket"]
    if "transaction_timestamp" in result:
        candidate_columns.append("transaction_timestamp")
    candidates = result.loc[eligible, candidate_columns].copy()
    candidates["review_priority"] = priority
    sort_columns = ["capacity_bucket", "review_priority", "risk_score", "positive_exposure"]
    ascending = [True, False, False, False]
    if "transaction_timestamp" in candidates:
        sort_columns.append("transaction_timestamp")
        ascending.append(True)
    sort_columns.append("source_row_id")
    ascending.append(True)
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

    # Vectorized capacity/rank bookkeeping used by the final run. This preserves
    # the original deterministic ordering while avoiding per-bucket full-frame scans.
    bucket_sizes = result.groupby("capacity_bucket", sort=False).size()
    if capacity_mode == "FIXED_CASES_PER_BUCKET":
        capacity_by_bucket = pd.Series(int(fixed_cases), index=bucket_sizes.index, dtype="int64")
    else:
        capacity_by_bucket = np.floor(
            bucket_sizes.astype(float) * float(capacity_fraction)
        ).clip(lower=0).astype("int64")

    candidates["review_rank"] = candidates.groupby("capacity_bucket", sort=False).cumcount() + 1
    candidates["bucket_capacity"] = candidates["capacity_bucket"].map(capacity_by_bucket).fillna(0).astype(int)
    candidates["bucket_selected"] = candidates["review_rank"] <= candidates["bucket_capacity"]

    result["review_priority"] = np.nan
    result.loc[candidates.index, "review_priority"] = candidates["review_priority"].to_numpy()
    result["review_rank"] = pd.Series(pd.array([pd.NA] * len(result), dtype="Int64"), index=result.index)
    result.loc[candidates.index, "review_rank"] = candidates["review_rank"].astype("Int64").to_numpy()
    result["bucket_capacity"] = result["capacity_bucket"].map(capacity_by_bucket).fillna(0).astype(int)
    result["bucket_selected"] = False
    result.loc[candidates.index, "bucket_selected"] = candidates["bucket_selected"].to_numpy()

    result["overflow"] = eligible & ~result["bucket_selected"]
    result.loc[result["overflow"], "action"] = overflow_action
    result.loc[eligible & result["bucket_selected"], "action"] = "REVIEW"
    result["reason_codes"] = "" if emit_reason_codes else None
    if not emit_reason_codes:
        return result

    def append_code(mask: pd.Series, code: str) -> None:
        current = result.loc[mask, "reason_codes"]
        result.loc[mask, "reason_codes"] = current.where(current.eq(""), current + ";") + code

    append_code(result.candidate_action.eq("BLOCK"), "RC001")
    append_code(result.candidate_action.eq("REVIEW"), "RC002")
    append_code(result["bucket_selected"], "RC010")
    append_code(result["overflow"], str(config["overflow"].get("reason_code", "RC011")))
    if priority_method in {"EXPOSURE_WEIGHTED_PROBABILITY", "EXPOSURE_WEIGHTED_RANK", "AMOUNT_GRAPH"}:
        append_code(result.candidate_action.eq("REVIEW"), "RC003")
    if priority_method in {"GRAPH_NOVELTY", "AMOUNT_GRAPH"}:
        append_code(result.candidate_action.eq("REVIEW"), "RC012")
    return result
