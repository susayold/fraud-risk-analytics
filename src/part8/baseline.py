from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .category_monitor import category_reference
from .contracts import OPERATIONAL
from .data_quality import quality_profile, quality_table
from .feature_monitor import build_reference
from .io import REPORT_DIR, ROOT, public_manifest, sha256_file, utc_now, write_csv, write_json
from .label_maturity import build_operational_view
from .lineage import frame_fingerprint
from .score_monitor import score_summary
from .windowing import assign_windows, window_summary


def _reference_frame(frame: pd.DataFrame) -> pd.DataFrame:
    split = frame.get("split_name", pd.Series("UNKNOWN", index=frame.index)).astype(str).str.upper()
    preferred = frame[split.isin({"VALIDATION", "VALIDATION_SELECTION", "P7_POLICY_CONFIRM"})]
    if not preferred.empty:
        return preferred.copy()
    return frame[~split.isin({"FINAL_OOT", "OOT", "OUT_OF_TIME_OOT"})].copy()


def build_baseline(frame: pd.DataFrame, config_dir: Path | None = None) -> dict:
    config_dir = config_dir or ROOT / "config" / "part8"
    frame = assign_windows(frame)
    operational = build_operational_view(frame.drop(columns=["fraud_label"], errors="ignore"))
    reference = _reference_frame(operational)
    if reference.empty:
        raise ValueError("No pre-OOT reference rows available")
    features = [c for c in ("amount", "risk_score", "channel", "MCC", "state_missing_flag", "pair_new", "cold_card", "new_merchant", "cross_community") if c in reference]
    ref_spec = build_reference(reference, features)
    baseline_id = f"P8_BASELINE_{frame.transaction_timestamp.min().strftime('%Y%m%d')}_{frame.transaction_timestamp.max().strftime('%Y%m%d')}"
    quality = quality_profile(reference, {"channel": category_reference(reference, "channel")["known_categories"]} if "channel" in reference else {})
    score = score_summary(reference) if "risk_score" in reference else {"n": 0}
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    write_json(REPORT_DIR / "reference_feature_distributions.json", ref_spec)
    write_csv(REPORT_DIR / "reference_feature_distributions.csv", pd.DataFrame([{"feature_name": name, "feature_type": "numerical", "reference_n": spec.get("reference_n", 0), "status": "PASS"} for name, spec in ref_spec.get("numerical", {}).items()] + [{"feature_name": name, "feature_type": "categorical", "reference_n": spec.get("reference_n", 0), "status": "PASS"} for name, spec in ref_spec.get("categorical", {}).items()]))
    write_csv(REPORT_DIR / "reference_window_summary.csv", window_summary(reference, "drift_window_id"))
    write_csv(REPORT_DIR / "reference_data_quality.csv", quality_table(quality))
    write_csv(REPORT_DIR / "reference_score_distribution.csv", pd.DataFrame([score]))
    write_csv(REPORT_DIR / "reference_performance.csv", pd.DataFrame([{"metric": "PR_AUC", "status": "BLOCKED", "label_mode": "OUTCOMES_MATURED", "support": "", "fraud_support": ""}]))
    write_json(REPORT_DIR / "reference_baseline_metadata.json", {"baseline_id": baseline_id, "reference_scope": "VALIDATION_SELECTION_OR_P7_POLICY_CONFIRM", "reference_row_count": len(reference), "reference_start": reference.transaction_timestamp.min().isoformat(), "reference_end": reference.transaction_timestamp.max().isoformat(), "feature_registry_hash": frame_fingerprint(reference[features]) if features else "EMPTY", "created_at_utc": utc_now(), "oot_used_for_threshold_calibration": False})
    write_json(REPORT_DIR / "alert_threshold_calibration.json", {"status": "CANDIDATES_ONLY", "threshold_source": "EMPIRICAL_PRE_OOT_BASELINE", "final_thresholds_frozen": False, "baseline_id": baseline_id})
    write_csv(REPORT_DIR / "alert_threshold_calibration.csv", pd.DataFrame([{"metric": "ALL", "threshold_source": "EMPIRICAL_PRE_OOT_BASELINE", "amber": None, "red": None, "persistence": "2_of_3", "status": "CANDIDATES_ONLY"}]))
    write_json(REPORT_DIR / "runtime_manifest.json", {"run_id": f"P8_BASELINE_RUN_{utc_now().replace(':','').replace('-','')}", "mode": "baseline", "input_hash": "not_persisted_in_public_snapshot", "baseline_id": baseline_id, "label_mode": OPERATIONAL, "rows": len(frame), "window_count": int(reference.drift_window_id.nunique()), "status": "BASELINE_READY", "started_at": utc_now(), "completed_at": utc_now()})
    write_csv(REPORT_DIR / "report_manifest.csv", public_manifest(baseline_id))
    return {"baseline_id": baseline_id, "reference": reference, "reference_spec": ref_spec, "quality": quality}
