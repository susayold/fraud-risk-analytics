import unittest

from src.part8.data_quality import quality_profile, schema_check
from test_helpers import fixture_frame


class QualityTests(unittest.TestCase):
    def test_clean_fixture_passes(self):
        self.assertEqual(quality_profile(fixture_frame(10, False))["status"], "PASS")

    def test_duplicate_id_is_failure(self):
        frame = fixture_frame(10, False); frame.loc[1, "source_row_id"] = frame.loc[0, "source_row_id"]
        self.assertEqual(quality_profile(frame)["status"], "FAIL")

    def test_schema_missing_is_explicit(self):
        self.assertEqual(schema_check(fixture_frame(2, False).drop(columns=["amount"]))["status"], "FAIL")
