from __future__ import annotations

import numpy as np
import pandas as pd

from .contracts import ACTION_DOMAIN


REQUIRED_COLUMNS = ("source_row_id", "transaction_timestamp", "amount", "risk_score", "split_name")


def schema_check(frame: pd.DataFrame, required: tuple[str, ...] = REQUIRED_COLUMNS) -> dict:
    missing = sorted(set(required) - set(frame.columns))
    return {"status": "PASS" if not missing else "FAIL", "missing_columns": missing, "required_columns": list(required)}


def quality_profile(frame: pd.DataFrame, known_categories: dict[str, list[str]] | None = None, baseline_missing: dict[str, float] | None = None) -> dict:
    known_categories = known_categories or {}
    baseline_missing = baseline_missing or {}
    rows = len(frame)
    timestamps = pd.to_datetime(frame.get("transaction_timestamp"), utc=True, errors="coerce") if "transaction_timestamp" in frame else pd.Series(dtype="datetime64[ns, UTC]")
    scores = pd.to_numeric(frame.get("risk_score"), errors="coerce") if "risk_score" in frame else pd.Series(dtype=float)
    amounts = pd.to_numeric(frame.get("amount"), errors="coerce") if "amount" in frame else pd.Series(dtype=float)
    duplicate_rate = float(1 - frame.source_row_id.nunique() / rows) if rows and "source_row_id" in frame else float("nan")
    metrics = {
        "row_count": rows,
        "unique_source_row_id": int(frame.source_row_id.nunique()) if "source_row_id" in frame else 0,
        "duplicate_row_rate": duplicate_rate,
        "timestamp_parse_error_rate": float(timestamps.isna().mean()) if rows else float("nan"),
        "future_timestamp_rate": 0.0,
        "score_missing_rate": float(scores.isna().mean()) if rows else float("nan"),
        "score_out_of_range_rate": float((~scores.between(0, 1)).fillna(False).mean()) if rows else float("nan"),
        "amount_nonfinite_rate": float((~np.isfinite(amounts)).fillna(False).mean()) if rows else float("nan"),
        "null_rate": {str(col): float(frame[col].isna().mean()) for col in frame.columns},
        "structural_missingness_delta": {str(col): float(frame[col].isna().mean() - baseline_missing.get(col, frame[col].isna().mean())) for col in frame.columns},
        "unknown_category_rate": {},
        "new_category_rate": {},
    }
    for col, known in known_categories.items():
        if col in frame and rows:
            values = frame[col].astype("string")
            unknown = ~values.isin([str(x) for x in known])
            metrics["unknown_category_rate"][col] = float(unknown.mean())
            metrics["new_category_rate"][col] = float((values.dropna().isin([str(x) for x in known])).eq(False).mean()) if values.notna().any() else 0.0
    issues = []
    if metrics["duplicate_row_rate"] > 0: issues.append("DUPLICATE_SOURCE_ROW_ID")
    if metrics["timestamp_parse_error_rate"] > 0: issues.append("TIMESTAMP_PARSE_FAILURE")
    if metrics["score_missing_rate"] > 0: issues.append("SCORE_MISSING")
    if metrics["score_out_of_range_rate"] > 0: issues.append("SCORE_OUT_OF_RANGE")
    if metrics["amount_nonfinite_rate"] > 0: issues.append("AMOUNT_NONFINITE")
    if "action" in frame and not frame.action.astype(str).str.upper().isin(ACTION_DOMAIN).all(): issues.append("ACTION_DOMAIN_FAILURE")
    metrics["critical_issues"] = issues
    metrics["status"] = "FAIL" if issues else "PASS"
    return metrics


def quality_table(profile: dict) -> pd.DataFrame:
    scalar = {k: v for k, v in profile.items() if not isinstance(v, (dict, list))}
    return pd.DataFrame([{"metric": key, "value": value, "status": profile.get("status", "PASS")} for key, value in scalar.items()])

