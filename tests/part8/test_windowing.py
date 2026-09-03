import unittest

from src.part8.windowing import assign_windows
from test_helpers import fixture_frame


class WindowTests(unittest.TestCase):
    def test_one_row_gets_all_windows(self):
        result = assign_windows(fixture_frame(3))
        self.assertTrue(result[["operational_window_id", "drift_window_id", "performance_window_id"]].notna().all().all())

    def test_future_rows_do_not_change_old_window_ids(self):
        base = assign_windows(fixture_frame(5))["drift_window_id"].tolist()
        extended = assign_windows(fixture_frame(8))["drift_window_id"].tolist()[:5]
        self.assertEqual(base, extended)
