import unittest

from src.portfolio.validate_public_portfolio import validate


class PublicPortfolioClosureTest(unittest.TestCase):
    def test_all_public_closure_gates_pass(self):
        failures = [row for row in validate() if row["status"] != "PASS"]
        self.assertEqual([], failures)


if __name__ == "__main__":
    unittest.main()
