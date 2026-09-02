import unittest

import pandas as pd

from src.part7.score_gate import audit_score_frame


class ScoreStatusReplayTests(unittest.TestCase):
    def setUp(self):
        self.frame = pd.DataFrame({
            "source_row_id": [1],
            "transaction_timestamp": ["2026-01-01T00:00:00Z"],
            "risk_score": [0.9],
            "amount": [10.0],
            "split_name": ["FINAL_OOT"],
        })

    def test_probability_score_requires_calibration_version(self):
        self.assertEqual(audit_score_frame(self.frame, "PROBABILITY_USABLE", "SCORE_V1", None).status, "INPUT_BLOCKED")

    def test_ranking_score_allows_null_calibration_version(self):
        result = audit_score_frame(self.frame, "RANKING_ONLY", "SCORE_V1", None)
        self.assertEqual(result.status, "SCORE_GATE_LOCKED")
        self.assertIsNone(result.calibration_version)


if __name__ == "__main__":
    unittest.main()
