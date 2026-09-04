from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HTML = (ROOT / "part-6.html").read_text(encoding="utf-8")
JS = (ROOT / "js" / "part-6.js").read_text(encoding="utf-8")


class GraphGovernanceTests(unittest.TestCase):
    def test_graph_cannot_be_presented_as_a_standalone_decision(self):
        for text in ("Graph-only BLOCK", "Graph context does not decide alone", "TARGET ENCODING IS A HIGH-RISK LEAKAGE SURFACE", "Raw IDs", "raw graph edges"):
            self.assertIn(text, HTML)

    def test_public_boundary_is_source_driven(self):
        for key in ("graph_auto_block_allowed", "raw_ids_published", "raw_edges_published", "aggregate_only"):
            self.assertIn(key, JS)
        self.assertIn("aggregate-only", HTML)


if __name__ == "__main__":
    unittest.main()
