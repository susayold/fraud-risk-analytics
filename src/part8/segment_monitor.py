from __future__ import annotations

import pandas as pd


SEGMENTS = {"channel": "channel", "amount_band": "amount", "MCC": "MCC", "cold_start": "cold_card", "new_card_merchant_pair": "pair_new", "new_merchant": "new_merchant", "policy_action": "action", "risk_band": "risk_band"}


def add_segment_columns(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    if "amount" in result:
        amount = pd.to_numeric(result.amount, errors="coerce")
        result["amount_band"] = pd.cut(amount, [-float("inf"), 25, 100, 500, float("inf")], labels=["LOW", "MEDIUM", "HIGH", "VERY_HIGH"]).astype("string")
    if "risk_band" not in result and "risk_score" in result:
        score = pd.to_numeric(result.risk_score, errors="coerce")
        result["risk_band"] = pd.cut(score, [-float("inf"), .2, .5, .8, float("inf")], labels=["LOW", "MEDIUM", "HIGH", "VERY_HIGH"]).astype("string")
    if "cold_start" not in result and "cold_card" in result:
        result["cold_start"] = result.cold_card.fillna(False).astype(bool)
    return result


def monitor_segments(frame: pd.DataFrame, window_id: str = "") -> pd.DataFrame:
    result = add_segment_columns(frame)
    rows = []
    for segment_type, column in SEGMENTS.items():
        if column not in result: continue
        for value, group in result.groupby(column, dropna=False, sort=True):
            rows.append({"window_id": window_id, "segment_type": segment_type, "segment": str(value), "support": int(len(group)), "share_transactions": float(len(group) / len(result)) if len(result) else None, "share_exposure": float(pd.to_numeric(group.get("positive_exposure", group.get("amount", 0)), errors="coerce").fillna(0).sum() / pd.to_numeric(result.get("positive_exposure", result.get("amount", 0)), errors="coerce").fillna(0).sum()) if len(result) and pd.to_numeric(result.get("positive_exposure", result.get("amount", 0)), errors="coerce").fillna(0).sum() else None})
    return pd.DataFrame(rows)

