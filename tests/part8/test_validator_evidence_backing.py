import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.part8.validate_part8 import validate


class ValidatorEvidenceTests(unittest.TestCase):
    def test_locked_label_does_not_make_missing_evidence_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp)
            (report / "part8_input_audit.json").write_text(json.dumps({"status": "INPUT_BLOCKED", "input_hash": None}), encoding="utf-8")
            (report / "PART8_FINAL_SUMMARY.json").write_text(json.dumps({"status": "MONITORING_GOVERNANCE_LOCKED"}), encoding="utf-8")
            with patch("src.part8.validate_part8.REPORT_DIR", report):
                result = validate()
            self.assertLess(int((result.status == "PASS").sum()), 72)
            self.assertEqual(result.loc[result.gate_id == "P8T72", "status"].iloc[0], "BLOCKED")
            self.assertTrue(result["evidence_field"].notna().all())

