import unittest
from pathlib import Path
import pandas as pd
from src.part9.source_registry import build_source_registry


class SourceRegistryTests(unittest.TestCase):
    def test_core_sources_are_available_and_hashed(self):
        registry = build_source_registry(Path("."))
        core = registry[registry.source_id.isin(["part2_summary", "part2_split_summary", "part3_monthly_trend", "part3_channel_risk", "part3_amount_band_risk", "part3_mcc_risk", "part4_feature_registry"])]
        self.assertTrue((core.status == "AVAILABLE").all())
        self.assertTrue(core.sha256.str.len().eq(64).all())
