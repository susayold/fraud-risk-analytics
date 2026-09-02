import unittest
import pandas as pd

from src.part7.exposure import add_exposure_bases
from src.part7.review_queue import apply_policy


class Part7GraphBoundaryTests(unittest.TestCase):
    def test_graph_does_not_change_block_eligibility(self):
        frame = add_exposure_bases(pd.DataFrame([
            {"source_row_id": 1, "risk_score": .96, "amount": 1, "pair_new": True},
            {"source_row_id": 2, "risk_score": .95, "amount": 1, "pair_new": False},
        ]))
        score = apply_policy(frame, .5, .95, .5, "SCORE_ONLY")
        graph = apply_policy(frame, .5, .95, .5, "GRAPH_NOVELTY")
        self.assertEqual(score.loc[score.source_row_id == 1, "candidate_action"].iloc[0], graph.loc[graph.source_row_id == 1, "candidate_action"].iloc[0])
        self.assertEqual(score.loc[score.source_row_id == 2, "candidate_action"].iloc[0], graph.loc[graph.source_row_id == 2, "candidate_action"].iloc[0])


if __name__ == "__main__":
    unittest.main()
