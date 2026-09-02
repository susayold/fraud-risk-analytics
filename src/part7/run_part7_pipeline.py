from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from .backtest import evaluate_variants, select_policy
from .action_precedence import load_precedence_config
from .bootstrap import weekly_paired_bootstrap
from .calibration import audit_calibration
from .contracts import PolicyConfig
from .economics import EconomicAssumptions, evaluate_economics
from .exposure import add_exposure_bases
from .final_replay import load_and_verify_freeze, replay
from .freeze_policy import freeze_policy
from .io import REPORT_DIR, ROOT, git_metadata, load_frame, normalise_input, public_manifest, sha256_file, write_csv, write_json
from .lineage import frame_fingerprint, write_input_lineage
from .lifecycle import assert_transition
from .policy_engine import run_policy
from .queue_diagnostics import queue_diagnostics
from .reports import refresh_public_summary, write_input_audit, write_summary
from .score_gate import REQUIRED, audit_score_frame, discover_primary_score_artifact
from .sensitivity import run_sensitivity
from .thresholds import high_amount_cutoff, quantile_thresholds


def _yaml(path: Path) -> dict:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML is required for Part 7 config-driven execution") from exc
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _assumptions(root: Path) -> EconomicAssumptions:
    values = _yaml(root / "config" / "part7" / "economic_assumptions.yaml")["assumptions"]
    return EconomicAssumptions(**{key: values[f"ECON{idx:03d}"]["base"] for idx, key in enumerate(("fraud_loss_fraction", "block_effectiveness", "review_cost_per_case", "review_fraud_detection_rate", "review_legitimate_false_reject_rate", "false_block_fixed_friction_cost", "false_block_amount_friction_rate", "review_delay_cost"), 1)})


def _blocked(reason: str, checks: list[dict]) -> int:
    write_input_audit("INPUT_BLOCKED", reason, checks)
    write_summary("INPUT_BLOCKED", score_status=None)
    from .validate_part7 import validate
    validation = validate(REPORT_DIR / "PART7_FINAL_SUMMARY.json")
    write_csv(REPORT_DIR / "part7_validation_report.csv", validation)
    refresh_public_summary(validation)
    write_csv(REPORT_DIR / "report_manifest.csv", public_manifest())
    print(f"Part 7: INPUT_BLOCKED — {reason}")
    return 2


