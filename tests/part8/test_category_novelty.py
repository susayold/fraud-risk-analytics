import unittest

from src.part8.category_monitor import category_reference, monitor_categories
from test_helpers import fixture_frame


class CategoryTests(unittest.TestCase):
    def test_new_chip_like_category_is_detected(self):
        reference = fixture_frame(30, False); current = fixture_frame(30, False); current.loc[0, "channel"] = "Chip-Like-New"
        spec = category_reference(reference, "channel")
        result = monitor_categories(reference, current, spec)
        self.assertTrue(result.loc[result.category.eq("Chip-Like-New"), "is_new_category"].iloc[0])
