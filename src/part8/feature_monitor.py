from __future__ import annotations

import numpy as np
import pandas as pd

from .drift_metrics import frozen_bins, histogram_counts, jensen_shannon, jensen_shannon_counts, ks_statistic, normalized_wasserstein, psi, psi_counts


def build_reference(frame: pd.DataFrame, features: list[str], bins: int = 10) -> dict:
    refs = {"numerical": {}, "categorical": {}, "feature_names": features}
    for feature in features:
        if feature not in frame:
            continue
        if pd.api.types.is_numeric_dtype(frame[feature]) and not pd.api.types.is_bool_dtype(frame[feature]):
            values = pd.to_numeric(frame[feature], errors="coerce")
            edges = frozen_bins(values, bins=bins)
            refs["numerical"][feature] = {"feature_name": feature, "feature_type": "numerical", "bin_edges": edges.tolist(), "reference_bin_counts": histogram_counts(values, edges).astype(int).tolist(), "reference_n": int(values.notna().sum()), "reference_missing_n": int(values.isna().sum()), "reference_missing_rate": float(values.isna().mean()), "reference_mean": float(values.mean()), "reference_std": float(values.std(ddof=0)), "reference_quantiles": {str(q): float(values.quantile(q)) for q in (.01, .05, .25, .50, .75, .95, .99)}}
        else:
            values = frame[feature].astype("string").fillna("__NULL__")
            counts = values.value_counts(dropna=False)
            refs["categorical"][feature] = {"feature_name": feature, "feature_type": "categorical", "categories": [str(x) for x in counts.index.tolist()], "reference_counts": {str(k): int(v) for k, v in counts.items()}, "reference_n": int(len(values)), "reference_missing_n": int(frame[feature].isna().sum()), "reference_missing_rate": float(frame[feature].isna().mean()), "unknown_category_policy": "NOVELTY_BUCKET"}
    return refs


def monitor_features_from_frozen_reference(current: pd.DataFrame, frozen_reference_spec: dict, window_id: str = "") -> pd.DataFrame:
    """Monitor using only sufficient statistics stored by the baseline."""
    rows = []
    for feature, spec in frozen_reference_spec.get("numerical", {}).items():
        if feature not in current: continue
        cur = pd.to_numeric(current[feature], errors="coerce")
        edges = np.asarray(spec["bin_edges"], dtype=float)
        cur_counts = histogram_counts(cur, edges)
        ref_counts = np.asarray(spec["reference_bin_counts"], dtype=float)
        for name, value in (("jensen_shannon", jensen_shannon_counts(ref_counts, cur_counts)), ("psi", psi_counts(ref_counts, cur_counts))):
            rows.append({"window_id": window_id, "feature_name": feature, "feature_type": "numerical", "reference_n": int(spec["reference_n"]), "current_n": int(cur.notna().sum()), "missing_rate_reference": float(spec["reference_missing_rate"]), "missing_rate_current": float(cur.isna().mean()), "metric_name": name, "metric_value": value, "reference_source": "FROZEN_SUFFICIENT_STATISTICS"})
        ref_q = np.asarray(list(spec.get("reference_quantiles", {}).values()), dtype=float)
        cur_q = np.asarray([cur.quantile(q) for q in (.01, .05, .25, .50, .75, .95, .99)], dtype=float)
        rows.append({"window_id": window_id, "feature_name": feature, "feature_type": "numerical", "reference_n": int(spec["reference_n"]), "current_n": int(cur.notna().sum()), "missing_rate_reference": float(spec["reference_missing_rate"]), "missing_rate_current": float(cur.isna().mean()), "metric_name": "wasserstein", "metric_value": normalized_wasserstein(ref_q, cur_q), "reference_source": "FROZEN_QUANTILE_REPRESENTATION"})
    for feature, spec in frozen_reference_spec.get("categorical", {}).items():
        if feature not in current: continue
        values = current[feature].astype("string").fillna("__NULL__")
        categories = [str(x) for x in spec.get("categories", [])]
        ref_counts = np.asarray([spec.get("reference_counts", {}).get(category, 0) for category in categories], dtype=float)
        cur_counts = values.value_counts().reindex(categories, fill_value=0).to_numpy(dtype=float)
        for name, value in (("jensen_shannon", jensen_shannon_counts(ref_counts, cur_counts)), ("psi", psi_counts(ref_counts, cur_counts))):
            rows.append({"window_id": window_id, "feature_name": feature, "feature_type": "categorical", "reference_n": int(spec["reference_n"]), "current_n": int(len(values)), "missing_rate_reference": float(spec["reference_missing_rate"]), "missing_rate_current": float(current[feature].isna().mean()), "metric_name": name, "metric_value": value, "reference_source": "FROZEN_SUFFICIENT_STATISTICS"})
    return pd.DataFrame(rows)


def monitor_features(reference: pd.DataFrame, current: pd.DataFrame, reference_spec: dict, window_id: str = "") -> pd.DataFrame:
    rows = []
    for feature, spec in reference_spec.get("numerical", {}).items():
        if feature not in current or feature not in reference: continue
        ref, cur = pd.to_numeric(reference[feature], errors="coerce"), pd.to_numeric(current[feature], errors="coerce")
        bins = np.asarray(spec.get("bin_edges", spec.get("bins", [])), dtype=float)
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
