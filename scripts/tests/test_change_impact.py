import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import change_impact


class ChangeImpactTests(unittest.TestCase):
    def test_repo_name_normalization(self):
        self.assertEqual(
            "atlasreaper311/atlas-corpus",
            change_impact.repo_name("https://github.com/AtlasReaper311/atlas-corpus.git"),
        )

    def test_transitive_consumers(self):
        reverse = {
            "atlas-corpus": {"atlas-api-public"},
            "atlas-api-public": {"atlas-systems"},
        }
        direct, indirect = change_impact.transitive_consumers({"atlas-corpus"}, reverse)
        self.assertEqual({"atlas-api-public"}, direct)
        self.assertEqual({"atlas-systems"}, indirect)

    def test_classifies_contract_runtime_as_high(self):
        categories, risk = change_impact.classify_files(
            ["src/router.js", "openapi.json"]
        )
        self.assertIn("runtime", categories)
        self.assertIn("contract", categories)
        self.assertEqual("high", risk)


if __name__ == "__main__":
    unittest.main()
