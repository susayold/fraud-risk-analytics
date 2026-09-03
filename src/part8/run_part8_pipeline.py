from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

from .baseline import build_baseline
from .io import REPORT_DIR, ROOT, load_frame, normalise_input, public_manifest, sha256_file, write_csv, write_json
from .lineage import write_input_lineage
from .reports import reconcile_summary, write_summary
from .replay_monitoring import replay
from .freeze_monitoring import freeze_monitoring
from .lifecycle import assert_transition
from .validate_part8 import validate


def _advance_stage(target: str, **details) -> None:
    pointer = REPORT_DIR / "part8_stage_pointer.json"
    current = "INPUT_BLOCKED"
    if pointer.exists():
        current = json.loads(pointer.read_text(encoding="utf-8")).get("status", current)
    if current != target:
        assert_transition(current, target)
    write_json(pointer, {"status": target, "stage": target.lower(), **details})


def _snapshot(status: str, reason: str, input_path: Path | None = None) -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    write_json(REPORT_DIR / "part8_input_audit.json", {"status": status, "reason": reason, "input_path_name": input_path.name if input_path else None, "input_hash": sha256_file(input_path) if input_path and input_path.exists() else None, "raw_rows_persisted": False})
    write_csv(REPORT_DIR / "input_reconciliation.csv", pd.DataFrame([{"check_name": "input_source", "status": status, "reason": reason}]))
    if status == "INPUT_BLOCKED":
        write_json(REPORT_DIR / "part8_stage_pointer.json", {"status": "INPUT_BLOCKED", "stage": "input_blocked"})
    summary = write_summary(status=status)
    validation = validate()
    write_csv(REPORT_DIR / "part8_validation_report.csv", validation)
    reconcile_summary(validation, status=status)
    write_csv(REPORT_DIR / "report_manifest.csv", public_manifest())
    print(f"Part 8: {status} — {reason}")
    return 2 if status == "INPUT_BLOCKED" else 0


def baseline_stage(input_path: Path) -> int:
    if not input_path.exists():
        return _snapshot("INPUT_BLOCKED", "No genuine private monitoring mart was supplied", input_path)
    try:
        frame = normalise_input(load_frame(input_path))
        required = {"source_row_id", "transaction_timestamp", "amount", "risk_score", "split_name"}
        missing = sorted(required - set(frame.columns))
        if missing:
            return _snapshot("INPUT_BLOCKED", f"Monitoring contract missing columns: {missing}", input_path)
        if "fraud_label" in frame:
            # The operational baseline is label-free; the matured channel remains separate.
            operational = frame.drop(columns=["fraud_label"])
        else:
            operational = frame
        write_input_lineage(REPORT_DIR / "input_lineage.json", input_path, operational, model_version=str(frame.get("model_version", pd.Series([""])).iloc[0]), score_version=str(frame.get("score_version", pd.Series([""])).iloc[0]))
        _advance_stage("MONITORING_FRAMEWORK_READY", input_hash=sha256_file(input_path))
        build_baseline(frame)
        write_json(REPORT_DIR / "part8_input_audit.json", {"status": "PASS", "reason": "Input contract resolved; baseline uses pre-OOT reference only", "input_path_name": input_path.name, "input_hash": sha256_file(input_path), "rows": len(frame), "raw_rows_persisted": False})
        _advance_stage("BASELINE_READY", baseline_id=json.loads((REPORT_DIR / "reference_baseline_metadata.json").read_text(encoding="utf-8"))["baseline_id"])
        write_summary(status="BASELINE_READY")
        validation = validate(); write_csv(REPORT_DIR / "part8_validation_report.csv", validation); reconcile_summary(validation, "BASELINE_READY"); write_csv(REPORT_DIR / "report_manifest.csv", public_manifest())
        print("Part 8 baseline complete: BASELINE_READY")
        return 0
    except Exception as exc:
        return _snapshot("INPUT_BLOCKED", str(exc), input_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Block F / Part 8 monitoring lifecycle")
    sub = parser.add_subparsers(dest="stage", required=True)
    baseline = sub.add_parser("baseline"); baseline.add_argument("--input", type=Path, required=True)
    freeze = sub.add_parser("freeze")
    replay_parser = sub.add_parser("replay"); replay_parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.stage == "baseline": return baseline_stage(args.input)
        if args.stage == "freeze":
            frozen = freeze_monitoring(); _advance_stage("MONITORING_BASELINE_FROZEN", baseline_id=frozen["baseline_id"]); write_summary(status="MONITORING_BASELINE_FROZEN"); print("Part 8 freeze complete: MONITORING_BASELINE_FROZEN"); return 0
        replay(args.input)
        _advance_stage("MONITORING_REPLAY_COMPLETE", baseline_id=json.loads((REPORT_DIR / "PART8_MONITORING_BASELINE_FREEZE.json").read_text(encoding="utf-8"))["baseline_id"])
        write_summary(status="MONITORING_REPLAY_COMPLETE")
        validation = validate(); write_csv(REPORT_DIR / "part8_validation_report.csv", validation); reconcile_summary(validation, "MONITORING_REPLAY_COMPLETE"); write_csv(REPORT_DIR / "report_manifest.csv", public_manifest())
        if int((validation.status == "PASS").sum()) == 72 and int((validation.status == "BLOCKED").sum()) == 0 and int((validation.status == "FAIL").sum()) == 0:
            _advance_stage("MONITORING_GOVERNANCE_LOCKED", baseline_id=json.loads((REPORT_DIR / "PART8_MONITORING_BASELINE_FREEZE.json").read_text(encoding="utf-8"))["baseline_id"])
            write_summary(status="MONITORING_GOVERNANCE_LOCKED")
            validation = validate(); write_csv(REPORT_DIR / "part8_validation_report.csv", validation); reconcile_summary(validation, "MONITORING_GOVERNANCE_LOCKED"); write_csv(REPORT_DIR / "report_manifest.csv", public_manifest())
        print("Part 8 replay complete: MONITORING_REPLAY_COMPLETE")
        return 0
    except Exception as exc:
        print(f"Part 8 failed closed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
