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


def monitor_categories_from_frozen_reference(current: pd.DataFrame, spec: dict, window_id: str = "") -> pd.DataFrame:
    """Category novelty using frozen counts/categories; no pre-OOT rows are read."""
    feature = spec["feature_name"]
    if feature not in current:
        return pd.DataFrame()
    known = [str(x) for x in spec.get("categories", [])]
    current_values = current[feature].astype("string").fillna("__NULL__")
    current_counts = current_values.value_counts(dropna=False)
    current_n = len(current_values)
    reference_n = int(spec.get("reference_n", 0))
    reference_counts = {str(k): int(v) for k, v in (spec.get("reference_counts") or {}).items()}
    categories = sorted(set(known) | set(current_counts.index.astype(str)))
    return pd.DataFrame([{
        "window_id": window_id,
        "feature_name": feature,
        "category": category,
        "reference_share": float(reference_counts.get(category, 0) / reference_n) if reference_n else None,
        "current_share": float(current_counts.get(category, 0) / current_n) if current_n else None,
        "share_delta": (float(current_counts.get(category, 0) / current_n) - float(reference_counts.get(category, 0) / reference_n)) if current_n and reference_n else None,
        "is_new_category": category not in known,
        "is_unknown_category": category not in known,
        "reference_source": "FROZEN_CATEGORICAL_SUFFICIENT_STATISTICS",
    } for category in categories])
