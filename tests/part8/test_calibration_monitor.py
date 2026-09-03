import unittest

from src.part8.calibration_monitor import evaluate_calibration
from test_helpers import fixture_frame


class CalibrationTests(unittest.TestCase):
    def test_ranking_only_skips_calibration(self):
        self.assertEqual(evaluate_calibration(fixture_frame(10), score_status="RANKING_ONLY")["status"], "NOT_APPLICABLE")

    def test_probability_status_reports_ece(self):
        result = evaluate_calibration(fixture_frame(80), score_status="PROBABILITY_USABLE")
        self.assertIn("ece", result)
