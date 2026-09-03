from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

from .io import sha256_file, utc_now, write_json


def frame_fingerprint(frame: pd.DataFrame, columns: list[str] | None = None) -> str:
    cols = columns or sorted(frame.columns.tolist())
    value = frame.reindex(columns=cols).copy()
    for col in value.columns:
        if pd.api.types.is_datetime64_any_dtype(value[col]):
            value[col] = value[col].astype("string")
    payload = value.sort_values(by=cols, kind="mergesort", na_position="first").to_json(orient="records", date_format="iso", default_handler=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def write_input_lineage(path: Path, score_path: Path, frame: pd.DataFrame, model_version: str = "", score_version: str = "", calibration_version: str = "") -> None:
    def value(field: str, supplied: str = "") -> str:
        if supplied:
            return supplied
        if field in frame and frame[field].notna().any():
            return str(frame[field].dropna().astype(str).iloc[0])
        return "NOT_AVAILABLE"
    lineage = {"model_version": value("model_version", model_version), "score_version": value("score_version", score_version), "score_status": value("score_status"), "calibration_version": value("calibration_version", calibration_version), "policy_version": value("policy_version"), "graph_version": value("graph_version"), "part5_score_hash": value("part5_score_hash"), "part7_policy_freeze_hash": value("part7_policy_freeze_hash"), "part7_decision_mart_hash": value("part7_decision_mart_hash")}
    write_json(path, {"input_path_name": score_path.name, "input_hash": sha256_file(score_path) if score_path.exists() else "MISSING", "row_count": len(frame), "source_row_id_count": int(frame.source_row_id.nunique()) if "source_row_id" in frame else 0, "frame_fingerprint": frame_fingerprint(frame) if not frame.empty else "EMPTY", **lineage, "generated_at_utc": utc_now(), "raw_rows_persisted": False})
