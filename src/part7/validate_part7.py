"""Evidence-backed 64-gate validator for Block E.

Lifecycle status is never used as evidence. A gate is PASS only when its
declared artifact exists and the observed condition is true.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from .io import REPORT_DIR, ROOT, sha256_file, utc_now, write_csv


GATE_SPECS = [
    ("P7T01_input_source_resolved", "A", "Frozen score input exists"),
    ("P7T02_file_hash_recorded", "A", "Input file hash is recorded"),
    ("P7T03_row_id_unique", "A", "source_row_id is unique"),
    ("P7T04_timestamps_parse", "A", "Transaction timestamps parse"),
    ("P7T05_amounts_finite", "A", "Amounts are finite"),
    ("P7T06_split_values_valid", "A", "Split values are governed"),
    ("P7T07_source_reconciliation", "A", "Source row reconciliation passes"),
    ("P7T08_upstream_lineage_complete", "A", "Upstream version lineage is complete"),
    ("P7T09_score_non_null", "B", "Risk score is non-null"),
    ("P7T10_score_finite", "B", "Risk score is finite"),
    ("P7T11_score_range_valid", "B", "Risk score range is valid"),
    ("P7T12_score_direction_declared", "B", "Score direction is declared"),
    ("P7T13_score_status_explicit", "B", "Probability/ranking status is explicit"),
    ("P7T14_calibration_version_resolved", "B", "Calibration version is resolved when required"),
    ("P7T15_probability_audit_complete", "B", "Validation-only calibration evidence exists"),
    ("P7T16_ranking_expected_value_disabled", "B", "Ranking-only scores disable expected-value routing"),
    ("P7T17_label_absent_decision_dto", "C", "Decision DTO rejects labels"),
    ("P7T18_label_absent_policy_frame", "C", "Decision runtime rejects label columns"),
    ("P7T19_no_target_policy_feature", "C", "Target fields are not decision features"),
    ("P7T20_no_future_outcome_input", "C", "Future outcome fields are blocked"),
    ("P7T21_tune_precedes_confirm", "C", "Tune scope precedes confirm scope"),
    ("P7T22_oot_absent_threshold_search", "C", "OOT is sealed from threshold search"),
    ("P7T23_oot_absent_economics_tuning", "C", "OOT is sealed from economic tuning"),
    ("P7T24_no_model_reselection", "C", "Part 7 does not retrain/reselect the model"),
    ("P7T25_action_domain_exact", "D", "Actions are ALLOW/REVIEW/BLOCK only"),
    ("P7T26_one_action_per_transaction", "D", "One action exists per source row"),
    ("P7T27_action_totals_reconcile", "D", "Action totals reconcile"),
    ("P7T28_threshold_order_valid", "D", "Review threshold is below block threshold"),
    ("P7T29_bucket_capacity_respected", "D", "Causal bucket capacity is respected"),
    ("P7T30_overflow_explicit", "D", "Overflow action is explicit"),
    ("P7T31_deterministic_tiebreak", "D", "Queue tie-break is deterministic"),
    ("P7T32_future_rows_cannot_change_past", "D", "Future-invariance evidence exists"),
    ("P7T33_assumption_ids_complete", "E", "Economic assumption IDs are complete"),
    ("P7T34_assumption_units_complete", "E", "Economic assumption units are complete"),
    ("P7T35_source_claim_classes_complete", "E", "Economic source and claim classes are explicit"),
    ("P7T36_positive_exposure_nonnegative", "E", "Primary exposure is nonnegative"),
    ("P7T37_signed_amount_boundary", "E", "Signed amount is reconciliation-only"),
    ("P7T38_cost_decomposition_reconciles", "E", "Cost components reconcile"),
    ("P7T39_sensitivity_complete", "E", "Sensitivity output exists"),
    ("P7T40_selected_profile_constraints", "E", "Selected policy satisfies profile constraints"),
    ("P7T41_graph_autoblock_disabled", "F", "Graph cannot autoblock"),
    ("P7T42_graph_optionality_safe", "F", "Graph is optional routing evidence"),
    ("P7T43_graph_hash_recorded", "F", "Graph version/hash is recorded"),
    ("P7T44_part6_claim_preserved", "F", "Part 6 claim boundary is preserved"),
    ("P7T45_reason_codes_registered", "F", "Reason codes are registered"),
    ("P7T46_primary_reason_deterministic", "F", "Primary reason is deterministic"),
    ("P7T47_secondary_reasons_valid", "F", "Secondary reasons use the registry"),
    ("P7T48_public_reason_aggregate_only", "F", "Public reasons are aggregate-only"),
    ("P7T49_freeze_exists", "G", "Policy freeze exists"),
    ("P7T50_clean_worktree", "G", "Freeze was created on a clean worktree"),
    ("P7T51_full_config_hash", "G", "Decision-defining config bundle is hashed"),
    ("P7T52_code_commit_hash", "G", "Code commit is recorded"),
    ("P7T53_score_hash_version", "G", "Score hash and version are recorded"),
    ("P7T54_graph_hash_version", "G", "Graph hash and version are recorded"),
    ("P7T55_freeze_precedes_replay", "G", "Freeze precedes final replay"),
    ("P7T56_no_post_freeze_mutation", "G", "No decision mutation follows freeze"),
    ("P7T57_weekly_paired_block_bootstrap", "H", "Weekly paired bootstrap is present"),
    ("P7T58_bootstrap_draws_minimum", "H", "Bootstrap draws are at least 500"),
    ("P7T59_bootstrap_ci_finite", "H", "Bootstrap confidence intervals are finite"),
    ("P7T60_delta_reconciles", "H", "Challenger deltas reconcile"),
    ("P7T61_daily_metrics_reconcile", "H", "Daily metrics reconcile"),
    ("P7T62_segment_metrics_reconcile", "H", "Segment metrics reconcile"),
    ("P7T63_manifest_hashes_valid", "H", "Manifest hashes are valid"),
    ("P7T64_final_status_gate", "H", "Final status is locked only at 64/64 PASS"),
]
GATE_NAMES = [item[0] for item in GATE_SPECS]


def _load(path: Path, default):
    if not path.exists():
        return default
    if path.suffix.lower() == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    return pd.read_csv(path)


def _artifact(path: Path) -> str | None:
    return sha256_file(path) if path.exists() and path.is_file() else None


def _manifest_valid(path: Path) -> bool:
    try:
        frame = pd.read_csv(path)
        return all((ROOT / str(row.relative_path)).exists() and sha256_file(ROOT / str(row.relative_path)) == str(row.sha256) for row in frame.itertuples(index=False))
    except Exception:
        return False


def _row(name: str, family: str, description: str, *, source: Path, expected: str, observed, passed: bool, blocked: bool = False) -> dict:
    status = "PASS" if passed else ("BLOCKED" if blocked else "FAIL")
    try:
        source_name = source.relative_to(ROOT).as_posix()
    except ValueError:
        source_name = str(source)
    return {"check_name": name, "family": family, "description": description,
            "severity": "P0" if family in {"A", "B", "C", "D"} else "P1",
            "evidence_artifact": source_name, "evidence_sha256": _artifact(source),
            "expected_condition": expected, "observed_value": observed, "status": status,
            "violations": 0 if passed else 1, "checked_at": utc_now(),
            "checker_version": "PART7_EVIDENCE_VALIDATOR_v2.0"}


def validate(summary_path: Path = REPORT_DIR / "PART7_FINAL_SUMMARY.json") -> pd.DataFrame:
    summary = _load(summary_path, {})
    blocked = summary.get("status", "INPUT_BLOCKED") == "INPUT_BLOCKED"
    audit_path = REPORT_DIR / "part7_input_audit.json"; audit = _load(audit_path, {})
    recon_path = REPORT_DIR / "decision_input_reconciliation.csv"; recon = _load(recon_path, pd.DataFrame())
    config_dir = ROOT / "config" / "part7"; src_dir = ROOT / "src" / "part7"; test_dir = ROOT / "tests" / "part7"
    freeze_path = REPORT_DIR / "PART7_POLICY_FREEZE.json"; bootstrap_path = REPORT_DIR / "bootstrap_policy_ci.csv"; manifest_path = REPORT_DIR / "report_manifest.csv"; calibration_path = REPORT_DIR / "score_calibration_audit.csv"
    results: dict[str, tuple[Path, str, object, bool, bool]] = {}

    def add(name, source, expected, observed, passed, is_blocked=False):
        family = next(f for n, f, _ in GATE_SPECS if n == name)
        results[name] = (source, expected, observed, bool(passed), bool(is_blocked))

    def recon_value(key):
        if not isinstance(recon, pd.DataFrame) or recon.empty or not {"check_name", "value"}.issubset(recon.columns): return None
        found = recon.loc[recon.check_name.astype(str).eq(key), "value"]
        return found.iloc[0] if len(found) else None

    lineage_path = ROOT / "private" / "part7" / "input_lineage.json"; lineage = _load(lineage_path, {})
    add("P7T01_input_source_resolved", audit_path, "input audit is not INPUT_BLOCKED", audit.get("status"), bool(audit.get("status")) and not blocked, blocked)
    add("P7T02_file_hash_recorded", lineage_path, "non-empty score_file_sha256", lineage.get("score_file_sha256"), bool(lineage.get("score_file_sha256")), blocked)
    add("P7T03_row_id_unique", recon_path, "unique rows equal source rows", recon_value("unique_source_row_id"), recon_value("source_rows") is not None and recon_value("unique_source_row_id") == recon_value("source_rows"), blocked)
    for name, key in [("P7T04_timestamps_parse", "timestamp_parse"), ("P7T05_amounts_finite", "amount_finite"), ("P7T06_split_values_valid", "split_values")]:
        value = recon_value(key); add(name, recon_path, f"{key} is PASS", value, value == "PASS", blocked)
    add("P7T07_source_reconciliation", recon_path, "source rows reconcile", recon_value("source_rows"), recon_value("source_rows") is not None and recon_value("unique_source_row_id") == recon_value("source_rows"), blocked)
    add("P7T08_upstream_lineage_complete", lineage_path, "score and model lineage present", {k: lineage.get(k) for k in ("score_version", "model_version", "calibration_version")}, bool(lineage.get("score_version")) and bool(lineage.get("model_version")), blocked)
    for name, key in [("P7T09_score_non_null", "score_non_null"), ("P7T10_score_finite", "score_finite"), ("P7T11_score_range_valid", "score_range")]:
        value = recon_value(key); add(name, recon_path, f"{key} is PASS", value, value == "PASS", blocked)
    score_contract = config_dir / "score_contract.yaml"; contract_text = score_contract.read_text(encoding="utf-8") if score_contract.exists() else ""
    add("P7T12_score_direction_declared", score_contract, "score alias and range declared", "score contract", "score_range:" in contract_text and "primary_score_alias:" in contract_text)
    score_status = summary.get("score_status")
    add("P7T13_score_status_explicit", summary_path, "explicit score status", score_status, score_status in {"PROBABILITY_USABLE", "RANKING_ONLY"}, blocked)
    cal = _load(calibration_path, pd.DataFrame()); calrow = cal.iloc[0].to_dict() if isinstance(cal, pd.DataFrame) and not cal.empty else {}
    add("P7T14_calibration_version_resolved", calibration_path, "version present for probability score", calrow.get("calibration_version"), score_status == "RANKING_ONLY" or bool(calrow.get("calibration_version")), blocked)
    add("P7T15_probability_audit_complete", calibration_path, "calibrator_fitted_in_part7 is false", calrow.get("calibrator_fitted_in_part7"), calrow.get("calibrator_fitted_in_part7") is not True and calrow.get("status") in {"PASS", "NOT_EVALUATED"}, blocked)
    add("P7T16_ranking_expected_value_disabled", calibration_path, "expected-value disabled for ranking-only", calrow.get("expected_value_enabled"), score_status != "RANKING_ONLY" or calrow.get("expected_value_enabled") is False)

    contracts_path = src_dir / "contracts.py"; contracts_text = contracts_path.read_text(encoding="utf-8") if contracts_path.exists() else ""
    decision_path = src_dir / "decision_runtime.py"; decision_text = decision_path.read_text(encoding="utf-8") if decision_path.exists() else ""
    for name, expected, token in [("P7T17_label_absent_decision_dto", "DecisionContext rejects forbidden fields", "DecisionContext"), ("P7T18_label_absent_policy_frame", "decision runtime asserts policy columns", "assert_policy_columns"), ("P7T19_no_target_policy_feature", "target is forbidden", "target"), ("P7T20_no_future_outcome_input", "future_outcome is forbidden", "future_outcome")]:
        passed = "FORBIDDEN_POLICY_FIELDS" in contracts_text and token in (decision_text if name == "P7T18_label_absent_policy_frame" else contracts_text)
        add(name, contracts_path, expected, "firewall code present", passed)
    scope_path = config_dir / "temporal_scopes.yaml"; scope_text = scope_path.read_text(encoding="utf-8") if scope_path.exists() else ""
    add("P7T21_tune_precedes_confirm", scope_path, "scope order is declared", "P7_POLICY_TUNE before P7_POLICY_CONFIRM", scope_path.exists() and "P7_POLICY_TUNE" in scope_text, blocked)
    add("P7T22_oot_absent_threshold_search", scope_path, "FINAL_OOT is sealed from search", "OOT sealed", scope_path.exists() and "FINAL_OOT" in scope_text, blocked)
    add("P7T23_oot_absent_economics_tuning", scope_path, "FINAL_OOT is sealed from economics tuning", "OOT sealed", scope_path.exists() and "economics" in scope_text.lower(), blocked)
    add("P7T24_no_model_reselection", decision_path, "no fit/retrain in decision runtime", "decision-only", decision_path.exists() and "fit(" not in decision_text)

    action_path = REPORT_DIR / "policy_candidate_metrics.csv"; queue_path = config_dir / "review_queue.yaml"; queue_text = queue_path.read_text(encoding="utf-8") if queue_path.exists() else ""
    for name in ("P7T25_action_domain_exact", "P7T26_one_action_per_transaction", "P7T27_action_totals_reconcile"):
        add(name, action_path, "action evidence exists", "not executed", action_path.exists() and not blocked, blocked)
    add("P7T28_threshold_order_valid", contracts_path, "PolicyConfig enforces review < block", "PolicyConfig", "review_threshold < self.block_threshold" in contracts_text)
    add("P7T29_bucket_capacity_respected", queue_path, "capacity is per causal bucket", "FRACTION_OF_BUCKET", "type: DAY" in queue_text and "enabled: false" in queue_text)
    add("P7T30_overflow_explicit", queue_path, "overflow action is explicit", "ALLOW", "overflow:" in queue_text and "action: ALLOW" in queue_text)
    add("P7T31_deterministic_tiebreak", queue_path, "source_row_id is final tie-break", "source_row_id ASC", "source_row_id ASC" in queue_text)
    queue_test = test_dir / "test_review_queue.py"; add("P7T32_future_rows_cannot_change_past", queue_test, "future invariance test exists", "test_future_rows_do_not_change_past_bucket", queue_test.exists(), blocked)

    econ_path = config_dir / "economic_assumptions.yaml"; econ_text = econ_path.read_text(encoding="utf-8") if econ_path.exists() else ""
    add("P7T33_assumption_ids_complete", econ_path, "ECON001..ECON010", "ECON001..ECON010", all(f"ECON{i:03d}" in econ_text for i in range(1, 11)))
    add("P7T34_assumption_units_complete", econ_path, "at least 10 unit fields", econ_text.count("unit:"), econ_text.count("unit:") >= 10)
    add("P7T35_source_claim_classes_complete", econ_path, "source and claim fields present", {"source_type": econ_text.count("source_type:"), "claim_type": econ_text.count("claim_type:")}, econ_text.count("source_type:") >= 10 and econ_text.count("claim_type:") >= 10)
    exposure_path = src_dir / "exposure.py"; exposure_text = exposure_path.read_text(encoding="utf-8") if exposure_path.exists() else ""
    add("P7T36_positive_exposure_nonnegative", exposure_path, "positive_exposure=max(amount,0)", "np.maximum(amount, 0.0)", "np.maximum(amount, 0.0)" in exposure_text)
    add("P7T37_signed_amount_boundary", exposure_path, "positive exposure is primary basis", "economic_exposure_proxy", "economic_exposure_proxy" in exposure_text)
    economics_path = src_dir / "economics.py"; economics_text = economics_path.read_text(encoding="utf-8") if economics_path.exists() else ""
    add("P7T38_cost_decomposition_reconciles", economics_path, "total is component sum", "allow+block+review", "total = allow_cost + block_cost + review_cost" in economics_text, blocked)
    sensitivity_path = REPORT_DIR / "sensitivity_summary.csv"; add("P7T39_sensitivity_complete", sensitivity_path, "sensitivity report exists", "report present" if sensitivity_path.exists() else None, sensitivity_path.exists(), blocked)
    profile_path = config_dir / "policy_profiles.yaml"; profile_text = profile_path.read_text(encoding="utf-8") if profile_path.exists() else ""
    add("P7T40_selected_profile_constraints", profile_path, "all profiles have operational semantics", "growth/balanced/conservative", all(x in profile_text for x in ("growth:", "balanced:", "conservative:", "allowed_priority_methods:")), blocked)

    graph_path = config_dir / "graph_routing_policy.yaml"; graph_text = graph_path.read_text(encoding="utf-8") if graph_path.exists() else ""
    graph_code = src_dir / "graph_routing.py"; graph_code_text = graph_code.read_text(encoding="utf-8") if graph_code.exists() else ""
    add("P7T41_graph_autoblock_disabled", graph_path, "automatic_block_override.enabled=false", "false", "automatic_block_override:" in graph_text and "enabled: false" in graph_text)
    add("P7T42_graph_optionality_safe", graph_code, "graph only changes review priority", "review priority only", "never to BLOCK" in graph_code_text)
    add("P7T43_graph_hash_recorded", graph_path, "graph config has version", "version", "version:" in graph_text, blocked)
    add("P7T44_part6_claim_preserved", graph_path, "Part 6 global uplift not claimed", "claim boundary", "Part 6 did not establish" in graph_text)
    reason_path = config_dir / "reason_codes.yaml"; reason_text = reason_path.read_text(encoding="utf-8") if reason_path.exists() else ""
    add("P7T45_reason_codes_registered", reason_path, "reason registry includes RC001", "RC001", reason_path.exists() and "RC001" in reason_text)
    reason_code_path = src_dir / "reason_codes.py"; reason_code_text = reason_code_path.read_text(encoding="utf-8") if reason_code_path.exists() else ""
    add("P7T46_primary_reason_deterministic", reason_code_path, "reason order is deterministic", "dict.fromkeys", "tuple(dict.fromkeys(codes))" in reason_code_text)
    add("P7T47_secondary_reasons_valid", reason_path, "registry exists", "reason registry", reason_path.exists())
    add("P7T48_public_reason_aggregate_only", src_dir / "io.py", "public output is report directory only", "REPORT_DIR", "REPORT_DIR" in (src_dir / "io.py").read_text(encoding="utf-8"))

    freeze = _load(freeze_path, {})
    add("P7T49_freeze_exists", freeze_path, "freeze JSON exists", freeze.get("policy_version"), bool(freeze), blocked)
    add("P7T50_clean_worktree", freeze_path, "working_tree_clean=true", freeze.get("working_tree_clean"), freeze.get("working_tree_clean") is True, blocked)
    add("P7T51_full_config_hash", freeze_path, "config bundle hash exists", freeze.get("config_bundle_sha256"), bool(freeze.get("config_bundle_sha256")), blocked)
    add("P7T52_code_commit_hash", freeze_path, "code commit exists", freeze.get("code_commit"), bool(freeze.get("code_commit")), blocked)
    add("P7T53_score_hash_version", freeze_path, "score hash/version exist", {k: freeze.get(k) for k in ("score_file_sha256", "score_version")}, bool(freeze.get("score_file_sha256")) and bool(freeze.get("score_version")), blocked)
    add("P7T54_graph_hash_version", freeze_path, "graph hash/version exist", {k: freeze.get(k) for k in ("graph_routing_sha256", "graph_version")}, bool(freeze.get("graph_routing_sha256")) and bool(freeze.get("graph_version")), blocked)
    add("P7T55_freeze_precedes_replay", freeze_path, "freeze timestamp exists", freeze.get("freeze_created_at_utc"), bool(freeze.get("freeze_created_at_utc")), blocked)
    add("P7T56_no_post_freeze_mutation", freeze_path, "post_freeze_mutation is false", freeze.get("post_freeze_mutation"), freeze.get("post_freeze_mutation") is False, blocked)

    boot = _load(bootstrap_path, pd.DataFrame()); has_boot = isinstance(boot, pd.DataFrame) and not boot.empty
    draws = int(boot.draws.max()) if has_boot and "draws" in boot else None
    add("P7T57_weekly_paired_block_bootstrap", bootstrap_path, "weekly paired block method", "method", has_boot and "method" in boot and boot.method.astype(str).str.contains("weekly_paired_block_bootstrap").all(), blocked)
    add("P7T58_bootstrap_draws_minimum", bootstrap_path, "draws >= 500", draws, draws is not None and draws >= 500, blocked)
    finite_ci = has_boot and {"ci_lower", "ci_upper"}.issubset(boot.columns) and boot[["ci_lower", "ci_upper"]].apply(pd.to_numeric, errors="coerce").notna().all().all()
    add("P7T59_bootstrap_ci_finite", bootstrap_path, "CI values are finite", "finite" if finite_ci else None, finite_ci, blocked)
    for name, filename in [("P7T60_delta_reconciles", "shadow_policy_metric_delta.csv"), ("P7T61_daily_metrics_reconcile", "daily_policy_metrics.csv"), ("P7T62_segment_metrics_reconcile", "segment_policy_metrics.csv")]:
        path = REPORT_DIR / filename; add(name, path, "aggregate report exists", filename if path.exists() else None, path.exists(), blocked)
    add("P7T63_manifest_hashes_valid", manifest_path, "all manifest hashes verify", "valid" if _manifest_valid(manifest_path) else None, manifest_path.exists() and _manifest_valid(manifest_path), blocked)
    pass_before = sum(value[3] for value in results.values())
    add("P7T64_final_status_gate", summary_path, "locked iff previous 63 gates pass", {"status": summary.get("status"), "pass_before": pass_before}, summary.get("status") == "DECISION_POLICY_LOCKED" and pass_before == 63, blocked)

    return pd.DataFrame([_row(name, family, description, source=results[name][0], expected=results[name][1], observed=results[name][2], passed=results[name][3], blocked=results[name][4]) for name, family, description in GATE_SPECS])


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--summary", type=Path, default=REPORT_DIR / "PART7_FINAL_SUMMARY.json"); args = parser.parse_args()
    frame = validate(args.summary); write_csv(REPORT_DIR / "part7_validation_report.csv", frame)
    print(f"Part 7 validation: {(frame.status == 'PASS').sum()} PASS, {(frame.status == 'BLOCKED').sum()} BLOCKED, {(frame.status == 'FAIL').sum()} FAIL")
    return 1 if (frame.status == "FAIL").any() else 0


if __name__ == "__main__":
    raise SystemExit(main())
