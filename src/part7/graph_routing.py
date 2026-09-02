from __future__ import annotations

import pandas as pd


GRAPH_FIELDS = ("pair_new", "cold_card", "new_merchant", "cross_community")


def graph_overlay_priority(frame: pd.DataFrame, base_priority: pd.Series, weights: dict[str, float] | None = None) -> pd.Series:
    """Apply only to REVIEW priority; never to BLOCK eligibility."""
    weights = weights or {"pair_new": 1.10, "cold_card": 1.08, "new_merchant": 1.08, "cross_community": 1.06}
    factor = pd.Series(1.0, index=frame.index, dtype=float)
    for field, weight in weights.items():
        if field in frame:
            factor = factor.where(~frame[field].fillna(False).astype(bool), factor * float(weight))
    return base_priority * factor
