from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HTML = (ROOT / "part-9.html").read_text(encoding="utf-8")
JS = (ROOT / "js" / "part-9.js").read_text(encoding="utf-8")
AUDIT = (ROOT / "reports/part9/PART9_FINAL_RELEASE_AUDIT.md").read_text(encoding="utf-8")


class StaleArtifactDetectionTests(unittest.TestCase):
    def test_current_audit_does_not_publish_stale_part5_part6_block(self):
        self.assertNotIn("Part 5 model charts remain `INPUT_BLOCKED`", AUDIT)
        self.assertNotIn("Part 6 graph charts remain `INPUT_BLOCKED`", AUDIT)
        self.assertIn("SOURCE HEALTH", HTML)

    def test_runtime_has_explicit_stale_detection(self):
        self.assertIn("STALE", JS)
        self.assertIn("source-health-note", JS)


if __name__ == "__main__":
    unittest.main()
