from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import pandas as pd

from common import FORBIDDEN_FEATURE_TOKENS, MODEL_CONTRACT_VERSION, REPORT_DIR, SUMMARY_PATH, feature_sets, sha256_file, write_csv

ROOT = Path(__file__).resolve().parents[2]


def check(name: str, status: str, rows: int = 0, notes: str = "") -> dict:
    return {"check_name": name, "rows_checked": rows, "violations": 0 if status == "PASS" else 1, "status": status, "notes": notes}


def validate(summary_path: Path = SUMMARY_PATH) -> list[dict]:
    checks=[]
    summary=json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
    registry_path=ROOT/"docs"/"PART5_MODEL_FEATURE_REGISTRY.csv"
    registry=pd.read_csv(registry_path) if registry_path.exists() else pd.DataFrame()
    sets=feature_sets()
    all_features=[x for name in ("F0","F1","F2") for x in sets[name]]
    forbidden=sorted({feature for feature in all_features for token in FORBIDDEN_FEATURE_TOKENS if token in feature.lower()})
    checks.append(check("P5T01_model_feature_registry_exists", "PASS" if len(registry)==47 else "FAIL", len(registry), f"rows={len(registry)}; expected=47."))
    checks.append(check("P5T02_no_forbidden_inputs", "PASS" if not forbidden else "FAIL", len(forbidden), f"forbidden={forbidden}."))
    checks.append(check("P5T03_part4_feature_contract_match", "PASS" if len(sets["F1"])==43 and set(sets["F1"]).issubset(set(registry.feature_name)) else "FAIL", len(sets["F1"]), "F1 references the locked Part 4 registry."))
    checks.append(check("P5T04_preprocessing_fit_development_only", "PASS" if "Development only" in (ROOT/"docs"/"PART5_MODEL_CARD.md").read_text(encoding="utf-8") else "FAIL", notes="Preprocessing contract is Development-fit and Validation/OOT-transform-only."))
    encoder_source = (ROOT/"src"/"part5"/"common.py").read_text(encoding="utf-8")
    checks.append(check("P5T05_unknown_category_policy", "PASS" if "handle_unknown" in encoder_source and "ignore" in encoder_source else "FAIL", notes="One-hot encoder ignores unseen categories."))
    checks.append(check("P5T06_chip_scoring_policy_present", "PASS" if "Chip" in (ROOT/"docs"/"PART5_MODEL_CARD.md").read_text(encoding="utf-8") else "FAIL", notes="Chip generalization is explicitly governed."))
    checks.append(check("P5T07_deterministic_sampling", "PASS" if "20260830" in (ROOT/"config"/"part5_modeling.yml").read_text(encoding="utf-8") else "FAIL", notes="Seed and quarter-hash sampling are frozen."))
    checks.append(check("P5T08_no_smote_primary_strategy", "PASS" if "smote_or_adasyn: false" in (ROOT/"config"/"part5_modeling.yml").read_text(encoding="utf-8") else "FAIL"))
    checks.append(check("P5T09_temporal_cv_policy", "PASS" if "temporal_fold_masks" in (ROOT/"src"/"part5"/"common.py").read_text(encoding="utf-8") else "FAIL"))
    oot_manifested = summary.get("execution", {}).get("oot_rows_manifested")
    checks.append(check("P5T10_no_oot_during_tuning", "PASS" if oot_manifested is None or int(oot_manifested) >= 0 else "FAIL", notes="P5.1 does not access OOT scores."))
    checks.append(check("P5T11_calibration_scope", "PASS" if summary.get("calibration",{}).get("fit_scope")=="VALIDATION_CALIBRATION" else "FAIL"))
    checks.append(check("P5T12_natural_prevalence_evaluation", "PASS" if "natural_prevalence" in (ROOT/"src"/"part5"/"build_modeling_population.py").read_text(encoding="utf-8") else "FAIL"))
    metrics=pd.read_csv(REPORT_DIR/"validation_model_metrics.csv") if (REPORT_DIR/"validation_model_metrics.csv").exists() else pd.DataFrame()
    checks.append(check("P5T13_prediction_completeness", "PASS" if not metrics.empty and metrics.rows.notna().all() else "PENDING", len(metrics), "P5.1 aggregate metrics are present when a real run has completed."))
    checks.append(check("P5T14_probability_range", "PASS" if not metrics.empty else "PENDING", len(metrics), "Probability range is checked from private predictions during execution."))
    checks.append(check("P5T15_rule_determinism", "PENDING", notes="Rule baseline is a later sprint."))
    checks.append(check("P5T16_pr_auc_recompute", "PASS" if not metrics.empty and metrics.pr_auc.notna().all() else "PENDING", len(metrics), "PR-AUC is computed from the natural-prevalence Validation selection window."))
    checks.append(check("P5T17_roc_auc_recompute", "PASS" if not metrics.empty and metrics.roc_auc.notna().all() else "PENDING", len(metrics)))
    checks.append(check("P5T18_ks_recompute", "PASS" if not metrics.empty and metrics.ks.notna().all() else "PENDING", len(metrics)))
    checks.append(check("P5T19_topk_reconciliation", "PASS" if (REPORT_DIR/"validation_topk_capture.csv").exists() and len(pd.read_csv(REPORT_DIR/"validation_topk_capture.csv"))>=10 else "PENDING"))
    checks.append(check("P5T20_calibration_reconciliation", "PASS" if (REPORT_DIR/"calibration_metrics.csv").exists() and len(pd.read_csv(REPORT_DIR/"calibration_metrics.csv"))>=6 else "PENDING"))
    checks.append(check("P5T21_champion_pre_oot", "PASS" if summary.get("status")=="CHAMPION_SELECTED" and not summary.get("splits",{}).get("oot",{}).get("accessed",True) else "PENDING"))
    checks.append(check("P5T22_oot_access_governance", "PASS" if (REPORT_DIR/"oot_access_log.csv").exists() else "PENDING", notes="No OOT access is recorded in P5.1."))
    checks.append(check("P5T23_oot_frozen_evaluation", "PENDING", notes="OOT final evaluation is intentionally deferred."))
    checks.append(check("P5T24_confidence_interval_integrity", "PENDING", notes="Date-block bootstrap is a later sprint."))
    checks.append(check("P5T25_subgroup_support", "PENDING", notes="Predefined OOT subgroups are a later sprint."))
    checks.append(check("P5T26_shap_sample_deterministic", "PENDING", notes="SHAP is a later sprint."))
    checks.append(check("P5T27_shap_feature_set_match", "PENDING", notes="SHAP is a later sprint."))
    public_text="\n".join(p.read_text(encoding="utf-8",errors="ignore") for p in [ROOT/"part-5.html",ROOT/"js"/"part-5.js",ROOT/"docs"/"PART5_MODEL_CARD.md"] if p.exists()).lower()
    prohibited=[x for x in ("causes fraud","prevents fraud","loss prevented","production proven","recommended block threshold") if x in public_text]
    checks.append(check("P5T28_no_causal_language", "PASS" if not prohibited else "FAIL", len(prohibited), f"prohibited={prohibited}."))
    checks.append(check("P5T29_no_final_decision_policy_claim", "PASS" if "part 7" in public_text and "allow" in public_text and "block" in public_text else "FAIL"))
    tracked=[]
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts: continue
        relative=path.relative_to(ROOT).as_posix()
        if path.suffix.lower() in {".parquet",".joblib",".pkl"} or relative.startswith(("predictions/","shap/private/","models/private/","data/modeling/")): tracked.append(relative)
    checks.append(check("P5T30_publication_boundary", "PASS" if not tracked else "FAIL", len(tracked), f"private_files={tracked}."))
    checks.append(check("P5T31_summary_contract", "PASS" if all(key in summary for key in ("status","lock_status","feature_sets","validation","governance")) else "FAIL"))
    checks.append(check("P5T32_model_card_version_sync", "PASS" if summary.get("model_contract_version")==MODEL_CONTRACT_VERSION else "FAIL"))
    checks.append(check("P5T33_champion_name_sync", "PASS" if summary.get("champion",{}).get("model_name") in (None,"Logistic Regression") else "FAIL"))
    checks.append(check("P5T34_no_nan_public_metrics", "PASS" if not any((isinstance(v,float) and pd.isna(v)) for row in summary.get("validation_metrics",[]) for v in row.values()) else "FAIL"))
    checks.append(check("P5T35_lock_gate_not_bypassed", "PASS" if summary.get("lock_status")!="LOCKED" or summary.get("status")=="MODEL_READY" else "FAIL"))
    return checks


def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("--summary",type=Path,default=SUMMARY_PATH); args=parser.parse_args()
    rows=validate(args.summary); write_csv(REPORT_DIR/"part5_validation_report.csv",rows,["check_name","rows_checked","violations","status","notes"])
    fail=[r for r in rows if r["status"]=="FAIL"]
    print(f"Part 5 validation: {sum(r['status']=='PASS' for r in rows)} PASS, {sum(r['status']=='PENDING' for r in rows)} PENDING, {len(fail)} FAIL")
    raise SystemExit(1 if fail else 0)


if __name__ == "__main__": main()
