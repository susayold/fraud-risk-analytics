import unittest
from pathlib import Path


class OOTTuningTests(unittest.TestCase):
    def test_threshold_config_declares_pre_oot_source(self):
        text = Path("config/part8/alert_thresholds.yaml").read_text(encoding="utf-8")
        self.assertIn("threshold_source: EMPIRICAL_PRE_OOT_", text)
        self.assertIn("final_numbers_frozen: true", text)

