import unittest

from src.part8.policy_monitor import monitor_policy
from test_helpers import fixture_frame


class PolicyTests(unittest.TestCase):
    def test_action_rates_reconcile(self):
        result = monitor_policy(fixture_frame(30), "D-1")
        self.assertAlmostEqual(result["allow_rate"] + result["review_rate"] + result["block_rate"], 1.0)

    def test_mixed_policy_versions_fail_closed(self):
        frame = fixture_frame(10); frame.loc[1, "policy_version"] = "P7_V2"
        self.assertEqual(monitor_policy(frame)["status"], "FAIL")
