from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from math import isfinite
from typing import Any, Mapping


class Action(str, Enum):
    ALLOW = "ALLOW"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"


FORBIDDEN_POLICY_FIELDS = frozenset({
    "fraud_label", "target", "chargeback", "investigation_outcome", "future_outcome",
})


def _optional_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if str(value).strip().lower() in {"1", "true", "yes", "y"}:
        return True
    if str(value).strip().lower() in {"0", "false", "no", "n"}:
        return False
    raise ValueError(f"Cannot parse boolean context value: {value!r}")


@dataclass(frozen=True)
class DecisionContext:
    """Policy input DTO. It deliberately has no outcome/label field."""

    source_row_id: int
    transaction_timestamp: datetime
    risk_score: float
    amount: float
    pair_new: bool | None = None
    cold_card: bool | None = None
    new_merchant: bool | None = None
    cross_community: bool | None = None
    channel: str | None = None

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> "DecisionContext":
        forbidden = sorted(FORBIDDEN_POLICY_FIELDS.intersection(values))
        if forbidden:
            raise ValueError(f"Label firewall: forbidden policy fields: {forbidden}")
        timestamp = values.get("transaction_timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        score = float(values["risk_score"])
        amount = float(values["amount"])
        if not isfinite(score) or not 0 <= score <= 1:
            raise ValueError("risk_score must be finite and in [0, 1]")
        if not isfinite(amount):
            raise ValueError("amount must be finite")
        return cls(
            source_row_id=int(values["source_row_id"]),
            transaction_timestamp=timestamp,
            risk_score=score,
            amount=amount,
            pair_new=_optional_bool(values.get("pair_new")),
            cold_card=_optional_bool(values.get("cold_card")),
            new_merchant=_optional_bool(values.get("new_merchant")),
            cross_community=_optional_bool(values.get("cross_community")),
            channel=str(values["channel"]) if values.get("channel") is not None else None,
        )


@dataclass(frozen=True)
class PolicyConfig:
    policy_version: str
    review_threshold: float
    block_threshold: float
    review_capacity: float
    priority_method: str = "SCORE_ONLY"
    max_block_rate: float | None = None
    max_legitimate_block_rate: float | None = None

    def __post_init__(self) -> None:
        if not self.policy_version:
            raise ValueError("policy_version is required")
        if not all(isfinite(float(x)) for x in (self.review_threshold, self.block_threshold, self.review_capacity)):
            raise ValueError("policy thresholds and capacity must be finite")
        if not 0 <= self.review_threshold < self.block_threshold <= 1:
            raise ValueError("review_threshold must be < block_threshold within [0, 1]")
        if not 0 <= self.review_capacity <= 1:
            raise ValueError("review_capacity must be within [0, 1]")


@dataclass(frozen=True)
class ReviewCandidate:
    source_row_id: int
    priority: float
    risk_score: float
    exposure_proxy: float
    reason_codes: tuple[str, ...]


def assert_policy_columns(columns: list[str] | tuple[str, ...] | set[str]) -> None:
    forbidden = sorted(FORBIDDEN_POLICY_FIELDS.intersection(columns))
    if forbidden:
        raise ValueError(f"Label firewall: forbidden policy columns: {forbidden}")
