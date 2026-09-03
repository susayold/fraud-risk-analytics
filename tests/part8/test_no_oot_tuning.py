import unittest
import tempfile
from pathlib import Path

from src.part8.io import write_json


class OOTTuningTests(unittest.TestCase):
    def test_threshold_config_declares_pre_oot_source(self):
        text = Path("config/part8/alert_thresholds.yaml").read_text(encoding="utf-8")
        self.assertIn("EMPIRICAL_PRE_OOT_BASELINE", text)
        self.assertIn("final_numbers_frozen: false", text)

