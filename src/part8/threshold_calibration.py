from __future__ import annotations

import pandas as pd

from .drift_metrics import frozen_bins, histogram_counts, jensen_shannon_counts, psi_counts


def calibrate_threshold_candidates(frame: pd.DataFrame, score_col: str = "risk_score") -> dict:
    """Produce reviewable pre-OOT candidates only; never freezes final values."""
    split = frame.get("split_name", pd.Series("UNKNOWN", index=frame.index)).astype(str).str.upper()
    pre_oot = frame[~split.isin({"FINAL_OOT", "OOT", "OUT_OF_TIME_OOT"})].copy()
    if score_col not in pre_oot or len(pre_oot) < 20:
        return {"status": "INSUFFICIENT_SUPPORT", "source_scope": "PRE_OOT_ONLY", "oot_rows_used": 0, "candidates": {}}
    values = pd.to_numeric(pre_oot[score_col], errors="coerce").dropna()
    if len(values) < 20:
        return {"status": "INSUFFICIENT_SUPPORT", "source_scope": "PRE_OOT_ONLY", "oot_rows_used": 0, "candidates": {}}
    bins = frozen_bins(values)
    groups = []
    if "operational_window_id" in pre_oot:
        groups = [pd.to_numeric(group[score_col], errors="coerce").dropna() for _, group in pre_oot.groupby("operational_window_id")]
    groups = [group for group in groups if len(group) >= 5]
    if len(groups) < 3:
        return {"status": "CANDIDATES_READY_LOW_SUPPORT", "source_scope": "PRE_OOT_ONLY", "oot_rows_used": 0, "candidate_support": len(groups), "candidates": {"score_js": None, "score_psi": None, "channel_share": None}}
    js_values, psi_values = [], []
    reference_counts = histogram_counts(values, bins)
    for group in groups:
        current_counts = histogram_counts(group, bins)
        js_values.append(jensen_shannon_counts(reference_counts, current_counts))
        psi_values.append(psi_counts(reference_counts, current_counts))
    return {"status": "CANDIDATES_READY", "source_scope": "PRE_OOT_ONLY", "oot_rows_used": 0, "candidate_support": len(groups), "candidates": {"score_js": {"candidate_amber": float(pd.Series(js_values).quantile(.95)), "candidate_red": float(pd.Series(js_values).quantile(.99)), "method": "pre-OOT historical window quantiles"}, "score_psi": {"candidate_amber": float(pd.Series(psi_values).quantile(.95)), "candidate_red": float(pd.Series(psi_values).quantile(.99)), "method": "pre-OOT historical window quantiles"}, "channel_share": {"candidate_amber": None, "candidate_red": None, "method": "requires pre-OOT policy channel history"}}}
