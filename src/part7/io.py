from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT / "reports" / "part7"
PRIVATE_DIR = ROOT / "private" / "part7"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_metadata(repo_root: Path = ROOT) -> tuple[str, bool]:
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_root, text=True, capture_output=True, check=False).stdout.strip() or "UNKNOWN"
    dirty = bool(subprocess.run(["git", "status", "--porcelain"], cwd=repo_root, text=True, capture_output=True, check=False).stdout.strip())
    return commit, dirty


def load_frame(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".parquet", ".pq"}:
        return pd.read_parquet(path)
    raise ValueError(f"Unsupported input format: {path.suffix}; use CSV or Parquet")


def normalise_input(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    if "risk_score" not in frame and "PRIMARY_FRAUD_SCORE" in frame:
        frame["risk_score"] = frame["PRIMARY_FRAUD_SCORE"]
    if "split_name" not in frame and "split" in frame:
        frame["split_name"] = frame["split"]
    if "channel" not in frame and "use_chip" in frame:
        frame["channel"] = frame["use_chip"].map({"Online": "ONLINE", "Chip": "CHIP", "Swipe": "SWIPE"}).fillna("OTHER / UNKNOWN")
    return frame


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    def clean(item: Any) -> Any:
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
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(clean(value), indent=2, ensure_ascii=False, default=str, allow_nan=False) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def write_csv(path: Path, frame: pd.DataFrame | list[dict[str, Any]], columns: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    value = frame if isinstance(frame, pd.DataFrame) else pd.DataFrame(frame)
    if columns:
        value = value.reindex(columns=columns)
    temporary = path.with_suffix(path.suffix + ".tmp")
    value.to_csv(temporary, index=False)
    os.replace(temporary, path)


def public_manifest(policy_version: str | None = None) -> pd.DataFrame:
    commit, _ = git_metadata()
    rows = []
    for path in sorted(REPORT_DIR.glob("*")):
        if path.is_file() and path.name != "report_manifest.csv":
            rows.append({"relative_path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size, "sha256": sha256_file(path), "generated_at_utc": utc_now(), "policy_version": policy_version or "NOT_FROZEN", "code_commit": commit})
    return pd.DataFrame(rows, columns=["relative_path", "bytes", "sha256", "generated_at_utc", "policy_version", "code_commit"])
