from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def _metric(metric_id, label, value, claim_class, source_part, source_artifact, status="AVAILABLE", section=""):
    return {"metric_id": metric_id, "label": label, "value": value, "claim_class": claim_class, "source_part": source_part, "source_artifact": source_artifact, "status": status, "section": section}


def build_metric_registry(root: Path) -> pd.DataFrame:
    part2 = json.loads((root / "assets/data/part2_summary.json").read_text(encoding="utf-8"))
    metrics = [
        _metric("source_total_transactions", "Total transactions", part2.get("transactions"), "OBSERVED", 2, "assets/data/part2_summary.json", section="hero"),
        _metric("source_fraud_transactions", "Fraud transactions", part2.get("fraud_transactions"), "OBSERVED", 2, "assets/data/part2_summary.json", section="hero"),
        _metric("source_fraud_rate", "Fraud rate", part2.get("fraud_rate"), "OBSERVED", 2, "assets/data/part2_summary.json", section="hero"),
        _metric("source_users", "Users", part2.get("users"), "OBSERVED", 2, "assets/data/part2_summary.json", section="hero"),
        _metric("source_cards", "Cards", part2.get("cards"), "OBSERVED", 2, "assets/data/part2_summary.json", section="hero"),
        _metric("source_merchants", "Merchants", part2.get("merchants"), "OBSERVED", 2, "assets/data/part2_summary.json", section="hero"),
    ]

    features = pd.read_csv(root / "docs/PART4_FEATURE_REGISTRY.csv")
    primary = features[features["model_role"].astype(str).str.lower().eq("primary")]
    metrics.append(_metric("behavior_primary_features", "Primary PIT behavioral features", int(len(primary)), "DERIVED", 4, "docs/PART4_FEATURE_REGISTRY.csv", section="behavior"))

    part8 = json.loads((root / "assets/data/part8_summary.json").read_text(encoding="utf-8"))
    metrics.append(_metric("monitoring_gate_count", "Mandatory monitoring gates", part8.get("validation", {}).get("mandatory_gates"), "GOVERNANCE", 8, "assets/data/part8_summary.json", section="monitoring"))

    part7 = json.loads((root / "assets/data/part7_summary.json").read_text(encoding="utf-8"))
    final = part7.get("final_evidence", {})
    queue = part7.get("queue", {})
    economics = part7.get("economics", {})
    metrics.extend([
        _metric("fraud_capture_rate", "Final OOT fraud capture rate", final.get("fraud_capture"), "SIMULATED", 7, "assets/data/part7_summary.json", section="business"),
        _metric("fraud_amount_capture", "Final OOT fraud exposure capture", final.get("fraud_exposure_capture"), "SIMULATED", 7, "assets/data/part7_summary.json", section="business"),
        _metric("precision", "Precision / hit rate", None, "DEFINITION", 1, "docs/PART3_KPI_DICTIONARY.md", status="NOT_APPLICABLE", section="business"),
        _metric("review_rate", "Final OOT review rate", final.get("review_rate"), "SIMULATED", 7, "assets/data/part7_summary.json", section="business"),
        _metric("capacity_utilization", "Review capacity utilization", queue.get("capacity_utilization"), "SIMULATED", 7, "assets/data/part7_summary.json", section="business"),
        _metric("expected_total_cost", "Selected-policy simulated total cost", economics.get("selected_cost", final.get("simulated_total_cost")), "SIMULATED", 7, "assets/data/part7_summary.json", section="business"),
    ])
    return pd.DataFrame(metrics)
