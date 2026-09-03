from __future__ import annotations

import numpy as np
import pandas as pd

from .drift_metrics import frozen_bins, histogram_counts, jensen_shannon, jensen_shannon_counts, normalized_wasserstein, psi, psi_counts


def score_summary(frame: pd.DataFrame, score_col: str = "risk_score", review_threshold: float | None = None, block_threshold: float | None = None) -> dict:
    scores = pd.to_numeric(frame[score_col], errors="coerce")
    result = {"score_status": frame.get("score_status", pd.Series([None])).iloc[0] if len(frame) else None, "n": int(scores.notna().sum()), "mean": float(scores.mean()), "median": float(scores.median()), "std": float(scores.std(ddof=0)), "p50": float(scores.quantile(.50)), "p75": float(scores.quantile(.75)), "p90": float(scores.quantile(.90)), "p95": float(scores.quantile(.95)), "p99": float(scores.quantile(.99))}
    result["share_above_review_threshold"] = float((scores >= review_threshold).mean()) if review_threshold is not None else None
    result["share_above_block_threshold"] = float((scores >= block_threshold).mean()) if block_threshold is not None else None
    return result


def score_reference_from_series(reference: pd.Series, score_status: str = "RANKING_ONLY", review_threshold=None, block_threshold=None) -> dict:
    bins = frozen_bins(reference)
    values = pd.to_numeric(reference, errors="coerce")
    return {"score_status": score_status, "bin_edges": bins.tolist(), "bin_counts": histogram_counts(values, bins).astype(int).tolist(), "n": int(values.notna().sum()), "missing_n": int(values.isna().sum()), "mean": float(values.mean()), "std": float(values.std(ddof=0)), "quantiles": {str(q): float(values.quantile(q)) for q in (.01, .05, .25, .50, .75, .90, .95, .99)}, "review_threshold": review_threshold, "block_threshold": block_threshold}


def monitor_score_from_frozen_reference(current: pd.Series, frozen_score_reference: dict, window_id: str = "") -> pd.DataFrame:
    values = pd.to_numeric(current, errors="coerce")
    ref_counts = frozen_score_reference.get("bin_counts", [])
    bins = np.asarray(frozen_score_reference.get("bin_edges", []), dtype=float)
    if len(bins) < 2 or not ref_counts:
        raise ValueError("Frozen score reference is incomplete")
    cur_counts = histogram_counts(values, bins)
    return pd.DataFrame([{"window_id": window_id, "metric": name, "observed": value, "score_status": frozen_score_reference.get("score_status", "RANKING_ONLY"), "claim_class": "EARLY_WARNING", "reference_source": "FROZEN_SCORE_SUFFICIENT_STATISTICS"} for name, value in (("score_js", jensen_shannon_counts(ref_counts, cur_counts)), ("score_psi", psi_counts(ref_counts, cur_counts)), ("score_wasserstein", normalized_wasserstein(np.asarray(list(frozen_score_reference.get("quantiles", {}).values()), dtype=float), np.asarray([values.quantile(q) for q in (.01, .05, .25, .50, .75, .90, .95, .99)], dtype=float))))])


def monitor_score(first: pd.Series, second, window_id: str = "", score_status: str = "RANKING_ONLY") -> pd.DataFrame:
    """Compatibility wrapper; final replay uses the frozen-reference API above."""
    if isinstance(second, dict):
        return monitor_score_from_frozen_reference(first, second, window_id)
    bins = frozen_bins(first)
    return pd.DataFrame([{"window_id": window_id, "metric": name, "observed": value, "score_status": score_status, "claim_class": "EARLY_WARNING"} for name, value in (("score_js", jensen_shannon(first, second, bins)), ("score_psi", psi(first, second, bins)), ("score_wasserstein", normalized_wasserstein(first, second)))])
