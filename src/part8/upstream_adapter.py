from __future__ import annotations

import pandas as pd


CANONICAL_MAP = {
    "bucket_selected": "review_selected",
    "overflow": "review_overflow",
    "capacity_bucket": "review_capacity_bucket",
}


def adapt_part7_decision_mart(frame: pd.DataFrame) -> pd.DataFrame:
    """Map the Part 7 decision mart to the Part 8 monitoring contract.

    Capacity is a bucket-level value. It is never summed across repeated
    row-level records; inconsistent values fail closed.
    """
    result = frame.rename(columns={source: target for source, target in CANONICAL_MAP.items() if source in frame and target not in frame}).copy()
    required = {"candidate_action", "action", "review_selected", "review_overflow"}
    missing = sorted(required - set(result.columns))
    if missing:
        raise ValueError(f"Part 7 decision mart missing adapter columns: {missing}")
    result["action"] = result.action.astype(str).str.upper()
    result["candidate_action"] = result.candidate_action.astype(str).str.upper()
    result["review_selected"] = result.review_selected.fillna(False).astype(bool)
    result["review_overflow"] = result.review_overflow.fillna(False).astype(bool)
    if "bucket_capacity" not in result:
        result["bucket_capacity"] = 0
    bucket_col = "review_capacity_bucket" if "review_capacity_bucket" in result else "operational_window_id"
    result["review_capacity_bucket"] = result.get(bucket_col, pd.Series("DEFAULT", index=result.index)).fillna("DEFAULT").astype(str)
    for bucket, group in result.groupby("review_capacity_bucket", sort=False):
        values = pd.to_numeric(group.bucket_capacity, errors="coerce").dropna().unique()
        if len(values) != 1:
            raise ValueError(f"Inconsistent bucket_capacity in bucket {bucket}")
        capacity = int(values[0])
        eligible = int(group.candidate_action.eq("REVIEW").sum())
        selected = int(group.review_selected.sum())
        overflow = int(group.review_overflow.sum())
        if eligible != selected + overflow:
            raise ValueError(f"Capacity reconciliation failed in bucket {bucket}: eligible={eligible}, selected={selected}, overflow={overflow}")
        if selected > capacity:
            raise ValueError(f"Selected reviews exceed capacity in bucket {bucket}")
    return result


def capacity_reconciliation(frame: pd.DataFrame) -> pd.DataFrame:
    adapted = adapt_part7_decision_mart(frame)
    rows = []
    for bucket, group in adapted.groupby("review_capacity_bucket", sort=True):
        capacity = int(pd.to_numeric(group.bucket_capacity, errors="coerce").iloc[0])
        selected = int(group.review_selected.sum())
        rows.append({"capacity_bucket": bucket, "eligible_cases": int(group.candidate_action.eq("REVIEW").sum()), "selected_cases": selected, "overflow_cases": int(group.review_overflow.sum()), "bucket_capacity": capacity, "capacity_utilization": selected / capacity if capacity else None, "status": "PASS"})
    return pd.DataFrame(rows)

