import json
import tempfile
import unittest
from pathlib import Path

from src.part8.lineage import write_input_lineage
from test_helpers import fixture_frame


class LineageContractTests(unittest.TestCase):
    def test_missing_lineage_is_explicit_not_blank(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "input.csv"; fixture_frame(3, False).to_csv(input_path, index=False)
            output = Path(tmp) / "lineage.json"
            write_input_lineage(output, input_path, fixture_frame(3, False))
            payload = json.loads(output.read_text())
            self.assertEqual(payload["part5_score_hash"], "NOT_AVAILABLE")
            self.assertEqual(payload["part7_policy_freeze_hash"], "NOT_AVAILABLE")
            self.assertEqual(payload["graph_version"], "G1")

