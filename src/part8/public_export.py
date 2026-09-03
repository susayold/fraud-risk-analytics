from __future__ import annotations

from pathlib import Path

import pandas as pd

from .contracts import FORBIDDEN_PUBLIC_FIELDS, ensure_public_safe
from .io import write_csv, write_json


def export_aggregate(frame: pd.DataFrame, path: Path) -> None:
    ensure_public_safe(list(frame.columns))
    write_csv(path, frame)


def export_summary(summary: dict, path: Path) -> None:
    validate_public_payload(summary)
    write_json(path, summary)


def validate_public_payload(value, path: str = "$" ) -> None:
    """Reject forbidden row-level keys recursively while allowing aggregate values/text."""
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in FORBIDDEN_PUBLIC_FIELDS:
                raise ValueError(f"Public summary contains forbidden row-level key at {path}.{key}")
            validate_public_payload(child, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            validate_public_payload(child, f"{path}[{index}]")
