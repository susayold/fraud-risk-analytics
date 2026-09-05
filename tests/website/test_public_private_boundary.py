from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HTML = (ROOT / "part-9.html").read_text(encoding="utf-8")


class PublicPrivateBoundaryTests(unittest.TestCase):
    def test_public_aggregate_boundary_is_visible(self):
        for text in ("PUBLIC · ALLOWED", "PRIVATE · NOT PUBLISHED", "PUBLIC PRIVACY BOUNDARY · PASS", "AGGREGATE ONLY"):
            self.assertIn(text, HTML)

    def test_sensitive_row_level_artifacts_are_not_presented_as_public(self):
        for text in ("row-level source IDs", "row-level ALLOW / REVIEW / BLOCK", "raw graph edges and embeddings", "model binaries"):
            self.assertIn(text, HTML)
        self.assertNotIn("source_row_id,", HTML)


if __name__ == "__main__":
    unittest.main()
