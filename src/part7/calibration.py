"""Validation-only score calibration audit. No calibrator is fitted here."""
from __future__ import annotations

import numpy as np
import pandas as pd


def audit_calibration(
    scores: pd.DataFrame,
    labels: pd.DataFrame | None,
    *,
    score_version: str,
    calibration_version: str | None,
    score_status: str,
    scope: str,
    bins: int = 10,
) -> tuple[dict, pd.DataFrame]:
    """Compute reliability evidence only when an evaluation label is supplied."""
    required = {"source_row_id", "risk_score"}
    if required - set(scores.columns):
        raise ValueError(f"Calibration score frame missing {sorted(required - set(scores.columns))}")
    base = scores[["source_row_id", "risk_score"]].copy()
    base["risk_score"] = pd.to_numeric(base["risk_score"], errors="coerce")
    if labels is None:
        return ({"scope": scope, "score_version": score_version, "calibration_version": calibration_version,
                 "status": "NOT_EVALUATED", "expected_value_enabled": score_status == "PROBABILITY_USABLE",
                 "calibrator_fitted_in_part7": False, "rows": 0}, pd.DataFrame())
    joined = base.merge(labels[["source_row_id", "fraud_label"]], on="source_row_id", how="inner", validate="one_to_one")
    p = joined.risk_score.to_numpy(float)
    y = joined.fraud_label.astype(int).to_numpy()
    valid = np.isfinite(p) & np.isfinite(y) & (p >= 0) & (p <= 1)
    p, y = p[valid], y[valid]
    if len(p) == 0:
        return ({"scope": scope, "score_version": score_version, "calibration_version": calibration_version,
                 "status": "FAIL", "expected_value_enabled": False, "calibrator_fitted_in_part7": False, "rows": 0}, pd.DataFrame())
    clipped = np.clip(p, 1e-15, 1 - 1e-15)
    log_loss = float(-(y * np.log(clipped) + (1 - y) * np.log(1 - clipped)).mean())
    brier = float(np.mean((p - y) ** 2))
    groups = pd.DataFrame({"pred": p, "label": y, "bin": pd.cut(p, bins=np.linspace(0, 1, bins + 1), include_lowest=True)})
    reliability = groups.groupby("bin", observed=False).agg(rows=("label", "size"), mean_predicted_probability=("pred", "mean"), observed_fraud_rate=("label", "mean")).reset_index()
    reliability["scope"] = scope
    reliability["bin"] = reliability["bin"].astype(str)
    reliability["bin_gap"] = (reliability.mean_predicted_probability - reliability.observed_fraud_rate).abs()
    ece = float((reliability.bin_gap * reliability.rows / len(groups)).sum())
    status = "PASS" if score_status == "RANKING_ONLY" or calibration_version else "FAIL"
    return ({"scope": scope, "score_version": score_version, "calibration_version": calibration_version,
             "calibration_method": "UPSTREAM_ONLY", "calibrator_fitted_in_part7": False,
             "rows": int(len(p)), "brier_score": brier, "log_loss": log_loss,
             "expected_calibration_error": ece, "status": status,
             "expected_value_enabled": score_status == "PROBABILITY_USABLE" and bool(calibration_version)}, reliability)
