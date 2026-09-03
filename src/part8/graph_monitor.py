from __future__ import annotations

import pandas as pd


def monitor_graph(frame: pd.DataFrame, window_id: str = "") -> dict:
    total = len(frame)
    def rate(column: str) -> float | None:
        return float(pd.Series(frame.get(column, False), index=frame.index).fillna(False).astype(bool).mean()) if total else None
    graph_version = frame.graph_version.dropna().astype(str).unique().tolist() if "graph_version" in frame else []
    auto_block = bool(frame.get("graph_auto_block", pd.Series(False, index=frame.index)).fillna(False).astype(bool).any())
    return {"window_id": window_id, "status": "FAIL" if auto_block else "PASS", "graph_version": graph_version[0] if len(graph_version) == 1 else (None if not graph_version else "MIXED"), "pair_new_rate": rate("pair_new"), "cold_card_rate": rate("cold_card"), "new_merchant_rate": rate("new_merchant"), "cross_community_rate": rate("cross_community"), "graph_signal_missing_rate": float(frame.get("graph_version", pd.Series(index=frame.index)).isna().mean()) if total else None, "graph_auto_block": auto_block, "graph_governance": "context_and_priority_only"}

