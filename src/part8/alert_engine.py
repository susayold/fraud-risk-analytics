from __future__ import annotations

import pandas as pd

from .contracts import Alert, SEVERITIES, ensure_severity


def classify(observed: float | None, amber: float | None, red: float | None, support: int = 0, min_support: int = 0, hard_failure: bool = False) -> str:
    if hard_failure: return "RED"
    if observed is None or amber is None or red is None: return "INSUFFICIENT_SUPPORT" if support < min_support else "BLOCKED"
    if support < min_support: return "INSUFFICIENT_SUPPORT"
    if observed >= red: return "RED"
    if observed >= amber: return "AMBER"
    return "GREEN"


def build_alerts(signals: pd.DataFrame, thresholds: dict[str, dict], window_id: str = "") -> pd.DataFrame:
    rows = []
    for row in signals.to_dict("records"):
        rule = thresholds.get(str(row.get("metric")), {})
        severity = classify(row.get("observed"), rule.get("amber"), rule.get("red"), int(row.get("support", 0) or 0), int(rule.get("min_support", 0) or 0), bool(row.get("hard_failure", False)))
        ensure_severity(severity)
        rows.append({"alert_id": f"P8-{str(row.get('metric'))}-{str(row.get('window_id', window_id))}", "window_id": row.get("window_id", window_id), "signal_family": row.get("signal_family", "UNKNOWN"), "metric": row.get("metric"), "severity": severity, "observed": row.get("observed"), "threshold": rule.get("red"), "support": int(row.get("support", 0) or 0), "claim_class": row.get("claim_class", "EARLY_WARNING"), "evidence_artifact": row.get("evidence_artifact", "")})
    return pd.DataFrame(rows)

