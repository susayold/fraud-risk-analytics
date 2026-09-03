import unittest

from src.part8.review_monitor import monitor_review
from test_helpers import fixture_frame


class ReviewTests(unittest.TestCase):
    def test_capacity_reconciles(self):
        result = monitor_review(fixture_frame(20), capacity=10)
        self.assertLessEqual(result["selected_cases"], 20)
        self.assertEqual(result["overflow_cases"], 0)
