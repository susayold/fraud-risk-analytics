from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HTML = (ROOT / "part-8.html").read_text(encoding="utf-8")
JS = (ROOT / "js" / "part-8.js").read_text(encoding="utf-8")


class MonitoringSupportSemanticsTests(unittest.TestCase):
    def test_support_boundary_is_visible(self):
        self.assertIn("INSUFFICIENT_SUPPORT", HTML)
        self.assertIn("no fraud support cannot produce a zero PR-AUC claim", HTML)
        self.assertIn("Matured PR-AUC timeline unavailable", HTML)

    def test_zero_support_has_dedicated_status(self):
        self.assertIn("const noSupport = raw(support) === 0", JS)
        self.assertIn("status = 'INSUFFICIENT_SUPPORT'", JS)
        self.assertNotIn("set('prauc', 0)", JS)


if __name__ == "__main__":
    unittest.main()
