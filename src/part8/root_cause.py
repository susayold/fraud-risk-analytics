from __future__ import annotations

import pandas as pd


def root_cause_bundle(feature_drift: pd.DataFrame | None = None, category_novelty: pd.DataFrame | None = None, score_shift: pd.DataFrame | None = None, segment_shift: pd.DataFrame | None = None) -> dict:
    def top(frame, column="metric_value"):
        if frame is None or frame.empty: return []
        cols = [c for c in ("feature_name", "category", "metric", column) if c in frame]
        return frame.sort_values(column, ascending=False).head(5)[cols].to_dict("records") if column in frame else frame.head(5).to_dict("records")
    return {"top_drifting_features": top(feature_drift), "top_new_categories": top(category_novelty, "share_delta"), "score_shift": top(score_shift, "observed"), "segments_affected": top(segment_shift, "share_transactions"), "causal_language": "associated with / coincides with / candidate driver; no causal claim"}

