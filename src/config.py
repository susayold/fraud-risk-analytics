from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
INTERIM_DIR = ROOT / "data" / "interim"
PROCESSED_DIR = ROOT / "data" / "processed"
REPORTS_DIR = ROOT / "reports"
DATABASE_DIR = ROOT / "database"
SUMMARY_PATH = ROOT / "assets" / "data" / "part2_summary.json"

for directory in (INTERIM_DIR, PROCESSED_DIR, REPORTS_DIR, DATABASE_DIR, SUMMARY_PATH.parent):
    directory.mkdir(parents=True, exist_ok=True)
