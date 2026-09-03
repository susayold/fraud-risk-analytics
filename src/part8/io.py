from __future__ import annotations

import hashlib
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT / "reports" / "part8"
PRIVATE_DIR = ROOT / "private" / "part8"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_metadata(repo_root: Path = ROOT) -> tuple[str, bool]:
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_root, capture_output=True, text=True, check=False).stdout.strip() or "UNKNOWN"
    dirty = bool(subprocess.run(["git", "status", "--porcelain"], cwd=repo_root, capture_output=True, text=True, check=False).stdout.strip())
    return commit, dirty


def load_frame(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    if path.suffix.lower() in {".parquet", ".pq"}:
        return pd.read_parquet(path)
    raise ValueError(f"Unsupported monitoring mart format: {path.suffix}")


def normalise_input(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    aliases = {"PRIMARY_FRAUD_SCORE": "risk_score", "score": "risk_score", "timestamp": "transaction_timestamp", "split": "split_name"}
    for source, target in aliases.items():
        if target not in frame and source in frame:
            frame[target] = frame[source]
    if "positive_exposure" not in frame and "amount" in frame:
        frame["positive_exposure"] = pd.to_numeric(frame["amount"], errors="coerce").clip(lower=0)
    if "action" in frame:
        frame["action"] = frame["action"].astype(str).str.upper()
    if "transaction_timestamp" in frame:
        frame["transaction_timestamp"] = pd.to_datetime(frame["transaction_timestamp"], utc=True, errors="coerce")
    return frame


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    def clean(item: Any):
        if isinstance(item, dict):
            return {str(key): clean(val) for key, val in item.items()}
        if isinstance(item, (list, tuple)):
            return [clean(val) for val in item]
        if isinstance(item, float) and not math.isfinite(item):
            return None
        try:
            if pd.isna(item):
                return None
        except (TypeError, ValueError):
            pass
        return item.item() if hasattr(item, "item") else item

    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(clean(value), indent=2, ensure_ascii=False, default=str, allow_nan=False) + "\n", encoding="utf-8")
    temp.replace(path)


def write_csv(path: Path, frame: pd.DataFrame | list[dict[str, Any]], columns: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    value = frame if isinstance(frame, pd.DataFrame) else pd.DataFrame(frame)
    if columns:
        value = value.reindex(columns=columns)
    temp = path.with_suffix(path.suffix + ".tmp")
    value.to_csv(temp, index=False)
    temp.replace(path)


def public_manifest(baseline_id: str | None = None) -> pd.DataFrame:
    commit, _ = git_metadata()
    excluded = {"report_manifest.csv", "part8_validation_report.csv", "P8_TEST_REPORT.json", "unit_test_evidence.json", "PART8_FINAL_SUMMARY.json"}
    rows = []
    def public_path(path: Path) -> str:
        try:
            return path.relative_to(ROOT).as_posix()
        except ValueError:
            # Test and private execution reports may intentionally live outside
            # the repository; never leak their absolute path into public evidence.
            return f"reports/part8/{path.name}"
    for path in sorted(REPORT_DIR.glob("*")):
        if path.is_file() and path.name not in excluded:
            rows.append({"relative_path": public_path(path), "stage": "GOVERNANCE", "bytes": path.stat().st_size, "sha256": sha256_file(path), "generated_at_utc": utc_now(), "baseline_id": baseline_id or "NOT_FROZEN", "model_version": "", "policy_version": "", "code_commit": commit})
    return pd.DataFrame(rows, columns=["relative_path", "stage", "bytes", "sha256", "generated_at_utc", "baseline_id", "model_version", "policy_version", "code_commit"])
