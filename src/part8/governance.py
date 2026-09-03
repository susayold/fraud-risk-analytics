from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from .contracts import GOVERNANCE_ACTIONS


def recommendations(alerts: list[dict]) -> list[dict]:
    mapping = {"DATA_QUALITY": ("DATA_INCIDENT", "DATA_QUALITY_REVIEW"), "PERFORMANCE": ("MODEL_HEALTH_INCIDENT", "MODEL_RETRAIN_REVIEW_RECOMMENDED"), "CALIBRATION": ("MODEL_HEALTH_INCIDENT", "CALIBRATION_REVIEW_RECOMMENDED"), "POLICY": ("POLICY_OPERATIONS_INCIDENT", "POLICY_REVIEW_RECOMMENDED"), "REVIEW": ("POLICY_OPERATIONS_INCIDENT", "POLICY_REVIEW_RECOMMENDED"), "GRAPH": ("GRAPH_CONTEXT_INCIDENT", "GRAPH_REVIEW_RECOMMENDED")}
    result = []
    for alert in alerts:
        family = str(alert.get("signal_family", "")).upper()
        incident, action = next((value for key, value in mapping.items() if key in family), ("GOVERNANCE_INCIDENT", "INVESTIGATE"))
        if action not in GOVERNANCE_ACTIONS: action = "INVESTIGATE"
        evidence_hash = hashlib.sha256(json.dumps(alert, sort_keys=True, default=str).encode()).hexdigest()
        result.append({"window_id": alert.get("window_id", ""), "incident_type": incident, "recommendation": action, "severity": alert.get("severity", "AMBER"), "rationale": "aggregate monitoring evidence requires owner review; no automatic model or policy mutation", "evidence_hash": evidence_hash, "generated_at_utc": datetime.now(timezone.utc).isoformat()})
    return result

