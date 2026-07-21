from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.readme_contract import all_readme_findings, check_local, order_findings

ROOT = Path(__file__).resolve().parents[2]
POLICY = json.loads((ROOT / "policy" / "repository-hygiene.json").read_text(encoding="utf-8"))
REPOSITORY = "AtlasReaper311/example-repository"


def compliant_readme() -> str:
    return """<div align=\"center\">\n  <img src=\"https://raw.githubusercontent.com/AtlasReaper311/AtlasReaper311/main/atlas-icon-dark-256.png\" width=\"88\" alt=\"Atlas Systems\"/>\n</div>\n\n# example-repository\n\n```\n┌─────────────────────────────────────────────┐\n│  ATLAS SYSTEMS // example-repository        │\n│  deterministic example                      │\n└─────────────────────────────────────────────┘\n```\n\n![CI](https://github.com/AtlasReaper311/example-repository/actions/workflows/ci.yml/badge.svg)\n![Python](https://img.shields.io/badge/python-3.12-f5a623?style=flat-square&labelColor=0a0a0f)\n![Scope](https://img.shields.io/badge/scope-example-aaa9a0?style=flat-square&labelColor=0a0a0f)\n![Cost](https://img.shields.io/badge/cost-%C2%A30-aaa9a0?style=flat-square&labelColor=0a0a0f)\n\nAn example repository used to prove the README contract.\n\n## Usage\n\nRun the example.\n\n## How it fits into Atlas Systems\n\nIt validates one source-local README without creating a repository inventory.\n\nThe transferable principle is to validate presentation from the same source that owns it.\n\n---\n\nPart of [atlas-systems.uk](https://atlas-systems.uk)\n"""


class ReadmeContractTests(unittest.TestCase):
    def test_compliant_readme_has_no_findings(self) -> None:
        self.assertEqual(
            [],
            all_readme_findings(REPOSITORY, compliant_readme(), POLICY, has_license=False),
        )

    def test_footer_must_be_final_non_empty_line(self) -> None:
        text = compliant_readme() + "\n## Too late\n"
        rules = {item.rule_id for item in order_findings(REPOSITORY, text, POLICY)}
        self.assertIn("footer-order", rules)

    def test_how_it_fits_must_be_final_h2(self) -> None:
        text = compliant_readme().replace(
            "\n---\n\nPart of [atlas-systems.uk]",
            "\n## Extra section\n\nNo.\n\n---\n\nPart of [atlas-systems.uk]",
        )
        rules = {item.rule_id for item in order_findings(REPOSITORY, text, POLICY)}
        self.assertIn("atlas-fit-order", rules)

    def test_local_validation_is_source_local(self) -> None:
        with tempfile.TemporaryDirectory() as holder:
            root = Path(holder)
            readme = root / "README.md"
            readme.write_text(compliant_readme(), encoding="utf-8")
            self.assertEqual(
                0,
                check_local(
                    repository=REPOSITORY,
                    readme_path=readme,
                    license_path=root / "LICENSE",
                    policy_path=ROOT / "policy" / "repository-hygiene.json",
                ),
            )


if __name__ == "__main__":
    unittest.main()
