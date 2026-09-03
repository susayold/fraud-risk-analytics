from __future__ import annotations

import numpy as np
import pandas as pd

from .drift_metrics import frozen_bins, jensen_shannon, jensen_shannon_counts, ks_statistic, normalized_wasserstein, psi, psi_counts


def build_reference(frame: pd.DataFrame, features: list[str], bins: int = 10) -> dict:
    refs = {"numerical": {}, "categorical": {}, "feature_names": features}
    for feature in features:
        if feature not in frame:
            continue
        if pd.api.types.is_numeric_dtype(frame[feature]):
            values = pd.to_numeric(frame[feature], errors="coerce")
            edges = frozen_bins(values, bins=bins)
            refs["numerical"][feature] = {"bins": edges.tolist(), "reference_n": int(values.notna().sum()), "missing_rate": float(values.isna().mean())}
        else:
            values = frame[feature].astype("string").fillna("__NULL__")
            counts = values.value_counts(dropna=False)
            refs["categorical"][feature] = {"categories": [str(x) for x in counts.index.tolist()], "counts": {str(k): int(v) for k, v in counts.items()}, "reference_n": int(len(values))}
    return refs


def monitor_features(reference: pd.DataFrame, current: pd.DataFrame, reference_spec: dict, window_id: str = "") -> pd.DataFrame:
    rows = []
    for feature, spec in reference_spec.get("numerical", {}).items():
        if feature not in current or feature not in reference: continue
        ref, cur = pd.to_numeric(reference[feature], errors="coerce"), pd.to_numeric(current[feature], errors="coerce")
        bins = np.asarray(spec["bins"], dtype=float)
        rows.extend([
            {"window_id": window_id, "feature_name": feature, "feature_type": "numerical", "reference_n": int(ref.notna().sum()), "current_n": int(cur.notna().sum()), "missing_rate_reference": float(ref.isna().mean()), "missing_rate_current": float(cur.isna().mean()), "metric_name": name, "metric_value": value}
            for name, value in (("jensen_shannon", jensen_shannon(ref, cur, bins)), ("wasserstein", normalized_wasserstein(ref, cur)), ("psi", psi(ref, cur, bins)), ("ks", ks_statistic(ref, cur)))
        ])
    for feature, spec in reference_spec.get("categorical", {}).items():
        if feature not in current or feature not in reference: continue
        categories = [str(x) for x in spec["categories"]]
        ref_counts = reference[feature].astype("string").fillna("__NULL__").value_counts().reindex(categories, fill_value=0).to_numpy()
        cur_counts = current[feature].astype("string").fillna("__NULL__").value_counts().reindex(categories, fill_value=0).to_numpy()
        rows.extend([
            {"window_id": window_id, "feature_name": feature, "feature_type": "categorical", "reference_n": int(ref_counts.sum()), "current_n": int(cur_counts.sum()), "missing_rate_reference": float(reference[feature].isna().mean()), "missing_rate_current": float(current[feature].isna().mean()), "metric_name": name, "metric_value": value}
            for name, value in (("jensen_shannon", jensen_shannon_counts(ref_counts, cur_counts)), ("psi", psi_counts(ref_counts, cur_counts)))
        ])
    return pd.DataFrame(rows)
