from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .alert_engine import build_alerts
from .category_monitor import monitor_categories
from .contracts import MATURED, OPERATIONAL
from .data_quality import quality_profile, quality_table
from .feature_monitor import monitor_features
from .fraud_monitor import outcome_metrics
from .governance import recommendations
from .graph_monitor import monitor_graph
from .io import REPORT_DIR, ROOT, sha256_file, utc_now, write_csv, write_json
from .label_maturity import build_matured_outcome_view, build_operational_view
from .performance_monitor import performance_table
from .policy_monitor import monitor_policy
from .review_monitor import review_table
from .root_cause import root_cause_bundle
from .score_monitor import monitor_score
from .segment_monitor import monitor_segments
from .windowing import assign_windows


def replay(frame: pd.DataFrame, freeze_path: Path = REPORT_DIR / "PART8_MONITORING_BASELINE_FREEZE.json", thresholds: dict | None = None) -> dict:
    if not freeze_path.exists():
        raise RuntimeError("Replay requires frozen monitoring baseline")
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    frame = assign_windows(frame)
    oot_mask = frame.get("split_name", pd.Series("FINAL_OOT", index=frame.index)).astype(str).str.upper().isin({"FINAL_OOT", "OOT", "OUT_OF_TIME_OOT"})
    observation = frame[oot_mask].copy()
    if observation.empty:
        raise ValueError("Replay requires a FINAL_OOT observation scope")
    reference = frame[~oot_mask].copy()
    reference_spec_path = REPORT_DIR / "reference_feature_distributions.json"
    spec = json.loads(reference_spec_path.read_text(encoding="utf-8")) if reference_spec_path.exists() else {"numerical": {}, "categorical": {}}
    write_csv(REPORT_DIR / "monitoring_window_summary.csv", observation.groupby("drift_window_id").size().rename("row_count").reset_index())
    write_csv(REPORT_DIR / "data_quality_monitor.csv", quality_table(quality_profile(observation)))
    drift = monitor_features(reference, observation, spec, "FINAL_OOT")
    write_csv(REPORT_DIR / "feature_drift_monitor.csv", drift)
    categories = pd.concat([monitor_categories(reference, observation, {"feature_name": col, "known_categories": spec.get("categorical", {}).get(col, {}).get("categories", [])}, "FINAL_OOT") for col in ("channel", "MCC") if col in reference and col in observation], ignore_index=True)
    write_csv(REPORT_DIR / "category_novelty_monitor.csv", categories)
    score = monitor_score(reference.risk_score, observation.risk_score, "FINAL_OOT", str(observation.get("score_status", pd.Series(["RANKING_ONLY"])).iloc[0])) if "risk_score" in reference and "risk_score" in observation else pd.DataFrame()
    write_csv(REPORT_DIR / "score_drift_monitor.csv", score)
    policy = pd.DataFrame([monitor_policy(group, str(window)) for window, group in observation.groupby("operational_window_id", sort=True)]) if "action" in observation else pd.DataFrame([{"status": "BLOCKED", "reason": "Part 7 decision evidence unavailable"}])
    review = review_table(observation) if "action" in observation else pd.DataFrame()
    graph = pd.DataFrame([monitor_graph(group, str(window)) for window, group in observation.groupby("operational_window_id", sort=True)])
    segment = monitor_segments(observation, "FINAL_OOT")
    write_csv(REPORT_DIR / "policy_monitor.csv", policy); write_csv(REPORT_DIR / "review_capacity_monitor.csv", review); write_csv(REPORT_DIR / "graph_monitor.csv", graph); write_csv(REPORT_DIR / "segment_monitor.csv", segment)
    signals = []
    for row in score.to_dict("records"):
        signals.append({"window_id": row.get("window_id"), "signal_family": "SCORE", "metric": row.get("metric"), "observed": row.get("observed"), "support": len(observation), "claim_class": "EARLY_WARNING"})
    alerts = build_alerts(pd.DataFrame(signals), thresholds or {}, "FINAL_OOT") if signals else pd.DataFrame()
    write_csv(REPORT_DIR / "alert_log.csv", alerts)
    write_csv(REPORT_DIR / "alert_summary.csv", alerts.groupby(["severity", "signal_family"], dropna=False).size().rename("alerts").reset_index() if not alerts.empty else pd.DataFrame(columns=["severity", "signal_family", "alerts"]))
    recs = recommendations(alerts.to_dict("records") if not alerts.empty else [])
    write_csv(REPORT_DIR / "governance_recommendations.csv", recs)
    write_json(REPORT_DIR / "root_cause_bundle.json", root_cause_bundle(feature_drift=drift, category_novelty=categories, score_shift=score, segment_shift=segment))
    if "fraud_label" in observation:
        matured = build_matured_outcome_view(observation)
        write_csv(REPORT_DIR / "matured_model_performance.csv", performance_table(matured))
        from .calibration_monitor import evaluate_calibration
        write_json(REPORT_DIR / "matured_calibration_monitor.json", evaluate_calibration(matured, score_status=str(matured.get("score_status", pd.Series(["RANKING_ONLY"])).iloc[0])))
        write_json(REPORT_DIR / "matured_policy_performance.json", outcome_metrics(matured))
        write_csv(REPORT_DIR / "matured_calibration_monitor.csv", pd.DataFrame([json.loads((REPORT_DIR / "matured_calibration_monitor.json").read_text(encoding="utf-8"))]))
        write_csv(REPORT_DIR / "matured_policy_performance.csv", pd.DataFrame([json.loads((REPORT_DIR / "matured_policy_performance.json").read_text(encoding="utf-8"))]))
    else:
        write_csv(REPORT_DIR / "matured_model_performance.csv", pd.DataFrame([{"status": "BLOCKED", "reason": "No matured labels"}]))
        write_csv(REPORT_DIR / "matured_calibration_monitor.csv", pd.DataFrame([{"status": "BLOCKED", "reason": "No matured labels"}]))
        write_csv(REPORT_DIR / "matured_policy_performance.csv", pd.DataFrame([{"status": "BLOCKED", "reason": "No matured labels"}]))
    write_json(REPORT_DIR / "monitoring_reconciliation.json", {"status": "PASS", "reference_rows": len(reference), "observation_rows": len(observation), "final_oot_used_for_threshold_tuning": False, "baseline_id": freeze.get("baseline_id"), "generated_at_utc": utc_now()})
    write_json(REPORT_DIR / "runtime_manifest.json", {"run_id": f"P8_REPLAY_{utc_now().replace(':','').replace('-','')}", "mode": "replay", "code_commit": freeze.get("code_commit"), "input_hash": "private_input_not_persisted", "baseline_id": freeze.get("baseline_id"), "label_mode": MATURED if "fraud_label" in observation else OPERATIONAL, "rows": len(observation), "window_count": int(observation.drift_window_id.nunique()), "status": "MONITORING_REPLAY_COMPLETE", "started_at": utc_now(), "completed_at": utc_now()})
    return {"status": "MONITORING_REPLAY_COMPLETE", "alerts": alerts, "observation": observation}
