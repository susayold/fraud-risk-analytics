"""Build the website summary from the observed audit summary and manifest."""

from __future__ import annotations

import json
from pathlib import Path

from config import SUMMARY_PATH, REPORTS_DIR


def main() -> None:
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    manifest = REPORTS_DIR / "part2_run_manifest.json"
    if manifest.exists():
        summary["run_manifest"] = json.loads(manifest.read_text(encoding="utf-8"))
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Wrote {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
