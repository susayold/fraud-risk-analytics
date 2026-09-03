import re
import unittest
from pathlib import Path


class LinkTests(unittest.TestCase):
    def test_local_deep_links_resolve(self):
        root = Path(".")
        html = (root / "part-9.html").read_text(encoding="utf-8")
        links = re.findall(r'href="(part-[1-9]\.html|docs/[^"#]+|reports/[^"#]+)"', html)
        self.assertTrue(links)
        self.assertTrue(all((root / link).exists() for link in links))
