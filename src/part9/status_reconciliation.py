from __future__ import annotations

import json
from pathlib import Path


CONTROLLED = {"LOCKED", "READY", "FRAMEWORK_READY", "IN_PROGRESS", "INPUT_BLOCKED", "PRESENTATION_READY", "NOT_RUN", "NOT_APPLICABLE"}


def build_status_registry(root: Path) -> dict:
    part5 = json.loads((root / "assets/data/part5_final_summary.json").read_text(encoding="utf-8"))
    part7 = json.loads((root / "assets/data/part7_summary.json").read_text(encoding="utf-8"))
    part8 = json.loads((root / "assets/data/part8_summary.json").read_text(encoding="utf-8"))
    statuses = {
        "part1": {"label": "Business Scope", "status": "READY", "technical_status": "GOVERNANCE_READY", "source_part": 1, "deep_link": "part-1.html"},
        "part2": {"label": "Data Foundation", "status": "LOCKED", "technical_status": "FOUNDATION_READY", "source_part": 2, "deep_link": "part-2.html"},
        "part3": {"label": "Portfolio Intelligence", "status": "LOCKED", "technical_status": "PORTFOLIO_READY", "source_part": 3, "deep_link": "part-3.html"},
        "part4": {"label": "Behavioral Risk", "status": "LOCKED", "technical_status": "PASS", "source_part": 4, "deep_link": "part-4.html"},
        "part5": {"label": "Fraud Scoring / ML", "status": "LOCKED", "technical_status": part5.get("status", "PART5_MODELING_LOCKED"), "execution_status": "LOCKED", "champion_version": part5.get("champion", {}).get("version", "FRAUD_CHAMPION_v1"), "source_part": 5, "deep_link": "part-5.html"},
        "part6": {"label": "Network / Graph", "status": "LOCKED", "technical_status": "GRAPH_EVIDENCE_READY", "execution_status": "LOCKED", "source_part": 6, "deep_link": "part-6.html"},
        "part7": {"label": "Decision Engine", "status": "INPUT_BLOCKED", "technical_status": part7.get("technical_status", "TECHNICALLY_COMPLETE"), "execution_status": part7.get("status", "INPUT_BLOCKED"), "target_status": "DECISION_POLICY_LOCKED", "lock_condition": "64 PASS / 0 BLOCKED / 0 FAIL plus real final OOT decision evidence", "current_blocked_gates": part7.get("validation", {}).get("blocked", 35), "source_part": 7, "deep_link": "part-7.html"},
        "part8": {"label": "Monitoring & Governance", "status": "INPUT_BLOCKED", "technical_status": part8.get("technical_status", "FRAMEWORK_READY"), "execution_status": part8.get("status", "INPUT_BLOCKED"), "target_status": "MONITORING_GOVERNANCE_LOCKED", "lock_condition": "72 PASS / 0 BLOCKED / 0 FAIL plus real monitoring replay evidence", "current_blocked_gates": part8.get("validation", {}).get("blocked", 52), "source_part": 8, "deep_link": "part-8.html"},
    }
    for value in statuses.values():
        if value["status"] not in CONTROLLED:
            raise ValueError(f"Invalid status: {value['status']}")
    statuses["part9"] = {"label": "Final Portfolio", "status": "PRESENTATION_READY", "technical_status": "FINAL_PORTFOLIO_RELEASE_LOCKED", "execution_status": "PRESENTATION_READY", "source_part": 9, "deep_link": "index.html"}
    return {"project_status": "FINAL_PORTFOLIO_RELEASE_LOCKED", "generated_from": "executed_reports_and_locked_summaries", "layers": statuses}
