"""Run the resource-safe Part 5.1 logistic baseline.

This runner reads an already-built Part 4 evaluation view from a temporary
DuckDB database, keeps row-level matrices private, and publishes aggregate
evidence only. It intentionally does not access OOT scoring in P5.1.
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

from build_modeling_population import build_population
from common import (
    CALIBRATION_CONTRACT_VERSION,
    CURRENT_FEATURES,
    FRONTEND_CONTRACT_VERSION,
    MODEL_CONTRACT_VERSION,
    REPORT_DIR,
    SEED,
    SUMMARY_PATH,
    assert_feature_contract,
    calibration_bins,
    feature_sets,
    make_preprocessor,
    safe_binary_metrics,
    sample_weights,
    sha256_file,
    temporal_fold_masks,
    topk_rows,
    write_csv,
)

VALIDATION_FIELDS = ["model_name", "feature_set", "evaluation_scope", "rows", "fraud_rows", "pr_auc", "roc_auc", "ks", "brier", "log_loss", "status"]
TOPK_FIELDS = ["model_name", "feature_set", "evaluation_scope", "top_k", "selected_rows", "fraud_captured", "fraud_capture_rate", "precision", "lift"]


def public_clean() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    for path in REPORT_DIR.glob("*"):
        if path.is_file():
            path.unlink()
    SUMMARY_PATH.unlink(missing_ok=True)


def git_metadata(root: Path) -> tuple[str, bool]:
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=False).stdout.strip() or "UNKNOWN"
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=root, text=True, capture_output=True, check=False).stdout.splitlines()
    generated = ("reports/part5/", "assets/data/part5_summary.json")
    clean = not any(len(line) >= 4 and not line[3:].replace("\\", "/").startswith(generated) for line in dirty)
    return commit, clean


def fit_pipeline(train: pd.DataFrame, features: list[str], c_value: float, weight_full: int, weight_sample: int):
    assert_feature_contract(train, features)
    pre = make_preprocessor(train, features)
    model = LogisticRegression(C=c_value, penalty="l2", solver="liblinear", max_iter=1000, random_state=SEED)
    from sklearn.pipeline import Pipeline
    pipe = Pipeline([("preprocess", pre), ("model", model)])
    weights = sample_weights(train["fraud_label"], weight_full, weight_sample)
    pipe.fit(train[features], train["fraud_label"].astype(int), model__sample_weight=weights)
    return pipe


def write_manifest(run_meta: dict) -> None:
    fields = ["filename", "sha256", "size_bytes", "run_id", "code_commit", "contract_version", "generated_at"]
    rows = []
    for path in sorted(REPORT_DIR.iterdir()):
        if path.suffix not in {".csv", ".json"} or path.name in {"report_manifest.csv", "part5_validation_report.csv"}:
            continue
        rows.append({"filename": path.relative_to(ROOT).as_posix(), "sha256": sha256_file(path), "size_bytes": path.stat().st_size, "run_id": run_meta["run_id"], "code_commit": run_meta["code_commit"], "contract_version": MODEL_CONTRACT_VERSION, "generated_at": run_meta["run_timestamp_utc"]})
    with (REPORT_DIR / "report_manifest.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(rows)


def load_matrix(db_path: Path, private_manifest: Path) -> pd.DataFrame:
    db = duckdb.connect(str(db_path), read_only=True)
    try:
        manifest = pd.read_csv(private_manifest)
        db.register("p5_private_targets", manifest[["source_row_id", "modeling_scope"]])
        return db.execute("""
          SELECT e.*, t.modeling_scope
          FROM analytics.part4_evaluation_v1 e
          JOIN p5_private_targets t USING(source_row_id)
          ORDER BY e.transaction_timestamp, e.source_row_id
        """).df()
    finally:
        db.close()


def model_feature_importance(pipe, model_name: str, feature_set: str) -> list[dict]:
    names = pipe.named_steps["preprocess"].get_feature_names_out()
    coef = pipe.named_steps["model"].coef_[0]
    order = np.argsort(-np.abs(coef))[:15]
    return [{"model_name": model_name, "feature_set": feature_set, "feature_name": str(names[i]), "coefficient": float(coef[i]), "absolute_coefficient": float(abs(coef[i])), "interpretation": "predictive association; not causal"} for i in order]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--private-dir", type=Path, required=True)
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--memory-limit", default="2GB")
    parser.add_argument("--code-commit")
    parser.add_argument("--clean-generated", action="store_true")
    args = parser.parse_args()
    if not args.database.exists():
        raise SystemExit(f"Database not found: {args.database}")
    if args.clean_generated:
        public_clean()
    started = time.perf_counter(); args.private_dir.mkdir(parents=True, exist_ok=True)
    code_commit, working_tree_clean = git_metadata(ROOT)
    code_commit = args.code_commit or code_commit
    run_meta = {"run_id": f"P5-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}", "code_commit": code_commit, "working_tree_clean": working_tree_clean, "run_timestamp_utc": datetime.now(timezone.utc).isoformat(), "model_contract_version": MODEL_CONTRACT_VERSION, "calibration_contract_version": CALIBRATION_CONTRACT_VERSION, "frontend_contract_version": FRONTEND_CONTRACT_VERSION, "threads": args.threads, "memory_limit": args.memory_limit, "database_source": "temporary offline database (not published)", "execution_scope": "P5.1_LOGISTIC_VALIDATION_WINDOW_ONLY"}

    population = build_population(args.database, args.private_dir, REPORT_DIR)
    frame = load_matrix(args.database, Path(population["manifest_path"]))
    sets = feature_sets(); dev = frame[frame.modeling_scope == "DEVELOPMENT_TRAIN"].copy(); calibration = frame[frame.modeling_scope == "VALIDATION_CALIBRATION"].copy(); selection = frame[frame.modeling_scope == "VALIDATION_SELECTION"].copy()
    if dev.empty or calibration.empty or selection.empty:
        raise SystemExit("P5.1 requires non-empty Development training and two Validation periods")
    for name, features in sets.items():
        if name in {"F0", "F2"}:
            assert_feature_contract(frame, features)

    full_legit = population["full_development_legitimate_rows"]; sampled_legit = population["sampled_development_legitimate_rows"]
    cv_rows=[]; boundaries=[]; importance=[]; predictions={}; validation_metrics=[]; calibration_metric_rows=[]; calibration_bin_rows=[]; topk=[]
    for feature_set_name in ("F0", "F2"):
        features=sets[feature_set_name]
        for fold_train, fold_valid, meta in temporal_fold_masks(dev, 3):
            boundaries.append({"feature_set":feature_set_name, **meta, "train_rows":int(fold_train.sum()), "validation_rows":int(fold_valid.sum())})
            pipe=fit_pipeline(dev.loc[fold_train], features, 1.0, full_legit, sampled_legit)
            score=pipe.predict_proba(dev.loc[fold_valid][features])[:,1]
            metrics=safe_binary_metrics(dev.loc[fold_valid]["fraud_label"].to_numpy(), score)
            cv_rows.append({"model_name":"Logistic Regression","feature_set":feature_set_name,"fold":meta["fold"],**metrics,"selection_scope":"DEVELOPMENT temporal CV","status":"PASS" if metrics["pr_auc"] is not None else "LOW_SUPPORT"})
        pipe=fit_pipeline(dev, features, 1.0, full_legit, sampled_legit)
        calibration_score=pipe.predict_proba(calibration[features])[:,1]; selection_score=pipe.predict_proba(selection[features])[:,1]
        predictions[feature_set_name]=selection_score
        importance.extend(model_feature_importance(pipe,"Logistic Regression",feature_set_name))
        y_cal=calibration.fraud_label.astype(int).to_numpy(); y_sel=selection.fraud_label.astype(int).to_numpy()
        for method in ("uncalibrated","sigmoid","isotonic"):
            if method == "uncalibrated":
                calibrated=selection_score
            elif method == "sigmoid":
                cal=LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000, random_state=SEED); cal.fit(calibration_score.reshape(-1,1), y_cal); calibrated=cal.predict_proba(selection_score.reshape(-1,1))[:,1]
            else:
                cal=IsotonicRegression(out_of_bounds="clip"); cal.fit(calibration_score, y_cal); calibrated=cal.predict(selection_score)
            metric=safe_binary_metrics(y_sel, selection_score, calibrated)
            calibration_metric_rows.append({"model_name":"Logistic Regression","feature_set":feature_set_name,"method":method,"fit_scope":"VALIDATION_CALIBRATION","evaluation_scope":"VALIDATION_SELECTION",**metric,"status":"PASS" if metric["brier"] is not None else "LOW_SUPPORT"})
            if method == "sigmoid":
                predictions[feature_set_name+"_calibrated"]=calibrated
                calibration_bin_rows.extend([{**row,"model_name":"Logistic Regression","feature_set":feature_set_name,"method":method} for row in calibration_bins(y_sel, calibrated)])
        raw_metric=safe_binary_metrics(y_sel, selection_score, predictions[feature_set_name+"_calibrated"])
        validation_metrics.append({"model_name":"Logistic Regression","feature_set":feature_set_name,"evaluation_scope":"VALIDATION_SELECTION","status":"PASS" if raw_metric["pr_auc"] is not None else "LOW_SUPPORT",**raw_metric})
        topk.extend([{**row,"model_name":"Logistic Regression","feature_set":feature_set_name,"evaluation_scope":"VALIDATION_SELECTION"} for row in topk_rows(y_sel, selection_score)])

    val_frame=pd.DataFrame(validation_metrics); champion_row=val_frame.sort_values(["pr_auc","feature_set"],ascending=[False,True]).iloc[0].to_dict() if not val_frame.empty and val_frame.pr_auc.notna().any() else None
    f0=val_frame[val_frame.feature_set=="F0"].iloc[0].to_dict(); f2=val_frame[val_frame.feature_set=="F2"].iloc[0].to_dict()
    incremental={"evaluation_scope":"VALIDATION_SELECTION","model_name":"Logistic Regression","current_only_feature_set":"F0","current_plus_behavioral_feature_set":"F2","delta_pr_auc":(f2["pr_auc"]-f0["pr_auc"]) if f2["pr_auc"] is not None and f0["pr_auc"] is not None else None,"delta_roc_auc":(f2["roc_auc"]-f0["roc_auc"]) if f2["roc_auc"] is not None and f0["roc_auc"] is not None else None,"delta_ks":(f2["ks"]-f0["ks"]) if f2["ks"] is not None and f0["ks"] is not None else None,"delta_top1_capture":None,"status":"PASS" if champion_row else "PENDING"}
    selection_rows=[]
    for row in val_frame.to_dict("records"):
        row.update({"complexity_rank":1,"eligibility":"ELIGIBLE","selection_status":"CHAMPION_CANDIDATE" if champion_row and row["feature_set"]==champion_row["feature_set"] else "BASELINE","reason":"Validation PR-AUC comparison; OOT not accessed."})
        selection_rows.append(row)
    feature_audit=[]
    for feature_set_name, features in sets.items():
        for feature_name in features:
            feature_audit.append({"feature_set":feature_set_name,"feature_name":feature_name,"status":"PASS","forbidden_input":False,"fit_scope":"DEVELOPMENT","unknown_category_policy":"ignore" if feature_name in {"use_chip","merchant_category_code"} else "not_applicable"})
    write_csv(REPORT_DIR/"feature_registry_audit.csv",feature_audit)
    write_csv(REPORT_DIR/"development_cv_boundaries.csv",boundaries)
    write_csv(REPORT_DIR/"cv_model_results.csv",cv_rows)
    write_csv(REPORT_DIR/"validation_model_metrics.csv",validation_metrics,VALIDATION_FIELDS)
    write_csv(REPORT_DIR/"calibration_metrics.csv",calibration_metric_rows)
    write_csv(REPORT_DIR/"calibration_bins.csv",calibration_bin_rows)
    write_csv(REPORT_DIR/"validation_topk_capture.csv",topk,TOPK_FIELDS)
    write_csv(REPORT_DIR/"model_selection_report.csv",selection_rows)
    write_csv(REPORT_DIR/"feature_importance.csv",importance)
    write_csv(REPORT_DIR/"rule_baseline_metrics.csv",[],["model_name","feature_set","evaluation_scope","status","notes"])
    write_csv(REPORT_DIR/"oot_model_metrics.csv",[],VALIDATION_FIELDS)
    write_csv(REPORT_DIR/"oot_topk_capture.csv",[],TOPK_FIELDS)
    write_csv(REPORT_DIR/"oot_bootstrap_ci.csv",[],["model_name","metric","block_unit","draws","successful_draws","seed","estimate","ci_lower","ci_upper","status"])
    write_csv(REPORT_DIR/"subgroup_performance.csv",[],["subgroup","evaluation_scope","rows","fraud_rows","pr_auc","status","notes"])
    write_csv(REPORT_DIR/"shap_summary.csv",[],["feature_name","mean_abs_shap","sample_rows","status","notes"])
    write_csv(REPORT_DIR/"oot_access_log.csv",[],["timestamp","code_commit","model_version","reason","action"])
    write_csv(REPORT_DIR/"runtime_profile.csv",[{"stage":"population_and_matrix","rows":len(frame),"elapsed_seconds":round(time.perf_counter()-started,3),"threads":args.threads,"memory_limit":args.memory_limit,"status":"PASS"}])
    runtime={**run_meta,"status":"CHAMPION_SELECTED" if champion_row else "MODELING_IN_PROGRESS","validation_status":"PASS" if champion_row else "PENDING","pipeline_elapsed_seconds":round(time.perf_counter()-started,3),"oot_accessed":False,"raw_publication":False,"private_manifest_sha256":population["manifest_sha256"]}
    (REPORT_DIR/"runtime_manifest.json").write_text(json.dumps(runtime,indent=2,ensure_ascii=False),encoding="utf-8")
    write_manifest(run_meta)
    summary={"status":"CHAMPION_SELECTED" if champion_row else "MODELING_IN_PROGRESS","lock_status":"NOT_LOCKED","model_contract_version":MODEL_CONTRACT_VERSION,"calibration_contract_version":CALIBRATION_CONTRACT_VERSION,"frontend_contract_version":FRONTEND_CONTRACT_VERSION,"execution":{"scope":"P5.1_LOGISTIC_VALIDATION_WINDOW_ONLY","target_rows":int(len(frame)),"development_training_rows":int(len(dev)),"validation_calibration_rows":int(len(calibration)),"validation_selection_rows":int(len(selection)),"oot_rows_manifested":int((frame.modeling_scope=="OOT_EVALUATION_WINDOW").sum()),"source_population_rows":None,"representative_sample_claim":False,"full_population_model_run":False,"raw_publication":False},"splits":{"development":{"role":"training_plus_temporal_cv","date_start":dev.transaction_timestamp.min(),"date_end":dev.transaction_timestamp.max()},"validation":{"role":"calibration_plus_selection","date_start":frame[frame.split_name=="VALIDATION"].transaction_timestamp.min(),"date_end":frame[frame.split_name=="VALIDATION"].transaction_timestamp.max(),"window_days":365},"oot":{"role":"final_frozen_evaluation","accessed":False,"window_days":365}},"feature_sets":[{"name":"F0","label":"Current Context","feature_count":len(CURRENT_FEATURES),"features":CURRENT_FEATURES},{"name":"F1","label":"Behavioral","feature_count":len(sets["F1"]),"features":sets["F1"]},{"name":"F2","label":"Current + Behavioral","feature_count":len(sets["F2"]),"features":sets["F2"]}],"rules":{"status":"NOT_RUN","count":0},"models":[{"name":"Logistic Regression","version":"PART5_LOGISTIC_v1.0","feature_sets":["F0","F2"],"status":"CHAMPION_CANDIDATE" if champion_row else "PENDING","preprocessing":"Development-fit median imputation + missing indicators; OneHotEncoder(handle_unknown=ignore)"}],"validation_metrics":validation_metrics,"calibration":{"contract_version":CALIBRATION_CONTRACT_VERSION,"fit_scope":"VALIDATION_CALIBRATION","metrics":calibration_metric_rows,"bins":calibration_bin_rows},"topk":topk,"incremental_value":incremental,"oot_metrics":[],"subgroups":[],"feature_importance":importance,"champion":{"status":"CHAMPION_SELECTED" if champion_row else "PENDING","model_name":"Logistic Regression" if champion_row else None,"feature_set":champion_row["feature_set"] if champion_row else None,"selection_scope":"VALIDATION_SELECTION" if champion_row else None,"reason":"Highest Validation PR-AUC among the executed logistic F0/F2 comparison; final OOT lock is pending." if champion_row else None},"validation":{"status":"PASS" if champion_row else "PENDING","stage":"P5.1_LOGISTIC_BASELINE","oot_final_evaluation":"NOT_RUN","checks":{}},"governance":{"sampling_policy":"all Development fraud + deterministic quarter-stratified legitimate sample up to 20:1","primary_metric":"PR-AUC","forbidden_inputs":list(__import__('common').FORBIDDEN_FEATURE_TOKENS),"no_random_split":True,"no_oot_tuning":True,"no_final_decision_policy":True,"not_claimed":["full-population behavioral model","causality","loss prevented","production performance","ALLOW/REVIEW/BLOCK threshold"]},"findings":[] ,"run":runtime}
    SUMMARY_PATH.write_text(json.dumps(summary,indent=2,ensure_ascii=False,default=str),encoding="utf-8")
    validator = subprocess.run([sys.executable, str(ROOT / "src" / "part5" / "validate_part5.py"), "--summary", str(SUMMARY_PATH)], cwd=ROOT, text=True, check=False)
    if validator.returncode != 0:
        raise SystemExit("Part 5 validation failed; summary is not approved for publication.")
    validation_report = REPORT_DIR / "part5_validation_report.csv"
    if validation_report.exists():
        with validation_report.open(encoding="utf-8", newline="") as handle:
            summary["validation"]["checks"] = {row["check_name"]: row["status"] for row in csv.DictReader(handle)}
        SUMMARY_PATH.write_text(json.dumps(summary,indent=2,ensure_ascii=False,default=str),encoding="utf-8")
    print(json.dumps({"status":summary["status"],"lock_status":summary["lock_status"],"validation_rows":len(validation_metrics),"elapsed_seconds":runtime["pipeline_elapsed_seconds"]}))


ROOT = Path(__file__).resolve().parents[2]

if __name__ == "__main__":
    main()
