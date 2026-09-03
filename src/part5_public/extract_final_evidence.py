"""Extract only small aggregate Part 5 evidence from a final checkpoint ZIP.

The large checkpoint itself is intentionally never copied into the website repo.
"""
from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

ENTRY_MAP = {
    "part5_final_summary.json": "history/PART5_FINAL_SUMMARY.json",
    "part5_model_selection.json": "history/C09_model_selection_report.csv",
    "part5_calibration.json": "history/C09_calibration_metrics.csv",
    "part5_topk.json": "history/C10_oot_topk_capture.csv",
    "part5_subgroups.json": "history/C10_subgroup_performance.csv",
}


def extract(checkpoint: Path, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(checkpoint) as archive:
        names = set(archive.namelist())
        missing = [entry for entry in ENTRY_MAP.values() if entry not in names]
        if missing:
            raise FileNotFoundError("Missing governed entries: " + ", ".join(missing))
        # This command is deliberately conservative: it writes only files that have
        # already been transformed into the public aggregate schema by a maintainer.
        manifest = {"checkpoint": checkpoint.name, "entries_present": list(ENTRY_MAP.values()), "raw_archive_copied": False}
        (output / "extraction_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("--output", type=Path, default=Path("assets/data"))
    args = parser.parse_args()
    extract(args.checkpoint, args.output)
