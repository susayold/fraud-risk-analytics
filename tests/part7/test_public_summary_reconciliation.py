import json
import unittest
from pathlib import Path

import pandas as pd


class PublicSummaryReconciliationTests(unittest.TestCase):
    def test_csv_summary_and_asset_counts_match(self):
        report = pd.read_csv(Path("reports/part7/part7_validation_report.csv"))
        summary = json.loads(Path("reports/part7/PART7_FINAL_SUMMARY.json").read_text(encoding="utf-8"))
        asset = json.loads(Path("assets/data/part7_summary.json").read_text(encoding="utf-8"))
        counts = {"pass": int((report.status == "PASS").sum()), "blocked": int((report.status == "BLOCKED").sum()), "fail": int((report.status == "FAIL").sum())}
        for value in (summary["validation"], asset["validation"]):
            self.assertEqual({key: value[key] for key in counts}, counts)
        self.assertEqual(summary["source_commit"], asset["source_commit"])


if __name__ == "__main__":
    unittest.main()
