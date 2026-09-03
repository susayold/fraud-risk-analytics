import unittest
from src.part9.public_export import validate_public_payload


class PublicBoundaryTests(unittest.TestCase):
    def test_row_level_keys_are_rejected_recursively(self):
        self.assertTrue(validate_public_payload({"nested": [{"risk_score": 0.2}]}))

    def test_aggregate_risk_summary_key_is_allowed(self):
        self.assertEqual(validate_public_payload({"risk_score_mean": 0.2, "fraud_rate": 0.01}), [])
