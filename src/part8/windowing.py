from __future__ import annotations

import pandas as pd


def _period_id(series: pd.Series, frequency: str) -> pd.Series:
    calendar = series.dt.tz_convert("UTC").dt.tz_localize(None)
    freq = frequency.upper()
    if freq == "DAY":
        return calendar.dt.strftime("D-%Y-%m-%d")
    if freq == "WEEK":
        return calendar.dt.to_period("W-SUN").astype(str).str.replace("/", "_", regex=False).radd("W-")
    if freq == "MONTH":
        return calendar.dt.to_period("M").astype(str).radd("M-")
    raise ValueError(f"Unsupported monitoring frequency: {frequency}")


def assign_windows(frame: pd.DataFrame, timestamp_col: str = "transaction_timestamp", frequencies: dict[str, str] | None = None) -> pd.DataFrame:
    if timestamp_col not in frame:
        raise ValueError(f"Missing {timestamp_col}")
    result = frame.copy()
    timestamps = pd.to_datetime(result[timestamp_col], utc=True, errors="coerce")
    if timestamps.isna().any():
        raise ValueError("Windowing requires parseable UTC timestamps")
    result[timestamp_col] = timestamps
    frequencies = frequencies or {"operational_window_id": "DAY", "drift_window_id": "WEEK", "performance_window_id": "MONTH"}
    for column, frequency in frequencies.items():
        result[column] = _period_id(timestamps, frequency)
    return result


def window_summary(frame: pd.DataFrame, window_col: str) -> pd.DataFrame:
    if window_col not in frame:
        raise ValueError(window_col)
    return frame.groupby(window_col, sort=True, dropna=False).size().rename("row_count").reset_index()
