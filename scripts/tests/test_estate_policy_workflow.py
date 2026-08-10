from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "estate-policy.yml"


def step_block(text: str, name: str) -> str:
    marker = f"      - name: {name}\n"
    start = text.index(marker)
    end = text.find("\n      - name: ", start + len(marker))
    return text[start:] if end < 0 else text[start:end]


class EstatePolicyWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_primary_checkout_fetches_history_for_ancestry_tests(self) -> None:
        block = step_block(self.text, "Check out atlas-infra")
        self.assertIn("fetch-depth: 0", block)

    def test_consolidated_notification_matches_notify_assurance_cli(self) -> None:
        block = step_block(self.text, "Report consolidated findings")
        self.assertIn("NOTIFY_TOKEN: ${{ secrets.NOTIFY_TOKEN }}", block)
        self.assertIn('--title "Estate policy findings"', block)
        self.assertIn('--level "$LEVEL"', block)
        self.assertIn('--message "${ERRORS:-0} errors and ${WARNINGS:-0} warnings', block)
        self.assertIn('--url "$RUN_URL"', block)
        self.assertNotIn("--conformance", block)
        self.assertNotIn("--output reports/assurance-summary.json", block)

    def test_notification_requires_report_and_findings(self) -> None:
        block = step_block(self.text, "Report consolidated findings")
        self.assertIn("hashFiles('reports/estate-policy.json') != ''", block)
        self.assertIn("steps.policy.outputs.errors != '0'", block)
        self.assertIn("steps.policy.outputs.warnings != '0'", block)
        self.assertIn("continue-on-error: true", block)

    def test_policy_failure_remains_blocking_after_reporting(self) -> None:
        block = step_block(self.text, "Preserve blocking policy result")
        self.assertIn("if: always() && steps.policy.outcome == 'failure'", block)
        self.assertIn("exit 1", block)


if __name__ == "__main__":
    unittest.main()
