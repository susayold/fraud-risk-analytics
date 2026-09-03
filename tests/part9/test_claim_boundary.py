import unittest
from pathlib import Path
from src.part9.claim_boundary import validate_chart


class ClaimBoundaryTests(unittest.TestCase):
    def test_blocked_chart_with_data_fails(self):
        errors = validate_chart({"chart_id": "X", "claim_class": "DERIVED", "source_artifact": "missing.csv", "status": "INPUT_BLOCKED", "data": [{"x": 1}]}, Path("."))
        self.assertTrue(errors)
