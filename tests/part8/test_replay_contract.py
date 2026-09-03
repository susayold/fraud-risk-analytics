import unittest

from src.part8.public_export import export_summary
from pathlib import Path
import tempfile


class ReplayContractTests(unittest.TestCase):
    def test_recursive_public_firewall_rejects_row_level_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                export_summary({"window_id": "FINAL_OOT", "nested": [{"risk_score": 0.4}]}, Path(tmp) / "summary.json")

    def test_public_firewall_allows_aggregate_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            export_summary({"window_id": "FINAL_OOT", "status": "risk_score distribution reviewed"}, Path(tmp) / "summary.json")

