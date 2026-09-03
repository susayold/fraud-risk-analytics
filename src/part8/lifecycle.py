from __future__ import annotations

STATES = ("INPUT_BLOCKED", "FRAMEWORK_BUILDING", "MONITORING_FRAMEWORK_READY", "BASELINE_READY", "MONITORING_BASELINE_FROZEN", "MONITORING_REPLAY_COMPLETE", "MONITORING_GOVERNANCE_LOCKED")
TRANSITIONS = {
    "INPUT_BLOCKED": {"MONITORING_FRAMEWORK_READY"},
    "FRAMEWORK_BUILDING": {"MONITORING_FRAMEWORK_READY"},
    "MONITORING_FRAMEWORK_READY": {"BASELINE_READY"},
    "BASELINE_READY": {"MONITORING_BASELINE_FROZEN"},
    "MONITORING_BASELINE_FROZEN": {"MONITORING_REPLAY_COMPLETE"},
    "MONITORING_REPLAY_COMPLETE": {"MONITORING_GOVERNANCE_LOCKED"},
}


def assert_transition(current: str, target: str) -> None:
    if current not in STATES or target not in STATES:
        raise ValueError(f"Unknown Part 8 lifecycle state: {current} -> {target}")
    if target not in TRANSITIONS.get(current, set()):
        raise ValueError(f"Illegal Part 8 lifecycle transition: {current} -> {target}")


def can_lock(gates_pass: int, gates_blocked: int, gates_fail: int, lifecycle_status: str) -> bool:
    return lifecycle_status == "MONITORING_REPLAY_COMPLETE" and gates_pass == 72 and gates_blocked == 0 and gates_fail == 0

