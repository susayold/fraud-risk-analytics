from __future__ import annotations

import numpy as np
import pandas as pd

from .drift_metrics import frozen_bins, jensen_shannon, normalized_wasserstein, psi


def score_summary(frame: pd.DataFrame, score_col: str = "risk_score", review_threshold: float | None = None, block_threshold: float | None = None) -> dict:
    scores = pd.to_numeric(frame[score_col], errors="coerce")
    result = {"score_status": frame.get("score_status", pd.Series([None])).iloc[0] if len(frame) else None, "n": int(scores.notna().sum()), "mean": float(scores.mean()), "median": float(scores.median()), "std": float(scores.std(ddof=0)), "p50": float(scores.quantile(.50)), "p75": float(scores.quantile(.75)), "p90": float(scores.quantile(.90)), "p95": float(scores.quantile(.95)), "p99": float(scores.quantile(.99))}
    result["share_above_review_threshold"] = float((scores >= review_threshold).mean()) if review_threshold is not None else None
    result["share_above_block_threshold"] = float((scores >= block_threshold).mean()) if block_threshold is not None else None
    return result


def monitor_score(reference: pd.Series, current: pd.Series, window_id: str = "", score_status: str = "RANKING_ONLY") -> pd.DataFrame:
    bins = frozen_bins(reference)
    return pd.DataFrame([{"window_id": window_id, "metric": name, "observed": value, "score_status": score_status, "claim_class": "EARLY_WARNING"} for name, value in (("score_js", jensen_shannon(reference, current, bins)), ("score_psi", psi(reference, current, bins)), ("score_wasserstein", normalized_wasserstein(reference, current)))])

