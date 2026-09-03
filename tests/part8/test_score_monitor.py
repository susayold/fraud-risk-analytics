import unittest

from src.part8.score_monitor import monitor_score, score_summary
from test_helpers import fixture_frame


class ScoreTests(unittest.TestCase):
    def test_summary_has_quantiles(self):
        result = score_summary(fixture_frame(20, False))
        self.assertIn("p99", result)

    def test_score_drift_is_early_warning_only(self):
        frame = fixture_frame(30, False); result = monitor_score(frame.risk_score, frame.risk_score + .2)
        self.assertTrue((result.claim_class == "EARLY_WARNING").all())
