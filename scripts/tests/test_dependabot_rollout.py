import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import dependabot_rollout
from detect_ecosystem import Detection


class DependabotRolloutTests(unittest.TestCase):
    def test_production_config_is_weekly_grouped_and_branch_specific(self):
        entry = {"lifecycle": "production", "runtime_service": True}
        detections = [
            Detection("github-actions", ("/",)),
            Detection("npm", ("/", "/web")),
        ]

        text = dependabot_rollout.render_dependabot(detections, entry, "trunk")

        self.assertEqual(
            dependabot_rollout.validate_dependabot_text(
                text, detections, entry, "trunk"
            ),
            [],
        )
        self.assertEqual(text.count('interval: "weekly"'), 3)
        self.assertEqual(text.count('day: "monday"'), 3)
        self.assertEqual(text.count('target-branch: "trunk"'), 3)
        self.assertNotIn('          - "major"', text)

    def test_active_non_runtime_monthly_schedule_has_no_weekly_day(self):
        entry = {"lifecycle": "active", "runtime_service": False}
        detections = [Detection("pip", ("/",))]

        text = dependabot_rollout.render_dependabot(detections, entry, "main")

        self.assertIn('interval: "monthly"', text)
        self.assertNotIn("      day:", text)
        self.assertIn("open-pull-requests-limit: 5", text)
        self.assertEqual(
            dependabot_rollout.validate_dependabot_text(
                text, detections, entry, "main"
            ),
            [],
        )

    def test_deprecated_repository_gets_no_files(self):
        repository = {
            "repository": "AtlasReaper311/simple-proxy",
            "default_branch": "main",
            "archived": False,
        }
        entry = {
            "lifecycle": "deprecated",
            "scope": "internal",
            "provenance": "external-derived",
        }

        plan, files = dependabot_rollout._repo_plan(
            object(), repository, entry, "workflow"
        )

        self.assertEqual(plan["action"], "security-alerts-only")
        self.assertEqual(files, {})
        self.assertIn("do not enable version updates", plan["notes"][0])

    def test_archived_repository_is_skipped(self):
        repository = {
            "repository": "AtlasReaper311/atlas-cv",
            "default_branch": "main",
            "archived": True,
        }
        entry = {"lifecycle": "archived"}

        plan, files = dependabot_rollout._repo_plan(
            object(), repository, entry, "workflow"
        )

        self.assertEqual(plan["action"], "skip")
        self.assertEqual(files, {})

    def test_summary_marks_private_free_tier_automerge_inert(self):
        plan = {
            "repository": "AtlasReaper311/private",
            "lifecycle": "active",
            "ecosystems": ["npm"],
            "schedule": "monthly",
            "grouped": "minor and patch",
            "action": "propose",
            "required_checks_state": "configured",
            "allow_auto_merge": True,
            "free_tier_automerge_eligible": False,
        }
        reconciliation = {
            "reconciliation_digest": "a" * 64,
            "github_only": [],
            "registry_only": [],
        }

        markdown = dependabot_rollout._summary([plan], reconciliation)

        self.assertIn("| inert |", markdown)


if __name__ == "__main__":
    unittest.main()