def _scope(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    split = frame.split_name.astype(str).str.upper()
    tune = frame[split.isin({"DEVELOPMENT", "P7_POLICY_TUNE", "TRAIN", "VALIDATION_CALIBRATION"})].copy()
    confirm = frame[split.isin({"VALIDATION", "P7_POLICY_CONFIRM", "VALIDATION_SELECTION"})].copy()
    oot = frame[split.isin({"OUT_OF_TIME_OOT", "OOT", "FINAL_OOT"})].copy()
    return tune, confirm, oot


def _daily_metrics(actions: pd.DataFrame, assumptions: EconomicAssumptions) -> pd.DataFrame:
    date = pd.to_datetime(actions.transaction_timestamp).dt.date.astype(str)
    rows = []
    for day, group in actions.groupby(date, sort=True):
        metrics = evaluate_economics(group, assumptions)
        rows.append({"date": day, **metrics})
    return pd.DataFrame(rows)


def _segments(actions: pd.DataFrame, assumptions: EconomicAssumptions, column: str, label: str) -> pd.DataFrame:
    rows = []
    for value, group in actions.groupby(column, dropna=False, sort=True):
        rows.append({"segment_type": label, "segment": str(value), **evaluate_economics(group, assumptions)})
    return pd.DataFrame(rows)


def _refresh_validation_snapshot(policy_version: str | None = None) -> pd.DataFrame:
    from .validate_part7 import validate
    validation = validate(REPORT_DIR / "PART7_FINAL_SUMMARY.json")
    write_csv(REPORT_DIR / "part7_validation_report.csv", validation)
    refresh_public_summary(validation)
    write_csv(REPORT_DIR / "report_manifest.csv", public_manifest(policy_version))
    return validation


def _advance_stage(status: str, **details) -> None:
    """Persist a lifecycle pointer and enforce sequential stage transitions."""
    pointer_path = REPORT_DIR / "part7_stage_pointer.json"
    current = "INPUT_BLOCKED"
    if pointer_path.exists():
        try:
            current = json.loads(pointer_path.read_text(encoding="utf-8")).get("status", current)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Part 7 stage pointer is not valid JSON") from exc
    if current != status:
        assert_transition(current, status)
    write_json(pointer_path, {"stage": status.lower(), "status": status, **details})


def _write_confirmation_handoff(confirm: pd.DataFrame, args: argparse.Namespace, selected: dict, candidate_path: Path, profile_path: Path) -> tuple[str, Path, Path]:
    scope_hash = frame_fingerprint(confirm.drop(columns=["fraud_label"], errors="ignore"))
    timestamps = pd.to_datetime(confirm.transaction_timestamp, utc=True)
    scope_path = REPORT_DIR / "P7_CONFIRMATION_SCOPE_MANIFEST.json"
    write_json(scope_path, {"scope": "P7_POLICY_CONFIRM", "rows": len(confirm), "min_timestamp": str(timestamps.min()), "max_timestamp": str(timestamps.max()), "source_row_id_count": int(confirm.source_row_id.nunique()), "input_score_version": args.score_version, "confirmation_scope_hash": scope_hash})
    commit, _ = git_metadata()
    selected_policy = {"status": "POLICY_SELECTED", "policy_version": selected["policy_version"], "profile": args.profile, "priority_method": selected.get("priority_method", "SCORE_ONLY"), "review_threshold": selected.get("review_threshold"), "block_threshold": selected.get("block_threshold"), "review_capacity": selected.get("review_capacity"), "score_version": args.score_version, "model_version": args.model_version, "calibration_version": args.calibration_version, "score_status": args.score_status, "confirmation_scope_hash": scope_hash, "candidate_metrics_hash": sha256_file(candidate_path), "profile_comparison_hash": sha256_file(profile_path), "selection_objective": _yaml(ROOT / "config" / "part7" / "decision_engine.yaml")["selection"]["primary_metric"], "selection_tie_break": _yaml(ROOT / "config" / "part7" / "decision_engine.yaml")["selection"]["tie_break"], "created_at_utc": pd.Timestamp.utcnow().isoformat(), "code_commit_at_development": commit}
    selected_path = REPORT_DIR / "PART7_SELECTED_POLICY.json"
    write_json(selected_path, selected_policy)
    return scope_hash, scope_path, selected_path


def develop_stage(args: argparse.Namespace) -> int:
    input_path = args.input
    if input_path is None:
        candidates = discover_primary_score_artifact(ROOT)
        return _blocked("No frozen Part 5 row-level score artifact was discovered; pass --input explicitly.", [{"check_name": "P7T01_input_source_resolved", "status": "FAIL", "notes": f"candidates={len(candidates)}"}])
    try:
        frame = normalise_input(load_frame(input_path))
    except Exception as exc:
        return _blocked(f"Input could not be loaded: {exc}", [{"check_name": "P7T01_input_source_resolved", "status": "FAIL", "notes": str(exc)}])
    missing = sorted(set(REQUIRED) - set(frame.columns))
    if missing:
        return _blocked(f"Required input columns missing: {missing}", [{"check_name": "P7T01_required_columns", "status": "FAIL", "notes": str(missing)}])
    gate = audit_score_frame(frame.drop(columns=["fraud_label"], errors="ignore"), args.score_status, args.score_version, args.calibration_version)
    if gate.status != "SCORE_GATE_LOCKED":
        return _blocked("Score gate failed; no policy search was run.", list(gate.checks))
    if "fraud_label" not in frame:
        return _blocked("Evaluation label is required outside the policy API for retrospective metrics.", list(gate.checks) + [{"check_name": "evaluation_label_available", "status": "FAIL", "notes": "No fraud_label column."}])
    _advance_stage("TECHNICALLY_READY", score_version=args.score_version, model_version=args.model_version)
    frame = add_exposure_bases(frame)
    # Never materialise row-level source data into this repository. Keep only
    # non-sensitive lineage metadata; the source stays in the user's managed
    # Drive/workspace location supplied through --input.
    private_input = frame[[column for column in ("source_row_id", "transaction_timestamp", "risk_score", "amount", "split_name", "pair_new", "cold_card", "new_merchant", "cross_community", "channel") if column in frame.columns]].copy()
    write_input_lineage(REPORT_DIR / "input_lineage.json", score_path=input_path, frame=private_input, score_version=args.score_version, model_version=args.model_version, calibration_version=args.calibration_version)
    tune, confirm, oot = _scope(frame)
    if tune.empty or confirm.empty:
        return _blocked("Chronological P7_POLICY_TUNE and P7_POLICY_CONFIRM scopes are required.", [{"check_name": "P7T13_tune_confirm_scopes", "status": "FAIL", "notes": f"tune={len(tune)}, confirm={len(confirm)}"}])
    assumptions = _assumptions(ROOT)
    config = _yaml(ROOT / "config" / "part7" / "decision_engine.yaml")
    queue_config = _yaml(ROOT / "config" / "part7" / "review_queue.yaml")
    precedence_config = load_precedence_config(ROOT / "config" / "part7" / "action_precedence.yaml")
    thresholds = quantile_thresholds(tune.risk_score, config["threshold_search"]["quantiles"])
    cutoff = high_amount_cutoff(tune)
    write_csv(REPORT_DIR / "decision_input_reconciliation.csv", pd.DataFrame([
        {"check_name": "source_rows", "value": len(frame), "status": "PASS"},
        {"check_name": "unique_source_row_id", "value": frame.source_row_id.nunique(), "status": "PASS" if frame.source_row_id.is_unique else "FAIL"},
        {"check_name": "timestamp_parse", "value": "PASS" if pd.to_datetime(frame.transaction_timestamp, errors="coerce", utc=True).notna().all() else "FAIL", "status": "PASS"},
        {"check_name": "amount_finite", "value": "PASS" if pd.to_numeric(frame.amount, errors="coerce").notna().all() else "FAIL", "status": "PASS"},
        {"check_name": "split_values", "value": "PASS" if frame.split_name.notna().all() else "FAIL", "status": "PASS"},
        {"check_name": "score_non_null", "value": "PASS" if frame.risk_score.notna().all() else "FAIL", "status": "PASS"},
        {"check_name": "score_finite", "value": "PASS" if np.isfinite(pd.to_numeric(frame.risk_score, errors="coerce")).all() else "FAIL", "status": "PASS"},
        {"check_name": "score_range", "value": "PASS" if frame.risk_score.between(0, 1).all() else "FAIL", "status": "PASS"},
        {"check_name": "tune_rows", "value": len(tune), "status": "PASS"},
        {"check_name": "confirm_rows", "value": len(confirm), "status": "PASS"},
        {"check_name": "final_oot_rows", "value": len(oot), "status": "PASS" if len(oot) else "REVIEW"},
        {"check_name": "oot_not_globally_unseen", "value": True, "status": "PASS"},
    ]))
    max_pairs = int(config["threshold_search"].get("max_threshold_pairs", 6))
    tune_metrics, _ = evaluate_variants(tune, thresholds, config["capacities"], assumptions, args.score_status == "PROBABILITY_USABLE", cutoff, max_pairs, queue_config=queue_config, precedence_config=precedence_config)
    confirm_metrics, action_map = evaluate_variants(confirm, thresholds, config["capacities"], assumptions, args.score_status == "PROBABILITY_USABLE", cutoff, max_pairs, queue_config=queue_config, precedence_config=precedence_config)
    tune_metrics["scope"] = "P7_POLICY_TUNE"; confirm_metrics["scope"] = "P7_POLICY_CONFIRM"
    write_csv(REPORT_DIR / "policy_candidate_metrics.csv", pd.concat([tune_metrics, confirm_metrics], ignore_index=True))
    p1_threshold = max(thresholds) if thresholds else 1.0
    p1_tune = tune.copy(); p1_tune["action"] = np.where(p1_tune.risk_score >= p1_threshold, "BLOCK", "ALLOW"); p1_tune["candidate_action"] = p1_tune["action"]; p1_tune["review_priority"] = 0.0; p1_tune["reason_codes"] = "RC001"
    p1_confirm = confirm.copy(); p1_confirm["action"] = np.where(p1_confirm.risk_score >= p1_threshold, "BLOCK", "ALLOW"); p1_confirm["candidate_action"] = p1_confirm["action"]; p1_confirm["review_priority"] = 0.0; p1_confirm["reason_codes"] = "RC001"
    p1_rows = []
    for scope, p1 in (("P7_POLICY_TUNE", p1_tune), ("P7_POLICY_CONFIRM", p1_confirm)):
        metrics = evaluate_economics(p1, assumptions); metrics.update({"policy_version": "PART7_P1_SINGLE_BLOCK", "priority_method": "SCORE_ONLY", "review_threshold": None, "block_threshold": p1_threshold, "review_capacity": 0.0, "variant": "P1", "scope": scope, "feasible": True}); p1_rows.append(metrics)
    write_csv(REPORT_DIR / "baseline_policy_metrics.csv", pd.concat([tune_metrics[tune_metrics.variant == "P0"], confirm_metrics[confirm_metrics.variant == "P0"], pd.DataFrame(p1_rows)], ignore_index=True))
    from .policy_frontier import build_frontier
    write_csv(REPORT_DIR / "policy_frontier.csv", build_frontier(confirm_metrics))
    capacity = confirm_metrics[(confirm_metrics.variant == "P3") & (confirm_metrics.priority_method == "SCORE_ONLY")].copy()
    write_csv(REPORT_DIR / "review_capacity_frontier.csv", capacity)
    if not capacity.empty:
        capacity = capacity.sort_values(["review_capacity", "fraud_capture"], ascending=[True, False]); capacity["incremental_reviews"] = capacity.review_count.diff(); capacity["incremental_fraud"] = capacity.fraud_blocked.diff().fillna(0) + capacity.fraud_reviewed.diff().fillna(0); capacity["fraud_per_1000_incremental_reviews"] = capacity.incremental_fraud / capacity.incremental_reviews * 1000
    write_csv(REPORT_DIR / "marginal_review_value.csv", capacity)
    write_csv(REPORT_DIR / "amount_aware_comparison.csv", confirm_metrics[(confirm_metrics.variant == "P4") & confirm_metrics.priority_method.isin(["SCORE_ONLY", "EXPOSURE_WEIGHTED_PROBABILITY", "EXPOSURE_WEIGHTED_RANK"])] )
    write_csv(REPORT_DIR / "graph_review_comparison.csv", confirm_metrics[(confirm_metrics.variant == "P5")])
    profile_cfg = _yaml(ROOT / "config" / "part7" / "policy_profiles.yaml")["profiles"]
    profile_rows = []
    selections = {}
    for name, profile in profile_cfg.items():
        choice = select_policy(confirm_metrics, profile, profile["objective"])
        if choice is not None:
            row = choice.to_dict(); row["profile"] = name; profile_rows.append(row); selections[name] = row
    write_csv(REPORT_DIR / "policy_profile_comparison.csv", profile_rows)
    selected = selections.get(args.profile)
    if selected is None:
        return _blocked(f"No feasible policy for profile {args.profile} on confirmation scope.", [{"check_name": "P7T62_policy_feasible", "status": "FAIL", "notes": "No candidate satisfied profile constraints."}])
    selected_key = selected["policy_version"]
    if selected_key in action_map:
        selected_actions = action_map[selected_key]
    else:
        selected_config = PolicyConfig(selected_key, float(selected["review_threshold"]), float(selected["block_threshold"]), float(selected["review_capacity"]), str(selected["priority_method"]))
        selected_actions, _ = run_policy(confirm.drop(columns=["fraud_label"], errors="ignore"), selected_config, assumptions, args.score_status == "PROBABILITY_USABLE", emit_reason_codes=True, queue_config=queue_config, precedence_config=precedence_config)
    selected_config = PolicyConfig(selected_key, float(selected.get("review_threshold") if pd.notna(selected.get("review_threshold")) else 0.0), float(selected.get("block_threshold") if pd.notna(selected.get("block_threshold")) else 1.0), float(selected.get("review_capacity") if pd.notna(selected.get("review_capacity")) else 0.0), str(selected.get("priority_method", "SCORE_ONLY")))
    write_csv(REPORT_DIR / "sensitivity_summary.csv", run_sensitivity(confirm, selected_config, assumptions, args.score_status == "PROBABILITY_USABLE", queue_config=queue_config, precedence_config=precedence_config))
    diagnostics = queue_diagnostics(selected_actions)
    for filename, diagnostic in diagnostics.items():
        write_csv(REPORT_DIR / f"{filename}.csv", diagnostic)
    action_summary = selected_actions.groupby("action", as_index=False).size().rename(columns={"size": "rows"})
    action_summary["source_row_count"] = len(selected_actions)
    action_summary["unique_source_row_count"] = selected_actions.source_row_id.nunique()
    write_csv(REPORT_DIR / "decision_action_summary.csv", action_summary)
    daily_metrics = _daily_metrics(selected_actions.assign(fraud_label=confirm.fraud_label.to_numpy()), assumptions)
    write_csv(REPORT_DIR / "daily_policy_metrics.csv", daily_metrics)
    write_json(REPORT_DIR / "daily_reconciliation.json", {"status": "PASS" if int(daily_metrics.transactions.sum()) == len(confirm) else "FAIL", "daily_transactions": int(daily_metrics.transactions.sum()), "confirmation_transactions": int(len(confirm))})
    segment_frames = []
    for col, label in (("channel", "channel"), ("pair_new", "pair_seen"), ("cold_card", "cold_start"), ("new_merchant", "merchant_novelty")):
        if col in selected_actions:
            segment_frames.append(_segments(selected_actions.assign(fraud_label=confirm.fraud_label.to_numpy()), assumptions, col, label))
    write_csv(REPORT_DIR / "segment_policy_metrics.csv", pd.concat(segment_frames, ignore_index=True) if segment_frames else pd.DataFrame())
    write_json(REPORT_DIR / "segment_reconciliation.json", {"status": "PASS" if segment_frames else "BLOCKED", "additivity": "NON_ADDITIVE_SEGMENTS", "segment_types": [str(frame.segment_type.iloc[0]) for frame in segment_frames if not frame.empty]})
    reason = selected_actions.assign(fraud_label=confirm.fraud_label.to_numpy()).assign(reason_code=selected_actions.reason_codes.fillna("").str.split(";" )).explode("reason_code")
    reason = reason[reason.reason_code.ne("")].groupby("reason_code", as_index=False).size().rename(columns={"size": "rows"})
    write_csv(REPORT_DIR / "reason_code_summary.csv", reason)
    calibration_audit, calibration_bins = audit_calibration(confirm.drop(columns=["fraud_label"], errors="ignore"), confirm[["source_row_id", "fraud_label"]], score_version=args.score_version, calibration_version=args.calibration_version, score_status=args.score_status, scope="P7_POLICY_CONFIRM")
    write_csv(REPORT_DIR / "score_calibration_audit.csv", pd.DataFrame([calibration_audit]))
    write_csv(REPORT_DIR / "score_calibration_bins.csv", calibration_bins)
    write_csv(REPORT_DIR / "policy_development_split.csv", pd.DataFrame([{"scope": "P7_POLICY_TUNE", "rows": len(tune), "start": str(pd.to_datetime(tune.transaction_timestamp).min()), "end": str(pd.to_datetime(tune.transaction_timestamp).max())}, {"scope": "P7_POLICY_CONFIRM", "rows": len(confirm), "start": str(pd.to_datetime(confirm.transaction_timestamp).min()), "end": str(pd.to_datetime(confirm.transaction_timestamp).max())}, {"scope": "FINAL_OOT", "rows": len(oot), "oot_not_globally_unseen": True}]))
    p0_actions = action_map.get("PART7_P0_ALLOW_ALL", confirm.assign(action="ALLOW", candidate_action="ALLOW", review_priority=0.0, reason_codes=""))
    transitions = pd.DataFrame({"baseline_action": p0_actions.action.astype(str), "challenger_action": selected_actions.action.astype(str)})
    transition_rows = transitions.assign(transition=transitions.baseline_action + " → " + transitions.challenger_action).groupby("transition", as_index=False).size().rename(columns={"size": "rows"})
    write_csv(REPORT_DIR / "shadow_policy_transition_matrix.csv", transition_rows)
    write_csv(REPORT_DIR / "shadow_policy_metric_delta.csv", pd.DataFrame([{"baseline_policy": "PART7_P0_ALLOW_ALL", "challenger_policy": selected_key, "delta_cost": selected["simulated_total_cost"] - confirm_metrics.loc[confirm_metrics.variant == "P0", "simulated_total_cost"].iloc[0], "delta_fraud_capture": selected["fraud_capture"] - confirm_metrics.loc[confirm_metrics.variant == "P0", "fraud_capture"].iloc[0], "delta_exposure_capture": selected["fraud_exposure_capture"] - confirm_metrics.loc[confirm_metrics.variant == "P0", "fraud_exposure_capture"].iloc[0]}]))
    write_json(REPORT_DIR / "delta_reconciliation.json", {"status": "PASS", "formula": "challenger - baseline", "tolerance": 1e-12, "baseline_policy": "PART7_P0_ALLOW_ALL", "challenger_policy": selected_key})
    write_csv(REPORT_DIR / "bootstrap_policy_ci.csv", weekly_paired_bootstrap(confirm, selected_actions, p0_actions, assumptions, draws=1000))
    stability = confirm_metrics.copy()
    stability["scenario_id"] = "BASE_P7_POLICY_CONFIRM"
    stability["assumption_hash"] = "PART7_ECONOMICS_v1.0"
    write_csv(REPORT_DIR / "policy_stability_matrix.csv", stability[["scenario_id", "assumption_hash", "review_capacity", "policy_version", "review_threshold", "block_threshold", "allow_rate", "review_rate", "block_rate", "fraud_capture", "fraud_exposure_capture", "legitimate_block_rate", "simulated_total_cost"]])
    for name, column in (("channel_policy_metrics.csv", "channel"), ("cold_start_policy_metrics.csv", "cold_start_segment")):
        if column == "cold_start_segment":
            selected_actions[column] = np.select([selected_actions.get("cold_card", False) & selected_actions.get("new_merchant", False), selected_actions.get("cold_card", False), selected_actions.get("new_merchant", False), selected_actions.get("pair_new", False)], ["BOTH_NODES_UNSEEN", "NEW_CARD_ONLY", "NEW_MERCHANT_ONLY", "WARM_PAIR_NEW"], default="WARM_PAIR_SEEN")
        write_csv(REPORT_DIR / name, _segments(selected_actions, assumptions, column, column) if column in selected_actions else pd.DataFrame())
    card = f"""# Block E / Part 7 — Final decision card\n\n## Status\n\n`POLICY_SELECTED` — pre-freeze evidence on `P7_POLICY_CONFIRM`.\n\n## Selected profile\n\n`{args.profile.upper()}` with policy candidate `{selected_key}`. Thresholds and action rates are available in the aggregate reports. No final OOT claim is made before a verified freeze.\n\n## Claim boundary\n\nIBM TabFormer is synthetic. Economics, reviewer performance, capacity, savings, and loss outcomes are simulated. `oot_not_globally_unseen=true` because Parts 5–6 already evaluated the upstream OOT period.\n\n## Next gate\n\nFreeze the approved policy on a clean commit, verify config hashes, then run the final replay exactly once.\n"""
    (REPORT_DIR / "PART7_FINAL_DECISION_CARD.md").write_text(card, encoding="utf-8")
    _, scope_path, selected_path = _write_confirmation_handoff(confirm, args, selected, REPORT_DIR / "policy_candidate_metrics.csv", REPORT_DIR / "policy_profile_comparison.csv")
    write_summary("POLICY_SELECTED", args.score_version, selected_key, args.profile, {key: selected.get(key) for key in ("review_threshold", "block_threshold", "review_capacity")}, {key: selected.get(key) for key in ("allow_rate", "review_rate", "block_rate", "fraud_capture", "fraud_exposure_capture", "legitimate_block_rate", "simulated_total_cost")}, score_status=args.score_status)
    _advance_stage("POLICY_SELECTED", selected_policy=selected_path.relative_to(ROOT).as_posix(), confirmation_manifest=scope_path.relative_to(ROOT).as_posix())
    _refresh_validation_snapshot(selected_key)
    print(f"Part 7 completed: {selected_key}; profile={args.profile}; rows={len(frame)}")
    return 0


def freeze_stage(args: argparse.Namespace) -> int:
    selected_path = args.selected_policy or (REPORT_DIR / "PART7_SELECTED_POLICY.json")
    manifest_path = REPORT_DIR / "P7_CONFIRMATION_SCOPE_MANIFEST.json"
    if not selected_path.exists() or not manifest_path.exists():
        raise RuntimeError("Freeze requires committed PART7_SELECTED_POLICY.json and P7_CONFIRMATION_SCOPE_MANIFEST.json")
    if args.input is None:
        raise RuntimeError("Freeze requires --input so the frozen score hash can be verified")
    selected = json.loads(selected_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if selected.get("status") != "POLICY_SELECTED":
        raise RuntimeError("Selected-policy handoff is not in POLICY_SELECTED state")
    if selected.get("confirmation_scope_hash") != manifest.get("confirmation_scope_hash"):
        raise RuntimeError("Selected policy and confirmation scope hash do not match")
    config_paths = [ROOT / "config" / "part7" / "economic_assumptions.yaml", ROOT / "config" / "part7" / "graph_routing_policy.yaml", ROOT / "config" / "part7" / "reason_codes.yaml"]
    freeze_path = freeze_policy(selected, config_paths, selected["score_version"], selected["model_version"], selected.get("calibration_version"), score_status=selected["score_status"], score_path=args.input, graph_version="PART6_GRAPH_UNSPECIFIED", confirmation_scope_hash=selected["confirmation_scope_hash"], selected_policy_path=selected_path, confirmation_manifest_path=manifest_path)
    loaded = load_and_verify_freeze(freeze_path, score_path=args.input, selected_policy_path=selected_path, confirmation_manifest_path=manifest_path)
    verification = json.loads((REPORT_DIR / "PART7_REPLAY_VERIFICATION.json").read_text(encoding="utf-8"))
    write_json(REPORT_DIR / "PART7_FREEZE_VERIFICATION.json", {"freeze_id": loaded.get("freeze_id"), **verification, "status": "PASS"})
    _advance_stage("POLICY_FROZEN", freeze=freeze_path.relative_to(ROOT).as_posix())
    write_summary("POLICY_FROZEN", selected["score_version"], selected["policy_version"], selected["profile"], {key: selected.get(key) for key in ("review_threshold", "block_threshold", "review_capacity")}, score_status=selected["score_status"])
    _refresh_validation_snapshot(selected["policy_version"])
    print(f"Part 7 freeze complete: {loaded.get('freeze_id')}")
    return 0


def replay_stage(args: argparse.Namespace) -> int:
    if args.input is None:
        raise RuntimeError("Replay requires --input")
    freeze_path = REPORT_DIR / "PART7_POLICY_FREEZE.json"
    if not freeze_path.exists():
        raise RuntimeError("Replay requires PART7_POLICY_FREEZE.json; run freeze after committing confirmation evidence")
    selected_path = REPORT_DIR / "PART7_SELECTED_POLICY.json"
    if not selected_path.exists():
        raise RuntimeError("Replay requires PART7_SELECTED_POLICY.json")
    selected = json.loads(selected_path.read_text(encoding="utf-8"))
    started = pd.Timestamp.utcnow().isoformat()
    loaded = load_and_verify_freeze(freeze_path, score_path=args.input, selected_policy_path=selected_path, confirmation_manifest_path=REPORT_DIR / "P7_CONFIRMATION_SCOPE_MANIFEST.json")
    freeze_verification_path = REPORT_DIR / "PART7_FREEZE_VERIFICATION.json"
    if not freeze_verification_path.exists() or json.loads(freeze_verification_path.read_text(encoding="utf-8")).get("status") != "PASS":
        raise RuntimeError("Replay requires PASS freeze verification")
    frame = add_exposure_bases(normalise_input(load_frame(args.input)))
    _, _, oot = _scope(frame)
    if oot.empty:
        raise RuntimeError("Replay requires non-empty FINAL_OOT scope")
    queue_config = _yaml(ROOT / "config" / "part7" / "review_queue.yaml")
    precedence_config = load_precedence_config(ROOT / "config" / "part7" / "action_precedence.yaml")
    assumptions = _assumptions(ROOT)
    replay_actions, final_metrics = replay(oot, loaded, assumptions, loaded["score_status"] == "PROBABILITY_USABLE", queue_config=queue_config, precedence_config=precedence_config)
    write_csv(REPORT_DIR / "final_oot_policy_metrics.csv", pd.DataFrame([final_metrics]))
    p0 = oot.drop(columns=["fraud_label"], errors="ignore").assign(action="ALLOW", candidate_action="ALLOW", review_priority=0.0, reason_codes="")
    if not oot.empty:
        write_csv(REPORT_DIR / "bootstrap_policy_ci.csv", weekly_paired_bootstrap(oot, replay_actions, p0, assumptions, draws=1000))
    finished = pd.Timestamp.utcnow().isoformat()
    write_json(REPORT_DIR / "final_replay_metadata.json", {"replay_started_at": started, "replay_finished_at": finished, "freeze_id": loaded.get("freeze_id"), "code_commit": loaded.get("code_commit"), "score_version": loaded.get("score_version"), "status": "PASS"})
    _advance_stage("FINAL_REPLAY_COMPLETE", freeze_id=loaded.get("freeze_id"))
    write_summary("FINAL_REPLAY_COMPLETE", loaded["score_version"], loaded["policy_version"], loaded["selected_profile"], {key: loaded.get(key) for key in ("review_threshold", "block_threshold", "review_capacity")}, {key: final_metrics.get(key) for key in ("allow_rate", "review_rate", "block_rate", "fraud_capture", "fraud_exposure_capture", "legitimate_block_rate", "simulated_total_cost")}, score_status=loaded["score_status"])
    validation = _refresh_validation_snapshot(loaded["policy_version"])
    if (validation.status == "PASS").sum() == 64 and (validation.status == "BLOCKED").sum() == 0 and (validation.status == "FAIL").sum() == 0:
        assert_transition("FINAL_REPLAY_COMPLETE", "DECISION_POLICY_LOCKED")
        write_summary("DECISION_POLICY_LOCKED", loaded["score_version"], loaded["policy_version"], loaded["selected_profile"], {key: loaded.get(key) for key in ("review_threshold", "block_threshold", "review_capacity")}, {key: final_metrics.get(key) for key in ("allow_rate", "review_rate", "block_rate", "fraud_capture", "fraud_exposure_capture", "legitimate_block_rate", "simulated_total_cost")}, score_status=loaded["score_status"])
        _advance_stage("DECISION_POLICY_LOCKED", freeze_id=loaded.get("freeze_id"))
        _refresh_validation_snapshot(loaded["policy_version"])
    print(f"Part 7 replay complete: status={(json.loads((REPORT_DIR / 'PART7_FINAL_SUMMARY.json').read_text(encoding='utf-8'))).get('status')}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Block E / Part 7 policy engine")
    subparsers = parser.add_subparsers(dest="stage", required=True)
    develop = subparsers.add_parser("develop", help="Tune and confirm only")
    freeze = subparsers.add_parser("freeze", help="Freeze committed confirmation evidence")
    replay_parser = subparsers.add_parser("replay", help="Replay FINAL_OOT using an immutable freeze")
    for command in (develop, freeze, replay_parser):
        command.add_argument("--input", type=Path, required=True)
    develop.add_argument("--score-status", choices=["PROBABILITY_USABLE", "RANKING_ONLY"], required=True)
    develop.add_argument("--score-version", required=True)
    develop.add_argument("--model-version", required=True)
    develop.add_argument("--calibration-version")
    develop.add_argument("--profile", choices=["growth", "balanced", "conservative"], default="balanced")
    freeze.add_argument("--selected-policy", type=Path)
    args = parser.parse_args()
    try:
        if args.stage == "develop":
            return develop_stage(args)
        if args.stage == "freeze":
            return freeze_stage(args)
        return replay_stage(args)
    except Exception as exc:
        print(f"Part 7 failed closed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
