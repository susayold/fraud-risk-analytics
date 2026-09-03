import unittest

from src.part8.label_maturity import build_operational_view
from test_helpers import fixture_frame


class LabelFirewallTests(unittest.TestCase):
    def test_operational_view_rejects_label(self):
        with self.assertRaises(ValueError):
            build_operational_view(fixture_frame(5))

    def test_label_free_input_is_allowed(self):
        self.assertEqual(len(build_operational_view(fixture_frame(5, False))), 5)
