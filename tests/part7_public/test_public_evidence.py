import unittest

from src.part7_public.validate_public_evidence import validate


class TestPart7PublicEvidence(unittest.TestCase):
    def test_public_evidence_contract(self):
        failures = [name for name, ok, _ in validate() if not ok]
        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
