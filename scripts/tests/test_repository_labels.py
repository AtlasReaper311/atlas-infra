from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.repository_hygiene import label_findings
from scripts.repository_labels import render_markdown

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "policy" / "repository-hygiene.json"


class RepositoryLabelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))

    def _labels(self) -> list[dict[str, str]]:
        return [
            {
                "name": item["name"],
                "color": item["color"],
                "description": item["description"],
            }
            for item in self.policy["pull_request_labels"]
        ]

    def test_compliant_labels_have_no_findings(self) -> None:
        self.assertEqual(
            [],
            label_findings("AtlasReaper311/demo-repo", self._labels(), self.policy),
        )

    def test_missing_label_is_reported(self) -> None:
        labels = self._labels()[1:]
        findings = label_findings("AtlasReaper311/demo-repo", labels, self.policy)
        self.assertEqual(["missing-label"], [finding.rule_id for finding in findings])

    def test_color_and_description_drift_are_reported(self) -> None:
        labels = self._labels()
        labels[0]["color"] = "000000"
        labels[0]["description"] = "wrong"
        findings = label_findings("AtlasReaper311/demo-repo", labels, self.policy)
        self.assertEqual(
            {"label-color", "label-description"},
            {finding.rule_id for finding in findings},
        )

    def test_zero_finding_report_is_explicit(self) -> None:
        report = {
            "scope": "public",
            "mode": "enforce",
            "summary": {"repositories_checked": 31, "finding_count": 0},
            "findings": [],
        }
        rendered = render_markdown(report)
        self.assertIn("Repositories checked: **31**", rendered)
        self.assertIn("Findings: **0**", rendered)


if __name__ == "__main__":
    unittest.main()
