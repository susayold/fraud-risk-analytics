"""Run Part 8 tests without mutating real/frozen evidence."""
from __future__ import annotations

import hashlib
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports" / "part8"
sys.path.insert(0, str(ROOT))
PROTECTED = (
    ROOT / "reports/part8/PART8_MONITORING_BASELINE_FREEZE.json",
    ROOT / "reports/part8/PART8_FINAL_SUMMARY.json",
    ROOT / "reports/part8/reference_feature_distributions.json",
    ROOT / "assets/data/part8_summary.json",
    ROOT / "config/part8/alert_thresholds.yaml",
)


def digest(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() and path.is_file() else None


class EvidenceResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.outcomes = {}

    def startTest(self, test):
        super().startTest(test); self.outcomes[test.id()] = "RUNNING"

    def addSuccess(self, test):
        super().addSuccess(test); self.outcomes[test.id()] = "PASS"

    def addFailure(self, test, err):
        super().addFailure(test, err); self.outcomes[test.id()] = "FAIL"

    def addError(self, test, err):
        super().addError(test, err); self.outcomes[test.id()] = "ERROR"


class EvidenceRunner(unittest.TextTestRunner):
    resultclass = EvidenceResult


def main() -> int:
    before = {path: digest(path) for path in PROTECTED}
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests" / "part8"), pattern="test_*.py")
    result = EvidenceRunner(stream=sys.stdout, verbosity=1).run(suite)
    after = {path: digest(path) for path in PROTECTED}
    mutations = [str(path.relative_to(ROOT)) for path in PROTECTED if before[path] != after[path]]
    outcomes = {key.rsplit(".", 1)[-1]: value for key, value in result.outcomes.items()}
    report = {"generated_at_utc": datetime.now(timezone.utc).isoformat(), "test_count": result.testsRun, "failures": len(result.failures), "errors": len(result.errors), "protected_artifact_mutations": mutations, "status": "PASS" if result.wasSuccessful() and not mutations else "FAIL", "tests": outcomes}
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "P8_TEST_REPORT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (REPORT_DIR / "unit_test_evidence.json").write_text(json.dumps({"generated_at_utc": report["generated_at_utc"], "status": report["status"], **outcomes}, indent=2) + "\n", encoding="utf-8")
    print(f"Part 8 tests: {result.testsRun} run, {len(result.failures)} failures, {len(result.errors)} errors, protected mutations={len(mutations)}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

