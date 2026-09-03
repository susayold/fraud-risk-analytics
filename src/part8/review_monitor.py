from __future__ import annotations

import pandas as pd


def monitor_review(frame: pd.DataFrame, capacity: int | None = None, window_id: str = "") -> dict:
    total = len(frame)
    action = frame.get("action", pd.Series(index=frame.index, dtype=object)).astype(str).str.upper()
    candidate = frame.get("candidate_action", action).astype(str).str.upper().eq("REVIEW")
    selected = frame.get("review_selected", action.eq("REVIEW")).fillna(False).astype(bool)
    overflow = frame.get("review_overflow", pd.Series(False, index=frame.index)).fillna(False).astype(bool)
    eligible = int(candidate.sum())
    selected_n = int(selected.sum())
    overflow_n = int(overflow.sum())
    if capacity is not None:
        cap = int(capacity)
    elif "bucket_capacity" in frame:
        values = pd.to_numeric(frame.bucket_capacity, errors="coerce").dropna().unique()
        if len(values) != 1:
            return {"window_id": window_id, "status": "FAIL", "reason": "Inconsistent repeated bucket_capacity"}
        cap = int(values[0])
    else:
        cap = 0
    if eligible != selected_n + overflow_n:
        return {"window_id": window_id, "status": "FAIL", "reason": "eligible != selected + overflow", "eligible_cases": eligible, "selected_cases": selected_n, "overflow_cases": overflow_n}
    if cap and selected_n > cap:
        return {"window_id": window_id, "status": "FAIL", "reason": "selected reviews exceed capacity", "capacity": cap, "selected_cases": selected_n}
    return {"window_id": window_id, "status": "PASS", "eligible_cases": eligible, "selected_cases": selected_n, "overflow_cases": overflow_n, "capacity": cap, "capacity_utilization": float(selected_n / cap) if cap else None, "candidate_rate": float(eligible / total) if total else None, "selected_rate": float(selected_n / total) if total else None, "overflow_rate": float(overflow_n / total) if total else None, "mean_review_score": float(pd.to_numeric(frame.loc[selected, "risk_score"], errors="coerce").mean()) if selected.any() and "risk_score" in frame else None, "p90_review_score": float(pd.to_numeric(frame.loc[selected, "risk_score"], errors="coerce").quantile(.90)) if selected.any() and "risk_score" in frame else None, "mean_review_exposure": float(pd.to_numeric(frame.loc[selected, "positive_exposure"], errors="coerce").mean()) if selected.any() and "positive_exposure" in frame else None}


def review_table(frame: pd.DataFrame, window_col: str = "operational_window_id", capacity: int | None = None) -> pd.DataFrame:
    rows = []
    for window_id, group in frame.groupby(window_col, sort=True):
        if capacity is not None or "review_capacity_bucket" not in group:
            rows.append(monitor_review(group, capacity=capacity, window_id=str(window_id)))
            continue
        for bucket, bucket_frame in group.groupby("review_capacity_bucket", sort=True):
            rows.append(monitor_review(bucket_frame, capacity=capacity, window_id=f"{window_id}:{bucket}"))
    return pd.DataFrame(rows)
