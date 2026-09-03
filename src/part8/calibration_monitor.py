from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, log_loss


def evaluate_calibration(frame: pd.DataFrame, score_col: str = "risk_score", label_col: str = "fraud_label", score_status: str = "RANKING_ONLY", bins: int = 10) -> dict:
    if score_status == "RANKING_ONLY":
        return {"status": "NOT_APPLICABLE", "score_status": score_status, "brier": None, "log_loss": None, "ece": None, "support": int(len(frame))}
    if score_status != "PROBABILITY_USABLE":
        raise ValueError(f"Unknown score status: {score_status}")
    if label_col not in frame:
        raise ValueError("Calibration requires matured fraud_label")
    labels = pd.to_numeric(frame[label_col], errors="coerce")
    scores = pd.to_numeric(frame[score_col], errors="coerce").clip(0, 1)
    valid = labels.notna() & scores.notna()
    labels, scores = labels[valid].astype(int), scores[valid]
    if len(labels) == 0:
        return {"status": "INSUFFICIENT_SUPPORT", "score_status": score_status, "brier": None, "log_loss": None, "ece": None, "support": 0}
    edges = np.linspace(0, 1, bins + 1)
    ece = 0.0
    reliability = []
    for left, right in zip(edges[:-1], edges[1:]):
        mask = (scores >= left) & ((scores < right) if right < 1 else (scores <= right))
        if mask.any():
            gap = abs(float(scores[mask].mean()) - float(labels[mask].mean()))
            ece += float(mask.mean()) * gap
            reliability.append({"bin_left": left, "bin_right": right, "count": int(mask.sum()), "mean_score": float(scores[mask].mean()), "observed_rate": float(labels[mask].mean())})
    return {"status": "PASS", "score_status": score_status, "brier": float(brier_score_loss(labels, scores)), "log_loss": float(log_loss(labels, scores, labels=[0, 1])), "ece": float(ece), "support": int(len(labels)), "reliability_bins": reliability}

