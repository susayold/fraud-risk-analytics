"""Fail closed when required Part 2 reports or policies are missing."""

import json
from pathlib import Path

from config import REPORTS_DIR, SUMMARY_PATH

REQUIRED = ("data_inventory.csv", "data_dictionary.csv", "leakage_register.csv", "split_summary.csv", "data_issues.csv")


def main() -> None:
    missing = [name for name in REQUIRED if not (REPORTS_DIR / name).exists()]
    if missing or not SUMMARY_PATH.exists():
        raise SystemExit(f"Missing required Part 2 outputs: {', '.join(missing) or 'assets/data/part2_summary.json'}")
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    if summary.get("status") == "READY" and summary.get("transactions"):
        print(f"Part 2 outputs are valid and source-derived: {summary['transactions']:,} transactions audited.")
    else:
        print("Part 2 output structure is present. Numeric readiness still depends on an executed source audit.")


if __name__ == "__main__":
    main()
