"""Outcome/economics runtime, physically separated from decisioning."""
from __future__ import annotations

import pandas as pd

from .contracts import FORBIDDEN_POLICY_FIELDS
from .economics import EconomicAssumptions, evaluate_economics


def evaluate_decisions(
    decisions: pd.DataFrame,
    evaluation_labels: pd.DataFrame,
    assumptions: EconomicAssumptions,
    *,
    label_column: str = "fraud_label",
) -> dict:
    """Join labels by source_row_id only after the decision pass completes."""
    if any(field in decisions.columns for field in FORBIDDEN_POLICY_FIELDS):
        raise ValueError("Label firewall: decisions must not contain evaluation fields")
    if "source_row_id" not in decisions or "source_row_id" not in evaluation_labels:
        raise ValueError("source_row_id is required for post-decision evaluation")
    if label_column not in evaluation_labels:
        raise ValueError(f"Evaluation label {label_column!r} is missing")
    if not decisions.source_row_id.is_unique or not evaluation_labels.source_row_id.is_unique:
        raise ValueError("source_row_id must be unique in both decision and evaluation frames")
    labels = evaluation_labels[["source_row_id", label_column]].copy()
    joined = decisions.merge(labels, on="source_row_id", how="left", validate="one_to_one")
    if joined[label_column].isna().any():
        raise ValueError("Evaluation labels do not cover every decision row")
    return evaluate_economics(joined, assumptions, label_column)
