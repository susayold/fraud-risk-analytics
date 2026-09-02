import unittest

import pandas as pd

from src.part7.exposure import add_exposure_bases
from src.part7.review_queue import apply_policy


class CausalReviewQueueTests(unittest.TestCase):
    def _frame(self):
        return add_exposure_bases(pd.DataFrame([
            {"source_row_id": 1, "transaction_timestamp": "2026-01-01T00:00:00Z", "risk_score": .80, "amount": 100},
            {"source_row_id": 2, "transaction_timestamp": "2026-01-01T01:00:00Z", "risk_score": .70, "amount": 100},
            {"source_row_id": 3, "transaction_timestamp": "2026-01-02T00:00:00Z", "risk_score": .99, "amount": 100},
        ]))

    def test_capacity_is_bucket_local(self):
        out = apply_policy(self._frame(), .5, 1.0, .5)
        day_one = out[out.capacity_bucket == "2026-01-01"]
        day_two = out[out.capacity_bucket == "2026-01-02"]
        self.assertEqual(int(day_one.action.eq("REVIEW").sum()), 1)
        self.assertEqual(int(day_two.action.eq("ALLOW").sum()), 1)
        self.assertEqual(int(day_two.bucket_capacity.iloc[0]), 0)

    def test_future_rows_do_not_change_past_bucket(self):
        frame = self._frame()
        day_one = frame[frame.transaction_timestamp.str.startswith("2026-01-01")]
        first = apply_policy(day_one, .5, 1.0, .5).set_index("source_row_id").action
        combined = apply_policy(frame, .5, 1.0, .5).set_index("source_row_id").action
        pd.testing.assert_series_equal(first, combined.loc[first.index], check_names=False)

    def test_capacity_reconciles_per_bucket(self):
        out = apply_policy(self._frame(), .5, 1.0, .5)
        for _, group in out.groupby("capacity_bucket"):
            self.assertLessEqual(int(group.action.eq("REVIEW").sum()), int(group.bucket_capacity.iloc[0]))

    def test_ties_are_deterministic_and_order_invariant(self):
        frame = self._frame().iloc[[1, 0, 2]].reset_index(drop=True)
        a = apply_policy(frame, .5, 1.0, .5).set_index("source_row_id").action.sort_index()
        b = apply_policy(self._frame(), .5, 1.0, .5).set_index("source_row_id").action.sort_index()
        pd.testing.assert_series_equal(a, b)


if __name__ == "__main__":
    unittest.main()
