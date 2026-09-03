import unittest

from src.part8.upstream_adapter import adapt_part7_decision_mart, capacity_reconciliation
from test_helpers import fixture_frame


class Part7AdapterTests(unittest.TestCase):
    def test_exact_mapping_and_bucket_reconciliation(self):
        frame = fixture_frame(6, False)
        frame["candidate_action"] = ["REVIEW", "REVIEW", "ALLOW", "REVIEW", "REVIEW", "ALLOW"]
        frame["bucket_selected"] = [True, False, False, True, False, False]
        frame["overflow"] = [False, True, False, False, True, False]
        frame["capacity_bucket"] = ["B1"] * 6
        frame["bucket_capacity"] = [2] * 6
        adapted = adapt_part7_decision_mart(frame)
        self.assertIn("review_selected", adapted); self.assertIn("review_overflow", adapted)
        result = capacity_reconciliation(frame)
        self.assertEqual(result.iloc[0]["status"], "PASS")

