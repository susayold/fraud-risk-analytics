from __future__ import annotations

import pandas as pd


def _value(row: pd.Series, key: str, default=None):
    return row.get(key, default) if hasattr(row, "get") else getattr(row, key, default)


def reason_codes(row: pd.Series, candidate_action: str, priority_method: str, selected: bool, overflow: bool) -> tuple[str, ...]:
    codes: list[str] = []
    if candidate_action == "BLOCK":
        codes.append("RC001")
    elif candidate_action == "REVIEW":
        codes.append("RC002")
    if priority_method in {"EXPOSURE_WEIGHTED_PROBABILITY", "EXPOSURE_WEIGHTED_RANK", "AMOUNT_GRAPH"}:
        codes.append("RC003")
    if bool(_value(row, "pair_new", False)):
        codes.append("RC004")
    if bool(_value(row, "cold_card", False)):
        codes.append("RC005")
    if bool(_value(row, "new_merchant", False)):
        codes.append("RC006")
    if bool(_value(row, "cross_community", False)):
        codes.append("RC007")
    if str(_value(row, "channel", "")).upper() == "ONLINE":
        codes.append("RC008")
    if float(_value(row, "positive_exposure", 0.0)) >= float(_value(row, "high_amount_cutoff", float("inf"))):
        codes.append("RC009")
    if selected:
        codes.append("RC010")
    if overflow:
        codes.append("RC011")
    if priority_method in {"GRAPH_NOVELTY", "AMOUNT_GRAPH"} and candidate_action == "REVIEW":
        codes.append("RC012")
    return tuple(dict.fromkeys(codes))
