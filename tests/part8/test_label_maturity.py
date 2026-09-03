import unittest

from src.part8.label_maturity import build_matured_outcome_view
from test_helpers import fixture_frame


class LabelMaturityTests(unittest.TestCase):
    def test_matured_mode_is_explicit(self):
        result = build_matured_outcome_view(fixture_frame(5))
        self.assertEqual(result["label_mode"].iloc[0], "RETROSPECTIVE_MATURED")

    def test_missing_label_blocks(self):
        with self.assertRaises(ValueError):
            build_matured_outcome_view(fixture_frame(5, False))
