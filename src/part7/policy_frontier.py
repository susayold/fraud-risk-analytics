from __future__ import annotations

import pandas as pd


def nondominated(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    keep = []
    for i, row in frame.iterrows():
        better = (frame.simulated_total_cost <= row.simulated_total_cost) & (frame.fraud_capture >= row.fraud_capture) & (frame.legitimate_intervention_rate <= row.legitimate_intervention_rate)
        strictly = (frame.simulated_total_cost < row.simulated_total_cost) | (frame.fraud_capture > row.fraud_capture) | (frame.legitimate_intervention_rate < row.legitimate_intervention_rate)
        keep.append(not bool((better & strictly).any()))
    result = frame.loc[keep].copy()
    result["non_dominated"] = True
    return result


def build_frontier(frame: pd.DataFrame) -> pd.DataFrame:
    front = nondominated(frame)
    if front.empty:
        return pd.DataFrame(columns=["policy_version", "x_metric", "y_metric", "value_x", "value_y", "non_dominated"])
    rows = []
    for _, row in front.iterrows():
        for x, y in (("legitimate_intervention_rate", "fraud_capture"), ("review_rate", "fraud_exposure_capture"), ("simulated_total_cost", "fraud_capture")):
            rows.append({"policy_version": row.policy_version, "x_metric": x, "y_metric": y, "value_x": row[x], "value_y": row[y], "non_dominated": True})
    return pd.DataFrame(rows)
