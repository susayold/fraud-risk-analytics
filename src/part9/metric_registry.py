from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def _metric(metric_id, label, value, claim_class, source_part, source_artifact, status="AVAILABLE", section=""):
    return {"metric_id": metric_id, "label": label, "value": value, "claim_class": claim_class, "source_part": source_part, "source_artifact": source_artifact, "status": status, "section": section}


def build_metric_registry(root: Path) -> pd.DataFrame:
    part2_path = root / "assets/data/part2_summary.json"
    part2 = json.loads(part2_path.read_text(encoding="utf-8"))
    metrics = [
        _metric("source_total_transactions", "Total transactions", part2.get("transactions"), "OBSERVED", 2, "assets/data/part2_summary.json", section="hero"),
        _metric("source_fraud_transactions", "Fraud transactions", part2.get("fraud_transactions"), "OBSERVED", 2, "assets/data/part2_summary.json", section="hero"),
        _metric("source_fraud_rate", "Fraud rate", part2.get("fraud_rate"), "OBSERVED", 2, "assets/data/part2_summary.json", section="hero"),
        _metric("source_users", "Users", part2.get("users"), "OBSERVED", 2, "assets/data/part2_summary.json", section="hero"),
        _metric("source_cards", "Cards", part2.get("cards"), "OBSERVED", 2, "assets/data/part2_summary.json", section="hero"),
        _metric("source_merchants", "Merchants", part2.get("merchants"), "OBSERVED", 2, "assets/data/part2_summary.json", section="hero"),
    ]
    feature_path = root / "docs/PART4_FEATURE_REGISTRY.csv"
    features = pd.read_csv(feature_path)
    metrics.append(_metric("behavior_primary_features", "Primary PIT behavioral features", int(len(features[features["model_role"].astype(str).str.lower().eq("primary")])), "DERIVED", 4, "docs/PART4_FEATURE_REGISTRY.csv", section="behavior"))
    part8_path = root / "assets/data/part8_summary.json"
    part8 = json.loads(part8_path.read_text(encoding="utf-8"))
    metrics.append(_metric("monitoring_gate_count", "Mandatory monitoring gates", part8.get("validation", {}).get("mandatory_gates"), "GOVERNANCE", 8, "assets/data/part8_summary.json", section="monitoring"))
    definition_items = [("fraud_capture_rate", "Fraud capture rate"), ("fraud_amount_capture", "Fraud amount capture"), ("precision", "Precision / hit rate"), ("review_rate", "Review rate"), ("capacity_utilization", "Capacity utilization"), ("expected_total_cost", "Expected total cost")]
    for metric_id, label in definition_items:
        metrics.append(_metric(metric_id, label, None, "DEFINITION", 1, "docs/PART3_KPI_DICTIONARY.md", status="NOT_APPLICABLE", section="business"))
    return pd.DataFrame(metrics)
