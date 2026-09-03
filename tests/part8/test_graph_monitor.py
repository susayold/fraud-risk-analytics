import unittest

from src.part8.graph_monitor import monitor_graph
from test_helpers import fixture_frame


class GraphTests(unittest.TestCase):
    def test_graph_is_context_only(self):
        result = monitor_graph(fixture_frame(12), "D-1")
        self.assertEqual(result["graph_governance"], "context_and_priority_only")
        self.assertFalse(result["graph_auto_block"])
