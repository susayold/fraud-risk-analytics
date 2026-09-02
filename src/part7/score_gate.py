from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .contracts import assert_policy_columns


REQUIRED = ("source_row_id", "transaction_timestamp", "risk_score", "amount", "split_name")


@dataclass(frozen=True)
class ScoreGate:
    status: str
    score_version: str
    calibration_version: str | None
    checks: tuple[dict, ...]


def audit_score_frame(frame: pd.DataFrame, score_status: str | None, score_version: str = "UNSPECIFIED", calibration_version: str | None = None) -> ScoreGate:
    checks: list[dict] = []
    missing = sorted(set(REQUIRED) - set(frame.columns))
    checks.append({"check_name": "P7T01_required_columns", "status": "PASS" if not missing else "FAIL", "notes": f"missing={missing}"})
    if missing:
        return ScoreGate("INPUT_BLOCKED", score_version, calibration_version, tuple(checks))
    assert_policy_columns(list(frame.columns))
    checks.append({"check_name": "P7T02_source_row_id_unique", "status": "PASS" if frame.source_row_id.is_unique else "FAIL", "notes": "Decision input key must be unique."})
    timestamps = pd.to_datetime(frame.transaction_timestamp, errors="coerce")
    checks.append({"check_name": "P7T03_timestamp_parse", "status": "PASS" if timestamps.notna().all() else "FAIL", "notes": "Canonical transaction timestamp."})
    score = pd.to_numeric(frame.risk_score, errors="coerce")
    checks.append({"check_name": "P7T04_score_finite", "status": "PASS" if score.notna().all() and score.map(pd.api.types.is_number).all() else "FAIL", "notes": "No null or non-finite score."})
    checks.append({"check_name": "P7T05_score_range", "status": "PASS" if score.between(0, 1).all() else "FAIL", "notes": "Declared range [0, 1]."})
    amount = pd.to_numeric(frame.amount, errors="coerce")
    checks.append({"check_name": "P7T06_amount_finite", "status": "PASS" if amount.notna().all() else "FAIL", "notes": "Signed amount is source input, not realized loss."})
    checks.append({"check_name": "P7T07_split_values", "status": "PASS" if frame.split_name.notna().all() else "FAIL", "notes": "Split artifact is required."})
    checks.append({"check_name": "P7T08_probability_status_explicit", "status": "PASS" if score_status in {"PROBABILITY_USABLE", "RANKING_ONLY"} else "FAIL", "notes": "Expected-value formulas require an explicit status."})
    if score_status == "PROBABILITY_USABLE" and not calibration_version:
        checks.append({"check_name": "P7T09_calibration_metadata", "status": "FAIL", "notes": "Calibration version is required for probability use."})
    else:
        checks.append({"check_name": "P7T09_calibration_metadata", "status": "PASS" if score_status == "RANKING_ONLY" or calibration_version else "FAIL", "notes": "Ranking-only status disables expected-value interpretation."})
    status = "SCORE_GATE_LOCKED" if all(row["status"] == "PASS" for row in checks) else "INPUT_BLOCKED"
    return ScoreGate(status, score_version, calibration_version, tuple(checks))


def discover_primary_score_artifact(root: Path) -> list[Path]:
    """Discovery only; never substitutes a different model when the champion is absent."""
    candidates = []
    for pattern in ("**/*part5*score*.csv", "**/*PRIMARY_FRAUD_SCORE*.csv", "**/*prediction*.parquet", "**/*score*.parquet"):
        candidates.extend(root.glob(pattern))
    return sorted({p for p in candidates if p.is_file() and "private" not in p.parts})
