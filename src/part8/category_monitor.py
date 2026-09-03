from __future__ import annotations

import pandas as pd


def category_reference(frame: pd.DataFrame, feature: str, top_n: int = 100) -> dict:
    values = frame[feature].astype("string").fillna("__NULL__")
    counts = values.value_counts()
    known = [str(x) for x in counts.head(top_n).index]
    return {"feature_name": feature, "known_categories": known, "reference_shares": {str(k): float(v / len(values)) for k, v in counts.items()}, "other_policy": "OTHER"}


def monitor_categories(reference: pd.DataFrame, current: pd.DataFrame, spec: dict, window_id: str = "") -> pd.DataFrame:
    feature = spec["feature_name"]
    known = [str(x) for x in spec.get("known_categories", [])]
    ref_values = reference[feature].astype("string").fillna("__NULL__")
    cur_values = current[feature].astype("string").fillna("__NULL__")
    categories = sorted(set(known) | set(cur_values.unique().tolist()))
    rows = []
    for category in categories:
        ref_share = float((ref_values == category).mean())
        cur_share = float((cur_values == category).mean())
        is_new = category not in known
        rows.append({"window_id": window_id, "feature_name": feature, "category": category, "reference_share": ref_share, "current_share": cur_share, "share_delta": cur_share - ref_share, "is_new_category": is_new, "is_unknown_category": is_new})
    return pd.DataFrame(rows)

