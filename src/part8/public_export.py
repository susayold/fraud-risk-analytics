from __future__ import annotations

from pathlib import Path

import pandas as pd

from .contracts import ensure_public_safe
from .io import write_csv, write_json


def export_aggregate(frame: pd.DataFrame, path: Path) -> None:
    ensure_public_safe(list(frame.columns))
    write_csv(path, frame)


def export_summary(summary: dict, path: Path) -> None:
    # Summary is already aggregate-only by contract; reject accidental row data.
    forbidden_tokens = ("source_row_id", "fraud_label", "risk_score", "transaction_timestamp")
    text = str(summary).lower()
    if any(token in text for token in forbidden_tokens):
        raise ValueError("Public summary contains a forbidden row-level token")
    write_json(path, summary)

