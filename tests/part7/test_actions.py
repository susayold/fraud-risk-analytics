import unittest
from datetime import datetime, timezone

import pandas as pd

from src.part7.contracts import Action, DecisionContext, PolicyConfig
from src.part7.exposure import add_exposure_bases
from src.part7.review_queue import apply_policy


class Part7ActionTests(unittest.TestCase):
    def setUp(self):
        self.frame = add_exposure_bases(pd.DataFrame([
            {"source_row_id": 1, "transaction_timestamp": "2026-01-01T00:00:00+00:00", "risk_score": .99, "amount": 100, "pair_new": True},
            {"source_row_id": 2, "transaction_timestamp": "2026-01-02T00:00:00+00:00", "risk_score": .80, "amount": 50},
            {"source_row_id": 3, "transaction_timestamp": "2026-01-03T00:00:00+00:00", "risk_score": .10, "amount": -20},
        ]))

    def test_exact_action_domain_and_capacity(self):
        out = apply_policy(self.frame, .50, .95, 1/3)
        self.assertEqual(set(out.action), {"BLOCK", "REVIEW", "ALLOW"})
        self.assertEqual(int((out.action == "REVIEW").sum()), 1)
        self.assertTrue(set(out.action).issubset({x.value for x in Action}))

    def test_deterministic_tie_break_source_id(self):
        frame = add_exposure_bases(pd.DataFrame([
            {"source_row_id": 2, "transaction_timestamp": "2026-01-01", "risk_score": .70, "amount": 10},
            {"source_row_id": 1, "transaction_timestamp": "2026-01-01", "risk_score": .70, "amount": 10},
        ]))
        out = apply_policy(frame, .5, .9, .5)
        self.assertEqual(int(out.loc[out.source_row_id == 1, "action"].iloc[0] == "REVIEW"), 1)

    def test_decision_context_rejects_label(self):
        with self.assertRaises(ValueError):
            DecisionContext.from_mapping({"source_row_id": 1, "transaction_timestamp": datetime.now(timezone.utc), "risk_score": .5, "amount": 1, "fraud_label": 0})

    def test_policy_threshold_order(self):
        with self.assertRaises(ValueError):
            PolicyConfig("v", .9, .8, .01)


if __name__ == "__main__":
    unittest.main()
