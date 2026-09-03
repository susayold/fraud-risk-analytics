from __future__ import annotations

import pandas as pd

from .contracts import FORBIDDEN_OPERATIONAL_FIELDS, MATURED, OPERATIONAL


def build_operational_view(frame: pd.DataFrame) -> pd.DataFrame:
    forbidden = sorted(set(frame.columns) & FORBIDDEN_OPERATIONAL_FIELDS)
    if forbidden:
        raise ValueError(f"Operational monitoring cannot receive outcome fields: {forbidden}")
    return frame.copy()


def build_matured_outcome_view(frame: pd.DataFrame, label_mode: str = "RETROSPECTIVE_MATURED") -> pd.DataFrame:
    if label_mode not in {"RETROSPECTIVE_MATURED", "SIMULATED_DELAY"}:
        raise ValueError(f"Unsupported label mode: {label_mode}")
    if "fraud_label" not in frame:
        raise ValueError("Matured outcome monitoring requires fraud_label")
    result = frame.copy()
    result["label_mode"] = label_mode
    result["label_claim_class"] = "SIMULATED" if label_mode == "SIMULATED_DELAY" else "RETROSPECTIVE_MATURED"
    return result


def assert_label_mode(mode: str, matured: bool) -> None:
    if mode == OPERATIONAL and matured:
        raise ValueError("Operational clock cannot be marked as matured")
    if mode == MATURED and not matured:
        raise ValueError("Matured clock requires outcome evidence")

