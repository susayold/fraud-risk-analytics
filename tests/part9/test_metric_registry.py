import unittest
from pathlib import Path
from src.part9.metric_registry import build_metric_registry


class MetricRegistryTests(unittest.TestCase):
    def test_every_metric_has_provenance(self):
        metrics = build_metric_registry(Path(".") )
        self.assertEqual(len(metrics), 14)
        self.assertTrue(metrics.metric_id.is_unique)
        self.assertTrue(metrics.source_artifact.notna().all())
        self.assertTrue(metrics.claim_class.notna().all())
