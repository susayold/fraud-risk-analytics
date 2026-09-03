import unittest

from src.part8.lifecycle import can_lock


class ThresholdFreezeTests(unittest.TestCase):
    def test_lock_requires_all_gates(self):
        self.assertFalse(can_lock(71, 1, 0, "MONITORING_REPLAY_COMPLETE"))
        self.assertTrue(can_lock(72, 0, 0, "MONITORING_REPLAY_COMPLETE"))

