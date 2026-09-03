import unittest
import pandas as pd

from src.part8.alert_engine import build_alerts, classify


class AlertTests(unittest.TestCase):
    def test_severity_domain(self):
        self.assertEqual(classify(.2, .1, .3, 10, 1), "AMBER")
        self.assertEqual(classify(.4, .1, .3, 10, 1), "RED")

    def test_missing_threshold_is_blocked(self):
        result = build_alerts(pd.DataFrame([{"metric": "score_js", "observed": .2, "support": 10}]), {})
        self.assertEqual(result.severity.iloc[0], "BLOCKED")

