from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HTML = (ROOT / "part-7.html").read_text(encoding="utf-8")


class GraphPolicyBoundaryTests(unittest.TestCase):
    def test_graph_is_supplementary_and_cannot_auto_block(self):
        for text in ("Graph context can support REVIEW routing only", "graph evidence alone cannot auto-BLOCK", "Graph-only BLOCK", "Graph-Assisted"):
            self.assertIn(text, HTML)

    def test_public_evidence_boundary_is_explicit(self):
        for text in ("Aggregate-only", "no row-level decisions", "synthetic transaction study"):
            self.assertIn(text, HTML)


if __name__ == "__main__":
    unittest.main()
