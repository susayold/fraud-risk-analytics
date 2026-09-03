from __future__ import annotations


def persistence_status(history: list[str], breach: bool, required: str = "2_of_3") -> str:
    statuses = (history + ["RED" if breach else "GREEN"])[-3:]
    if required == "2_consecutive":
        return "RED" if len(statuses) >= 2 and statuses[-1] == statuses[-2] == "RED" else statuses[-1]
    return "RED" if sum(status == "RED" for status in statuses) >= 2 else statuses[-1]

