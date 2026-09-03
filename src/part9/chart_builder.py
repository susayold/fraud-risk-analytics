from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def _blocked(chart_id, section, title, source, claim, reason):
    return {"chart_id": chart_id, "section": section, "title": title, "chart_type": "evidence-state", "source_artifact": source, "x_field": "", "y_field": "", "support_field": "", "claim_class": claim, "render_condition": "status == AVAILABLE", "status": "INPUT_BLOCKED", "reason": reason, "insight": "Upstream governed evidence is required before this view can render.", "badge": claim if claim == "SIMULATED" else "INPUT BLOCKED", "data": []}


def _available(chart_id, section, title, chart_type, source, claim, data, x_field, y_field, support_field, insight, status="AVAILABLE"):
    return {"chart_id": chart_id, "section": section, "title": title, "chart_type": chart_type, "source_artifact": source, "x_field": x_field, "y_field": y_field, "support_field": support_field, "claim_class": claim, "render_condition": "status == AVAILABLE", "status": status, "reason": "", "insight": insight, "badge": claim, "data": data}


def build_charts(root: Path) -> dict:
    part2 = json.loads((root / "assets/data/part2_summary.json").read_text(encoding="utf-8"))
    fraud, total = int(part2["fraud_transactions"]), int(part2["transactions"])
    charts = {
        "D1": _available("D1", "data", "Fraud class imbalance", "bar", "assets/data/part2_summary.json", "OBSERVED", [{"label": "Legitimate", "value": total - fraud}, {"label": "Fraud", "value": fraud}], "label", "value", "", "Fraud is rare, so accuracy alone would obscure the risk signal."),
    }
    split = pd.read_csv(root / "reports/split_summary.csv")
    split_data = split[["split_name", "row_count", "fraud_count"]].rename(columns={"split_name": "label", "row_count": "transactions", "fraud_count": "fraud_transactions"}).to_dict("records")
    split_data = [{k: (int(v) if k in {"transactions", "fraud_transactions"} else v) for k, v in row.items()} for row in split_data]
    charts["D2"] = _available("D2", "data", "Transactions by chronological split", "bar", "reports/split_summary.csv", "OBSERVED", split_data, "label", "transactions", "fraud_transactions", "Chronological splits preserve the time direction required for honest evaluation.")
    rate_data = [{"label": row["split_name"], "fraud_rate": float(row["fraud_count"] / row["row_count"])} for _, row in split.iterrows()]
    charts["D3"] = _available("D3", "data", "Fraud rate by chronological split", "bar", "reports/split_summary.csv", "OBSERVED", rate_data, "label", "fraud_rate", "", "Fraud prevalence is reported separately from volume to keep units interpretable.")
    monthly = pd.read_csv(root / "reports/part3/monthly_fraud_trend.csv").dropna(subset=["month"])
    charts["P1"] = _available("P1", "portfolio", "Monthly fraud trend", "line", "reports/part3/monthly_fraud_trend.csv", "OBSERVED", monthly[["month", "fraud_rate", "transactions", "fraud_transactions"]].to_dict("records"), "month", "fraud_rate", "transactions", "The trend is descriptive Development discovery evidence, not a causal time series.")
    channel = pd.read_csv(root / "reports/part3/channel_risk.csv")
    charts["P2"] = _available("P2", "portfolio", "Channel fraud risk", "bar", "reports/part3/channel_risk.csv", "OBSERVED", channel[["segment_value", "fraud_rate", "fraud_lift", "transactions", "fraud_transactions", "support_status"]].rename(columns={"segment_value": "label"}).to_dict("records"), "label", "fraud_rate", "transactions", "Channel mix is a portfolio signal; support and scope stay visible in the tooltip.")
    amount = pd.read_csv(root / "reports/part3/amount_band_risk.csv")
    charts["P3"] = _available("P3", "portfolio", "Amount-band fraud risk", "bar", "reports/part3/amount_band_risk.csv", "OBSERVED", amount[["segment_value", "fraud_rate", "fraud_lift", "transactions", "fraud_transactions", "support_status"]].rename(columns={"segment_value": "label"}).to_dict("records"), "label", "fraud_rate", "transactions", "Predefined amount bands keep the comparison interpretable and support-qualified.")
    mcc = pd.read_csv(root / "reports/part3/mcc_risk.csv")
    mcc = mcc[mcc["support_status"].astype(str).eq("SUFFICIENT")].sort_values(["fraud_lift", "transactions"], ascending=[False, False]).head(10)
    charts["P4"] = _available("P4", "portfolio", "Support-qualified MCC risk", "bar", "reports/part3/mcc_risk.csv", "OBSERVED", mcc[["segment_value", "fraud_rate", "fraud_lift", "transactions", "fraud_transactions", "support_status"]].rename(columns={"segment_value": "label"}).to_dict("records"), "label", "fraud_rate", "transactions", "Tiny categories are excluded from the headline ranking through the locked support rule.")
    features = pd.read_csv(root / "docs/PART4_FEATURE_REGISTRY.csv")
    family = features.groupby("feature_family").size().reset_index(name="feature_count").rename(columns={"feature_family": "label"})
    charts["B1"] = _available("B1", "behavior", "Primary PIT feature family count", "bar", "docs/PART4_FEATURE_REGISTRY.csv", "DERIVED", family.to_dict("records"), "label", "feature_count", "", "The feature registry is the source of truth for behavioral feature coverage.")
    blocked = [
        ("P5", "portfolio", "Entity concentration", "reports/part3/top_entity_concentration.csv", "OBSERVED", "No safe aggregate source is currently registered for this view."),
        ("B2", "behavior", "Behavioral signal profile", "reports/part4/development_numeric_feature_signal.csv", "DERIVED", "Current evidence is QA-slice governed; no headline signal is promoted here."),
        ("M1", "model", "Validation PR-AUC comparison", "reports/part5/executed_model_comparison.csv", "DERIVED", "Part 5 executed model metrics are not available in the public evidence set."),
        ("M2", "model", "Precision-recall curve", "reports/part5/pr_curve.csv", "DERIVED", "Executed curve points are required."),
        ("M3", "model", "Calibration curve", "reports/part5/calibration.csv", "DERIVED", "Calibration requires probability-usable executed evidence."),
        ("M4", "model", "Top-K fraud capture", "reports/part5/topk.csv", "DERIVED", "Natural-prevalence executed evidence is required."),
        ("G1", "graph", "Graph novelty mix", "reports/part6/graph_novelty.csv", "DERIVED", "Audited aggregate graph evidence is not in this repository."),
        ("G2", "graph", "Incremental graph value", "reports/part6/graph_incremental_value.csv", "DERIVED", "Executed tabular-versus-graph comparison is not available."),
        ("DE1", "decision", "Decision mix", "reports/part7/final_decision_mix.csv", "SIMULATED", "Part 7 final decision mart is INPUT BLOCKED."),
        ("DE2", "decision", "Review capacity", "reports/part7/review_capacity.csv", "SIMULATED", "Part 7 final decision mart is INPUT BLOCKED."),
        ("DE3", "decision", "Fraud capture vs intervention", "reports/part7/policy_sensitivity.csv", "SIMULATED", "Part 7 outcome evidence is INPUT BLOCKED."),
        ("DE4", "decision", "Simulated economics", "reports/part7/economics.csv", "SIMULATED", "Part 7 policy evidence is INPUT BLOCKED."),
        ("MON1", "monitoring", "Drift timeline", "reports/part8/monitoring_reconciliation.json", "GOVERNANCE", "Part 8 final replay is INPUT BLOCKED."),
        ("MON2", "monitoring", "Action and review drift", "reports/part8/monitoring_reconciliation.json", "GOVERNANCE", "Part 7 decision evidence is INPUT BLOCKED."),
        ("MON3", "monitoring", "Matured performance over time", "reports/part8/matured_model_performance.csv", "GOVERNANCE", "Outcomes-matured replay evidence is INPUT BLOCKED."),
    ]
    for item in blocked:
        charts[item[0]] = _blocked(*item)
    return charts
