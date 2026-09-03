from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score, roc_curve


def evaluate_performance(frame: pd.DataFrame, score_col: str = "risk_score", label_col: str = "fraud_label", min_fraud_support: int = 30, top_k_rates: tuple[float, ...] = (.005, .01, .02, .05, .10)) -> dict:
    if label_col not in frame:
        raise ValueError("Outcome performance requires matured fraud_label")
    labels = pd.to_numeric(frame[label_col], errors="coerce")
    scores = pd.to_numeric(frame[score_col], errors="coerce")
    valid = labels.notna() & scores.notna()
    labels, scores = labels[valid].astype(int), scores[valid]
    fraud_support = int(labels.sum())
    result = {"label_mode": "RETROSPECTIVE_MATURED", "support": int(len(labels)), "fraud_support": fraud_support}
    if fraud_support < min_fraud_support or labels.nunique() < 2:
        result.update({"status": "INSUFFICIENT_SUPPORT", "pr_auc": None, "roc_auc": None, "ks": None, "prevalence": float(labels.mean()) if len(labels) else None})
        return result
    result.update({"status": "PASS", "pr_auc": float(average_precision_score(labels, scores)), "roc_auc": float(roc_auc_score(labels, scores)), "prevalence": float(labels.mean())})
    fpr, tpr, _ = roc_curve(labels, scores)
    result["ks"] = float(np.max(tpr - fpr))
    ordered = np.argsort(-scores.to_numpy(), kind="mergesort")
    for rate in top_k_rates:
        count = max(1, int(np.ceil(len(labels) * rate)))
        result[f"top_{rate:.3f}_capture"] = float(labels.iloc[ordered[:count]].sum() / fraud_support)
    return result


def performance_table(frame: pd.DataFrame, window_col: str = "performance_window_id", **kwargs) -> pd.DataFrame:
    rows = []
    for window_id, group in frame.groupby(window_col, sort=True):
        rows.append({"window_id": window_id, **evaluate_performance(group, **kwargs)})
    return pd.DataFrame(rows)

