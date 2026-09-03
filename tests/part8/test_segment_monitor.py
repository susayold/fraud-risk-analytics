import unittest

from src.part8.segment_monitor import monitor_segments
from test_helpers import fixture_frame


class SegmentTests(unittest.TestCase):
    def test_preregistered_segments_emit_support(self):
        result = monitor_segments(fixture_frame(20), "W-1")
        self.assertTrue((result.support > 0).all())
