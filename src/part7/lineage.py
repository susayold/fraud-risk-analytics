"""Lineage and immutable scope helpers; never copy raw data into public reports."""
from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

from .io import sha256_file, write_json, utc_now


def frame_fingerprint(frame: pd.DataFrame) -> str:
    ordered = frame.sort_values("source_row_id").copy()
    return hashlib.sha256(pd.util.hash_pandas_object(ordered, index=True).to_numpy().tobytes()).hexdigest()


def write_input_lineage(path: Path, *, score_path: Path, frame: pd.DataFrame, score_version: str, model_version: str, calibration_version: str | None, graph_version: str | None = None, graph_hash: str | None = None) -> None:
    timestamps = pd.to_datetime(frame.transaction_timestamp, errors="coerce", utc=True)
    write_json(path, {"generated_at_utc": utc_now(), "score_version": score_version,
                      "model_version": model_version, "calibration_version": calibration_version,
                      "graph_version": graph_version, "graph_sha256": graph_hash,
                      "score_file_sha256": sha256_file(score_path), "score_row_count": int(len(frame)),
                      "score_min_timestamp": str(timestamps.min()), "score_max_timestamp": str(timestamps.max()),
                      "input_frame_sha256": frame_fingerprint(frame),
                      "split_values": sorted(frame.split_name.astype(str).unique().tolist())})
