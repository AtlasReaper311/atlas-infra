import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "estate-rollout-board-sync.yml"


class EstateRolloutBoardWorkflowTests(unittest.TestCase):
    def test_scheduled_runs_are_dry_run_only(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn('cron: "37 7 * * *"', workflow)
        self.assertIn(
            "if: ${{ github.event_name == 'workflow_dispatch' && inputs.apply == true }}",
            workflow,
        )
        self.assertNotIn(
            "github.event_name == 'schedule' || inputs.apply == true",
            workflow,
        )

    def test_manual_apply_defaults_off(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn('description: "Apply project updates; false writes a dry-run report only"', workflow)
        self.assertIn("default: false", workflow)
        self.assertIn("type: boolean", workflow)


if __name__ == "__main__":
    unittest.main()
