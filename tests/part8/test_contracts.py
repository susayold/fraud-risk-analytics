import unittest

import pandas as pd

from src.part8.contracts import MonitoringEvent, ensure_public_safe


class ContractTests(unittest.TestCase):
    def test_event_is_explicit(self):
        event = MonitoringEvent("r1", "2026-01-01T00:00:00Z")
        self.assertEqual(event.source_row_id, "r1")

    def test_public_boundary_rejects_row_fields(self):
        with self.assertRaises(ValueError):
            ensure_public_safe(["window_id", "risk_score"])

