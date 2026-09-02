"""Run Part 7 tests and persist machine-readable evidence without raw data."""
from __future__ import annotations

import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports" / "part7"
sys.path.insert(0, str(ROOT))


class EvidenceResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.outcomes: dict[str, str] = {}

    def startTest(self, test):
        super().startTest(test)
        self.outcomes[test.id()] = "RUNNING"

    def addSuccess(self, test):
        super().addSuccess(test); self.outcomes[test.id()] = "PASS"

    def addFailure(self, test, err):
        super().addFailure(test, err); self.outcomes[test.id()] = "FAIL"

    def addError(self, test, err):
        super().addError(test, err); self.outcomes[test.id()] = "ERROR"


class EvidenceRunner(unittest.TextTestRunner):
    resultclass = EvidenceResult


def main() -> int:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests" / "part7"), pattern="test_*.py")
    result = EvidenceRunner(stream=sys.stdout, verbosity=1).run(suite)
    outcomes = {key.rsplit(".", 1)[-1]: value for key, value in result.outcomes.items()}
    report = {"generated_at_utc": datetime.now(timezone.utc).isoformat(), "test_count": result.testsRun,
              "failures": len(result.failures), "errors": len(result.errors), "status": "PASS" if result.wasSuccessful() else "FAIL", "tests": outcomes}
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "P7_TEST_REPORT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    key_map = {}
    for key, value in outcomes.items():
        key_map[key] = value
    (REPORT_DIR / "unit_test_evidence.json").write_text(json.dumps({"generated_at_utc": report["generated_at_utc"], "status": report["status"], **key_map}, indent=2) + "\n", encoding="utf-8")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
