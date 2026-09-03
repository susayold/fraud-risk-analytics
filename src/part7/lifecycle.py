"""Stage-specific state machine for the Part 7 closure lifecycle."""
from __future__ import annotations

import pandas as pd

STATES = ("INPUT_BLOCKED", "TECHNICALLY_READY", "POLICY_SELECTED", "POLICY_FROZEN", "FINAL_REPLAY_COMPLETE", "DECISION_POLICY_LOCKED")
TRANSITIONS = {"INPUT_BLOCKED": {"TECHNICALLY_READY"}, "TECHNICALLY_READY": {"POLICY_SELECTED"}, "POLICY_SELECTED": {"POLICY_FROZEN"}, "POLICY_FROZEN": {"FINAL_REPLAY_COMPLETE"}, "FINAL_REPLAY_COMPLETE": {"DECISION_POLICY_LOCKED"}}


def assert_transition(current: str, target: str) -> None:
    if target not in STATES or target not in TRANSITIONS.get(current, set()):
        raise ValueError(f"Forbidden Part 7 lifecycle transition: {current} -> {target}")


def lock_eligibility(first_63: pd.DataFrame | pd.Series, lifecycle_status: str) -> bool:
    """Gate 64 eligibility before the status is changed to LOCKED."""
    statuses = first_63.status if isinstance(first_63, pd.DataFrame) else first_63
    return lifecycle_status == "FINAL_REPLAY_COMPLETE" and len(statuses) == 63 and bool((statuses == "PASS").all())


def can_lock(*, gates_pass: int, gates_blocked: int, gates_fail: int, replay_status: str) -> bool:
    return replay_status == "FINAL_REPLAY_COMPLETE" and gates_pass in {63, 64} and gates_blocked == 0 and gates_fail == 0
