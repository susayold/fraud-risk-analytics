from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


OPERATIONAL = "OPERATIONS_NOW"
MATURED = "OUTCOMES_MATURED"
SEVERITIES = ("GREEN", "AMBER", "RED", "BLOCKED", "INSUFFICIENT_SUPPORT", "NOT_APPLICABLE")
GOVERNANCE_ACTIONS = (
    "OBSERVE", "INVESTIGATE", "DATA_QUALITY_REVIEW", "POLICY_REVIEW_RECOMMENDED",
    "CALIBRATION_REVIEW_RECOMMENDED", "MODEL_RETRAIN_REVIEW_RECOMMENDED", "GRAPH_REVIEW_RECOMMENDED",
)
FORBIDDEN_OPERATIONAL_FIELDS = {"fraud_label", "future_outcome", "future_dispute", "review_case_id"}
FORBIDDEN_PUBLIC_FIELDS = FORBIDDEN_OPERATIONAL_FIELDS | {"source_row_id", "transaction_id", "transaction_timestamp", "risk_score", "primary_fraud_score", "amount", "positive_exposure", "action", "candidate_action", "reason_codes", "review_priority", "review_rank", "review_selected", "review_overflow", "bucket_selected", "overflow"}
ACTION_DOMAIN = {"ALLOW", "REVIEW", "BLOCK"}


def ensure_severity(value: str) -> str:
    value = str(value).upper()
    if value not in SEVERITIES:
        raise ValueError(f"Invalid Part 8 severity: {value}")
    return value


def ensure_public_safe(columns: list[str] | set[str]) -> None:
    forbidden = sorted({str(column).lower() for column in columns} & FORBIDDEN_PUBLIC_FIELDS)
    if forbidden:
        raise ValueError(f"Public export contains forbidden row-level fields: {sorted(set(forbidden))}")


@dataclass(frozen=True)
class MonitoringEvent:
    source_row_id: str
    transaction_timestamp: str
    amount: float | None = None
    positive_exposure: float | None = None
    score: float | None = None
    score_status: str | None = None
    model_version: str | None = None
    score_version: str | None = None
    calibration_version: str | None = None
    policy_version: str | None = None
    action: str | None = None
    review_selected: bool | None = None
    review_overflow: bool | None = None
    channel: str | None = None
    pair_new: bool | None = None
    cold_card: bool | None = None
    new_merchant: bool | None = None
    cross_community: bool | None = None
    graph_version: str | None = None
    extras: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ReferenceWindow:
    window_id: str
    start: str
    end: str
    row_count: int
    feature_registry_hash: str
    bins: Mapping[str, list[float]] = field(default_factory=dict)
    categories: Mapping[str, list[str]] = field(default_factory=dict)


@dataclass(frozen=True)
class ObservationWindow:
    window_id: str
    start: str
    end: str
    row_count: int
    label_mode: str = OPERATIONAL


@dataclass(frozen=True)
class MonitoringSignal:
    window_id: str
    signal_family: str
    metric: str
    observed: float | None
    threshold: float | None
    severity: str
    support: int
    claim_class: str
    evidence_artifact: str = ""


@dataclass(frozen=True)
class Alert:
    alert_id: str
    window_id: str
    signal_family: str
    metric: str
    severity: str
    observed: float | None
    threshold: float | None
    support: int
    recommended_action: str
    claim_class: str
    evidence_artifact: str = ""


@dataclass(frozen=True)
class GovernanceRecommendation:
    window_id: str
    incident_type: str
    recommendation: str
    severity: str
    rationale: str
    evidence_hash: str = ""


@dataclass(frozen=True)
class MonitoringRun:
    run_id: str
    mode: str
    code_commit: str
    input_hash: str
    baseline_id: str | None
    label_mode: str
    status: str
    rows: int = 0
    window_count: int = 0
