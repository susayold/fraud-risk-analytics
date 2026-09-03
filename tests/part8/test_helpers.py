from __future__ import annotations

import pandas as pd


def fixture_frame(n: int = 120, include_labels: bool = True) -> pd.DataFrame:
    timestamps = pd.date_range("2026-01-01", periods=n, freq="h", tz="UTC")
    frame = pd.DataFrame({
        "source_row_id": [f"row-{i}" for i in range(n)],
        "transaction_timestamp": timestamps,
        "amount": [10 + (i % 7) * 20 for i in range(n)],
        "positive_exposure": [10 + (i % 7) * 20 for i in range(n)],
        "risk_score": [(i % 100) / 100 for i in range(n)],
        "split_name": ["VALIDATION" if i < 80 else "FINAL_OOT" for i in range(n)],
        "channel": ["Online" if i % 3 else "Chip" for i in range(n)],
        "MCC": [str(100 + (i % 4)) for i in range(n)],
        "pair_new": [i % 5 == 0 for i in range(n)],
        "cold_card": [i % 7 == 0 for i in range(n)],
        "new_merchant": [i % 6 == 0 for i in range(n)],
        "cross_community": [i % 8 == 0 for i in range(n)],
        "graph_version": ["G1"] * n,
        "action": ["ALLOW", "REVIEW", "BLOCK"][0:] if False else ["ALLOW" if i % 3 else "REVIEW" if i % 5 else "BLOCK" for i in range(n)],
        "policy_version": ["P7_V1"] * n,
    })
    if include_labels:
        frame["fraud_label"] = [(i % 17 == 0) for i in range(n)]
    return frame

