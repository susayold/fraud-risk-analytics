from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HTML = (ROOT / "part-7.html").read_text(encoding="utf-8")
JS = (ROOT / "js" / "part-7.js").read_text(encoding="utf-8")


class SimulatedEconomicsBoundaryTests(unittest.TestCase):
    def test_cost_is_explicitly_simulated(self):
        for text in ("SIMULATED ECONOMICS", "not booked savings", "NOT ACTUAL SAVINGS", "SIMULATED POLICY COST"):
            self.assertIn(text, HTML)
        self.assertIn("simulated_total_cost", JS)
        self.assertIn("allow_all", JS)

    def test_cost_chart_fails_closed_without_aggregate_components(self):
        self.assertIn("COST DECOMPOSITION NOT AVAILABLE IN PUBLIC AGGREGATE", JS)
        self.assertIn("allow-all baseline", HTML)


if __name__ == "__main__":
    unittest.main()
