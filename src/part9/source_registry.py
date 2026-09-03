from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd


SOURCE_DEFINITIONS = [
    ("part2_summary", "assets/data/part2_summary.json", 2, "FOUNDATION", "OBSERVED", ["source_total_transactions", "source_fraud_transactions", "source_fraud_rate", "source_users", "source_cards", "source_merchants"], ["D1"]),
    ("part2_split_summary", "reports/split_summary.csv", 2, "FOUNDATION", "OBSERVED", ["split_volume", "split_fraud_rate"], ["D2", "D3"]),
    ("part3_monthly_trend", "reports/part3/monthly_fraud_trend.csv", 3, "PORTFOLIO", "OBSERVED", ["monthly_fraud_trend"], ["P1"]),
    ("part3_channel_risk", "reports/part3/channel_risk.csv", 3, "PORTFOLIO", "OBSERVED", ["channel_fraud_risk"], ["P2"]),
    ("part3_amount_band_risk", "reports/part3/amount_band_risk.csv", 3, "PORTFOLIO", "OBSERVED", ["amount_band_fraud_risk"], ["P3"]),
    ("part3_mcc_risk", "reports/part3/mcc_risk.csv", 3, "PORTFOLIO", "OBSERVED", ["mcc_fraud_risk"], ["P4"]),
    ("part4_feature_registry", "docs/PART4_FEATURE_REGISTRY.csv", 4, "BEHAVIOR", "DERIVED", ["behavior_primary_features"], ["B1"]),
    ("part5_summary", "assets/data/part5_summary.json", 5, "MODEL", "DERIVED", [], ["M1", "M2", "M3", "M4"]),
    ("part6_presentation", "part-6.html", 6, "GRAPH", "DERIVED", [], ["G1", "G2"]),
    ("part7_summary", "assets/data/part7_summary.json", 7, "DECISION", "SIMULATED", [], ["DE1", "DE2", "DE3", "DE4"]),
    ("part8_summary", "assets/data/part8_summary.json", 8, "MONITORING", "GOVERNANCE", ["monitoring_gate_count"], ["MON1", "MON2", "MON3"]),
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_source_registry(root: Path) -> pd.DataFrame:
    rows = []
    for source_id, relative_path, source_part, section, claim_class, metric_ids, chart_ids in SOURCE_DEFINITIONS:
        path = root / relative_path
        available = path.exists() and path.is_file()
        rows.append({"source_id": source_id, "path": relative_path, "source_part": source_part, "section": section, "claim_class": claim_class, "metric_ids": ";".join(metric_ids), "chart_ids": ";".join(chart_ids), "status": "AVAILABLE" if available else "NOT_AVAILABLE", "sha256": sha256_file(path) if available else "NOT_AVAILABLE", "bytes": path.stat().st_size if available else None})
    return pd.DataFrame(rows)
