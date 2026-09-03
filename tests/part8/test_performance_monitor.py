import unittest

from src.part8.performance_monitor import evaluate_performance
from test_helpers import fixture_frame


class PerformanceTests(unittest.TestCase):
    def test_matured_performance_has_pr_auc(self):
        result = evaluate_performance(fixture_frame(120), min_fraud_support=3)
        self.assertIn("pr_auc", result); self.assertEqual(result["label_mode"], "RETROSPECTIVE_MATURED")

    def test_low_support_is_not_fail(self):
        result = evaluate_performance(fixture_frame(10), min_fraud_support=30)
        self.assertEqual(result["status"], "INSUFFICIENT_SUPPORT")
