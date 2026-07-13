import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import estate_policy


class EstatePolicyTests(unittest.TestCase):
    def test_full_sha_is_accepted(self):
        workflow = "steps:\n  - uses: owner/action@0123456789012345678901234567890123456789\n"
        findings = estate_policy.action_ref_findings("owner/repo", "ci.yml", workflow)
        self.assertEqual([], findings)

    def test_tag_is_warning(self):
        workflow = "steps:\n  - uses: actions/checkout@v4\n"
        findings = estate_policy.action_ref_findings("owner/repo", "ci.yml", workflow)
        self.assertEqual(1, len(findings))
        self.assertEqual("actions-pin", findings[0].rule)


if __name__ == "__main__":
    unittest.main()
