from __future__ import annotations

import pandas as pd


def outcome_metrics(frame: pd.DataFrame) -> dict:
    if "fraud_label" not in frame:
        raise ValueError("Outcome metrics require matured labels")
    labels = pd.to_numeric(frame.fraud_label, errors="coerce").fillna(0)
    amount = pd.to_numeric(frame.get("amount", pd.Series(0, index=frame.index)), errors="coerce").fillna(0).clip(lower=0)
    fraud_amount = amount.where(labels.astype(bool), 0)
    return {"label_mode": "RETROSPECTIVE_MATURED", "transactions": int(len(frame)), "fraud_count": int(labels.sum()), "fraud_rate": float(labels.mean()) if len(labels) else None, "fraud_positive_exposure": float(fraud_amount.sum()), "fraud_amount_rate": float(fraud_amount.sum() / amount.sum()) if amount.sum() else None}

