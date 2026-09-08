from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def _blocked(chart_id, section, title, source, claim, reason, status="NOT_AVAILABLE"):
    return {"chart_id": chart_id, "section": section, "title": title, "chart_type": "evidence-state", "source_artifact": source, "x_field": "", "y_field": "", "support_field": "", "claim_class": claim, "render_condition": "status == AVAILABLE", "status": status, "reason": reason, "insight": "The public release does not synthesize values that were not retained in governed aggregate evidence.", "badge": "NOT RETAINED" if status == "NOT_AVAILABLE" else claim, "data": []}


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
    concentration = pd.read_csv(root / "reports/part3/top_entity_concentration.csv")
    concentration = concentration[concentration["rank_band"].astype(str).eq("top_1pct")].copy()
    concentration["entity_type"] = concentration["entity_type"].replace({"MERCHANT_IDENTIFIER": "MERCHANT"})
    concentration = concentration.rename(columns={"entity_type": "label", "fraud_capture_share": "fraud_capture_share"})
    charts["P5"] = _available("P5", "portfolio", "Entity concentration (top 1% fraud share)", "bar", "reports/part3/top_entity_concentration.csv", "DERIVED", concentration[["label", "fraud_capture_share", "rank_band"]].to_dict("records"), "label", "fraud_capture_share", "", "Aggregate concentration is shown without publishing raw entity identifiers.")

    features = pd.read_csv(root / "docs/PART4_FEATURE_REGISTRY.csv")
    family = features.groupby("feature_family").size().reset_index(name="feature_count").rename(columns={"feature_family": "label"})
    charts["B1"] = _available("B1", "behavior", "Primary PIT feature family count", "bar", "docs/PART4_FEATURE_REGISTRY.csv", "DERIVED", family.to_dict("records"), "label", "feature_count", "", "The feature registry is the source of truth for behavioral feature coverage.")
    charts["B2"] = _blocked("B2", "behavior", "Behavioral signal profile", "reports/part4/development_numeric_feature_signal.csv", "DERIVED", "Current public evidence is QA-slice governed; no full-population signal profile is promoted.")

    part6 = json.loads((root / "assets/data/part6_summary.json").read_text(encoding="utf-8"))
    charts["G1"] = _available("G1", "graph", "Graph network scale", "bar", "assets/data/part6_summary.json", "DERIVED", [{"label": "Total nodes", "value": part6["graph"]["total_nodes"]}, {"label": "Unique pairs", "value": part6["graph"]["train_unique_edges"]}, {"label": "Leiden communities", "value": part6["graph"]["leiden_communities"]}], "label", "value", "", "Governed aggregate graph scale; no raw IDs or edges are published.")
    charts["G2"] = _available("G2", "graph", "Graph model comparison (Test warm PR-AUC)", "bar", "assets/data/part6_summary.json", "DERIVED", [{"label": row["model"], "pr_auc": row["pr_auc"]} for row in part6["model_comparison"]["test_warm"]], "label", "pr_auc", "", "Graph context is complementary; the overall Test difference is not statistically robust.")

    part5 = json.loads((root / "assets/data/part5_final_summary.json").read_text(encoding="utf-8"))
    selection = json.loads((root / "assets/data/part5_model_selection.json").read_text(encoding="utf-8"))
    calibration = json.loads((root / "assets/data/part5_calibration.json").read_text(encoding="utf-8"))
    topk = json.loads((root / "assets/data/part5_topk.json").read_text(encoding="utf-8"))
    charts["M1"] = _available("M1", "model", "Validation selection leaderboard", "bar", "assets/data/part5_model_selection.json", "DERIVED", [{"label": r["model"], "pr_auc": r["pr_auc"]} for r in selection["rows"]], "label", "pr_auc", "", "BlendTop3_Equal is the frozen Validation champion.")
    charts["M2"] = _blocked("M2", "model", "Precision-recall curve", "assets/data/part5_final_summary.json", "DERIVED", "PR-curve coordinates were not retained in the final aggregate evidence.")
    charts["M3"] = _available("M3", "model", "OOT calibration summary", "bar", "assets/data/part5_calibration.json", "DERIVED", [{"label": "Brier", "value": calibration["metrics"]["brier"]}, {"label": "LogLoss", "value": calibration["metrics"]["log_loss"]}], "label", "value", "", "Calibration intercept and slope are available; exact bin coordinates are not synthesized.")
    charts["M4"] = _available("M4", "model", "OOT Top-K fraud capture", "line", "assets/data/part5_topk.json", "DERIVED", [{"label": f"{r['top_k']:.1%}", "capture": r["capture"], "precision": r["precision"], "lift": r["lift"]} for r in topk["rows"]], "label", "capture", "", "Top-K is a ranking diagnostic, not a staffing recommendation.")

    part7 = json.loads((root / "assets/data/part7_summary.json").read_text(encoding="utf-8"))
    p7e = part7["final_evidence"]
    p7p = part7["policy"]
    p7econ = part7.get("economics", {})
    charts["DE1"] = _available("DE1", "decision", "Final OOT decision mix", "bar", "assets/data/part7_summary.json", "SIMULATED", [
        {"label": "ALLOW", "rate": float(p7e["allow_rate"])},
        {"label": "REVIEW", "rate": float(p7e["review_rate"])},
        {"label": "BLOCK", "rate": float(p7e["block_rate"])},
    ], "label", "rate", "", "The locked policy intervenes on a small share of final OOT transactions; actions are simulated policy outputs.")
    charts["DE2"] = _available("DE2", "decision", "Review capacity vs realized review rate", "bar", "assets/data/part7_summary.json", "SIMULATED", [
        {"label": "Frozen review capacity", "rate": float(p7p["review_capacity"])},
        {"label": "Final OOT review rate", "rate": float(p7e["review_rate"])},
    ], "label", "rate", "", "Review is governed by a finite 1% capacity contract; realized OOT review usage remains below that ceiling.")
    charts["DE3"] = _available("DE3", "decision", "Final OOT fraud protection vs intervention", "bar", "assets/data/part7_summary.json", "SIMULATED", [
        {"label": "Fraud capture", "rate": float(p7e["fraud_capture"])},
        {"label": "Fraud exposure capture", "rate": float(p7e["fraud_exposure_capture"])},
        {"label": "Review + block intervention", "rate": float(p7e["review_rate"]) + float(p7e["block_rate"])},
    ], "label", "rate", "", "Final OOT shows material fraud/exposure capture at a low intervention rate, with temporal degradation retained rather than retuned away.")
    charts["DE4"] = _available("DE4", "decision", "Simulated policy economics vs ALLOW_ALL", "bar", "assets/data/part7_summary.json", "SIMULATED", [
        {"label": "ALLOW_ALL", "cost": float(p7econ.get("allow_all_cost", p7e.get("allow_all_simulated_total_cost", 0)))},
        {"label": "Selected policy", "cost": float(p7econ.get("selected_cost", p7e["simulated_total_cost"]))},
    ], "label", "cost", "", "The selected policy reduces assumption-driven simulated cost versus ALLOW_ALL; this is not booked or observed bank savings.")

    part8 = json.loads((root / "assets/data/part8_summary.json").read_text(encoding="utf-8"))
    p8perf = part8.get("performance", {})
    alerts = part8.get("alerts", {})
    charts["MON1"] = _available("MON1", "monitoring", "Final monitoring alert disposition", "bar", "assets/data/part8_summary.json", "GOVERNANCE", [
        {"label": "GREEN", "count": int(alerts.get("green", 0))},
        {"label": "BLOCKED / unsupported", "count": int(alerts.get("blocked", 0))},
    ], "label", "count", "", "Monitoring distinguishes supported green signals from blocked/unsupported signals rather than coercing missing evidence to zero.")
    charts["MON2"] = _blocked("MON2", "monitoring", "Action and review drift timeline", "assets/data/part8_summary.json", "GOVERNANCE", "A public aggregate time-series for action/review drift was not retained in the final website package.")
    charts["MON3"] = _available("MON3", "monitoring", "Matured final OOT model performance", "bar", "assets/data/part8_summary.json", "GOVERNANCE", [
        {"label": "PR-AUC", "value": p8perf.get("pr_auc")},
        {"label": "ROC-AUC", "value": p8perf.get("roc_auc")},
        {"label": "Brier", "value": p8perf.get("brier")},
        {"label": "Log loss", "value": p8perf.get("log_loss")},
        {"label": "ECE", "value": p8perf.get("ece")},
    ], "label", "value", "support", "Outcome metrics are evaluated only after labels are available; unsupported windows are not treated as zero performance.")

    return charts
