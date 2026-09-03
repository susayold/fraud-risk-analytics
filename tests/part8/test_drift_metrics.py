import unittest
import numpy as np

from src.part8.drift_metrics import frozen_bins, jensen_shannon, normalized_wasserstein, psi


class DriftMetricTests(unittest.TestCase):
    def test_identical_is_near_zero(self):
        values = np.linspace(0, 1, 100)
        bins = frozen_bins(values)
        self.assertAlmostEqual(jensen_shannon(values, values, bins), 0.0, places=9)
        self.assertAlmostEqual(psi(values, values, bins), 0.0, places=9)

    def test_shift_is_larger(self):
        reference = np.linspace(0, 1, 100); bins = frozen_bins(reference)
        self.assertGreater(jensen_shannon(reference, reference + 2, bins), 0.1)
        self.assertGreater(normalized_wasserstein(reference, reference + 2), 1.0)

    def test_empty_target_is_nan_not_fake_green(self):
        self.assertTrue(np.isnan(normalized_wasserstein([1, 2], [])))

