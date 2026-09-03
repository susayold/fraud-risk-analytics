import unittest
from pathlib import Path

import pandas as pd

from src.part7.graph_routing import graph_weights_from_config, load_graph_weights
from src.part7.review_queue import apply_policy
from src.part7.exposure import add_exposure_bases


class GraphConfigTests(unittest.TestCase):
    def test_graph_weights_loaded_from_yaml(self):
        weights = load_graph_weights(Path("config/part7/graph_routing_policy.yaml"))
        self.assertEqual(weights, {"pair_new": 1.10, "cold_card": 1.08, "new_merchant": 1.08, "cross_community": 1.06})

    def test_config_weight_changes_review_priority_not_block_eligibility(self):
        frame = add_exposure_bases(pd.DataFrame([
            {"source_row_id": 1, "transaction_timestamp": "2026-01-01T00:00:00Z", "risk_score": .7, "amount": 10.0, "pair_new": True},
            {"source_row_id": 2, "transaction_timestamp": "2026-01-01T00:00:00Z", "risk_score": .7, "amount": 10.0, "pair_new": False},
            {"source_row_id": 3, "transaction_timestamp": "2026-01-01T00:00:00Z", "risk_score": .95, "amount": 10.0, "pair_new": True},
        ]))
        base = {"pair_new": 1.10}
        changed = {"pair_new": 2.0}
        first = apply_policy(frame, .5, .9, 1.0, "GRAPH_NOVELTY", graph_weights=base)
        second = apply_policy(frame, .5, .9, 1.0, "GRAPH_NOVELTY", graph_weights=changed)
        self.assertEqual(first.set_index("source_row_id").candidate_action.to_dict(), second.set_index("source_row_id").candidate_action.to_dict())
        self.assertNotEqual(float(first.loc[first.source_row_id == 1, "review_priority"].iloc[0]), float(second.loc[second.source_row_id == 1, "review_priority"].iloc[0]))
        self.assertEqual(first.set_index("source_row_id").action.to_dict(), second.set_index("source_row_id").action.to_dict())

    def test_unknown_graph_field_rejected(self):
        with self.assertRaises(ValueError):
            graph_weights_from_config({"automatic_block_override": {"enabled": False}, "review_priority": {"unknown": {"enabled": True, "weight": 1.1}}})

    def test_autoblock_rejected(self):
        with self.assertRaises(ValueError):
            graph_weights_from_config({"automatic_block_override": {"enabled": True}, "review_priority": {"pair_new": {"enabled": True, "weight": 1.1}}})


if __name__ == "__main__":
    unittest.main()
