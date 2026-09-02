"""Aggregate-only diagnostics for the causal review queue."""
from __future__ import annotations

import pandas as pd


def queue_diagnostics(actions: pd.DataFrame) -> dict[str, pd.DataFrame]:
    required = {"capacity_bucket", "candidate_action", "action", "bucket_capacity", "bucket_selected"}
    missing = sorted(required - set(actions.columns))
    if missing:
        raise ValueError(f"Queue diagnostics missing: {missing}")
    grouped = []
    overflow = []
    sla = []
    for bucket, group in actions.groupby("capacity_bucket", sort=True):
        candidates = int(group.candidate_action.eq("REVIEW").sum())
        selected = int(group.bucket_selected.sum())
        cap = int(group.bucket_capacity.iloc[0])
        over = max(candidates - cap, 0)
        grouped.append({"capacity_bucket": str(bucket), "candidate_review_count": candidates,
                        "selected_review_count": selected, "bucket_capacity": cap,
                        "queue_utilization": float(selected / cap) if cap else 0.0,
                        "overflow_count": over, "overflow_rate": float(over / candidates) if candidates else 0.0})
        overflow.append({"capacity_bucket": str(bucket), "candidate_review_count": candidates,
                         "overflow_count": over, "overflow_rate": float(over / candidates) if candidates else 0.0,
                         "overflow_action": "ALLOW"})
        sla.append({"capacity_bucket": str(bucket), "selected_review_count": selected,
                    "capacity_proxy_met": bool(selected <= cap),
                    "sla_proxy": "CAPACITY_ONLY_NOT_REAL_SLA"})
    return {"review_capacity_by_day": pd.DataFrame(grouped),
            "review_overflow_by_day": pd.DataFrame(overflow),
            "review_queue_utilization": pd.DataFrame(grouped),
            "review_queue_sla_proxy": pd.DataFrame(sla)}
