import datetime as dt
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
ROOT = SCRIPTS.parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import estate_rollout_board


class EstateRolloutBoardTests(unittest.TestCase):
    def load_config(self):
        return json.loads(
            (ROOT / "policy" / "estate-rollout-board.json").read_text(
                encoding="utf-8"
            )
        )

    def test_config_loads_expected_project_boundary(self):
        config = estate_rollout_board.load_config(
            ROOT / "policy" / "estate-rollout-board.json"
        )

        self.assertEqual("AtlasReaper311", config["owner"])
        self.assertEqual(1, config["project_number"])
        self.assertEqual(3, config["archive_after_done_days"])
        self.assertEqual("archive", estate_rollout_board.retention_action(config))
        self.assertEqual(
            "P-04 Honours Project",
            estate_rollout_board.pillar_for("addiction-honours-project", config),
        )
        self.assertEqual(
            "P-03 DevOps Core",
            estate_rollout_board.pillar_for("atlas-infra", config),
        )

    def test_stage_rules_handle_draft_gated_open_and_merged(self):
        config = self.load_config()

        self.assertEqual(
            "Draft - Awaiting Review",
            estate_rollout_board.stage_for({"draft": True, "state": "open"}, config),
        )
        self.assertEqual(
            "Draft - Awaiting Review",
            estate_rollout_board.stage_for(
                {
                    "draft": False,
                    "state": "open",
                    "title": "Ready",
                    "body": "No merge until rollout gate approval.",
                },
                config,
            ),
        )
        self.assertEqual(
            "In Progress",
            estate_rollout_board.stage_for(
                {"draft": False, "state": "open", "body": ""}, config
            ),
        )
        self.assertEqual(
            "Live / Verified",
            estate_rollout_board.stage_for(
                {"state": "closed", "merged_at": "2026-08-11T10:00:00Z"},
                config,
            ),
        )

    def test_excludes_dependabot_or_dependency_noise(self):
        config = self.load_config()

        self.assertTrue(
            estate_rollout_board.is_excluded(
                {
                    "user": {"login": "dependabot", "type": "Bot"},
                    "labels": [],
                },
                config,
            )
        )
        self.assertTrue(
            estate_rollout_board.is_excluded(
                {
                    "user": {"login": "dependabot[bot]", "type": "Bot"},
                    "labels": [{"name": "dependabot-major"}],
                    "title": "chore(deps): bump actions/setup-python",
                },
                config,
            )
        )
        self.assertTrue(
            estate_rollout_board.is_excluded(
                {
                    "user": {"login": "AtlasReaper311", "type": "User"},
                    "labels": [],
                    "title": "build(deps): bump the github-actions group",
                },
                config,
            )
        )
        self.assertTrue(
            estate_rollout_board.is_excluded(
                {
                    "user": {"login": "AtlasReaper311", "type": "User"},
                    "labels": [{"name": "dependencies"}],
                },
                config,
            )
        )

    def test_build_plan_archives_closed_project_item_after_grace_period(self):
        config = self.load_config()
        project = {
            "id": "project-id",
            "title": "Estate Rollout Board",
            "items": {
                "nodes": [
                    {
                        "id": "item-id",
                        "content": {
                            "__typename": "PullRequest",
                            "url": "https://github.com/AtlasReaper311/atlas-infra/pull/99",
                            "number": 99,
                            "state": "MERGED",
                            "title": "Old merged PR",
                            "mergedAt": "2026-08-01T10:00:00Z",
                            "closedAt": "2026-08-01T10:00:00Z",
                            "repository": {
                                "nameWithOwner": "AtlasReaper311/atlas-infra"
                            },
                        },
                    }
                ]
            },
        }

        plan = estate_rollout_board.build_plan(
            project,
            {},
            config,
            now=dt.datetime(2026, 8, 11, 10, tzinfo=dt.UTC),
        )

        self.assertEqual(1, plan["summary"]["items_to_archive"])
        self.assertIn(
            {
                "action": "archive_item",
                "item_id": "item-id",
                "url": "https://github.com/AtlasReaper311/atlas-infra/pull/99",
                "reason": "closed for at least 3 days",
            },
            plan["actions"],
        )

    def test_build_plan_keeps_recently_closed_item_done_until_grace_expires(self):
        config = self.load_config()
        project = {
            "id": "project-id",
            "title": "Estate Rollout Board",
            "items": {
                "nodes": [
                    {
                        "id": "item-id",
                        "content": {
                            "__typename": "PullRequest",
                            "url": "https://github.com/AtlasReaper311/atlas-infra/pull/99",
                            "state": "MERGED",
                            "title": "Recent merged PR",
                            "mergedAt": "2026-08-10T10:00:00Z",
                            "closedAt": "2026-08-10T10:00:00Z",
                            "repository": {
                                "nameWithOwner": "AtlasReaper311/atlas-infra"
                            },
                        },
                    }
                ]
            },
        }

        plan = estate_rollout_board.build_plan(
            project,
            {},
            config,
            now=dt.datetime(2026, 8, 11, 10, tzinfo=dt.UTC),
        )

        self.assertEqual(0, plan["summary"]["items_to_archive"])
        self.assertIn(
            {
                "action": "set_field",
                "item_id": "item-id",
                "url": "https://github.com/AtlasReaper311/atlas-infra/pull/99",
                "field": "Status",
                "value": "Done",
            },
            plan["actions"],
        )

    def test_done_retention_can_be_configured_to_delete_project_items(self):
        config = self.load_config()
        config["done_retention_action"] = "delete"
        project = {
            "id": "project-id",
            "title": "Estate Rollout Board",
            "items": {
                "nodes": [
                    {
                        "id": "item-id",
                        "content": {
                            "__typename": "PullRequest",
                            "url": "https://github.com/AtlasReaper311/atlas-infra/pull/99",
                            "state": "MERGED",
                            "title": "Old merged PR",
                            "mergedAt": "2026-08-01T10:00:00Z",
                            "closedAt": "2026-08-01T10:00:00Z",
                            "repository": {
                                "nameWithOwner": "AtlasReaper311/atlas-infra"
                            },
                        },
                    }
                ]
            },
        }

        plan = estate_rollout_board.build_plan(
            project,
            {},
            config,
            now=dt.datetime(2026, 8, 11, 10, tzinfo=dt.UTC),
        )

        self.assertIn(
            {
                "action": "delete_item",
                "item_id": "item-id",
                "url": "https://github.com/AtlasReaper311/atlas-infra/pull/99",
                "reason": "closed for at least 3 days",
            },
            plan["actions"],
        )

    def test_build_plan_archives_open_item_that_no_longer_matches_rules(self):
        config = self.load_config()
        project = {
            "id": "project-id",
            "title": "Estate Rollout Board",
            "items": {
                "nodes": [
                    {
                        "id": "item-id",
                        "content": {
                            "__typename": "PullRequest",
                            "url": "https://github.com/AtlasReaper311/atlas-infra/pull/146",
                            "state": "OPEN",
                            "title": "build(deps): bump github-actions",
                            "mergedAt": None,
                            "closedAt": None,
                            "repository": {
                                "nameWithOwner": "AtlasReaper311/atlas-infra"
                            },
                        },
                    }
                ]
            },
        }

        plan = estate_rollout_board.build_plan(
            project,
            {},
            config,
            now=dt.datetime(2026, 8, 11, 10, tzinfo=dt.UTC),
        )

        self.assertEqual(1, plan["summary"]["items_to_archive"])
        self.assertIn(
            {
                "action": "archive_item",
                "item_id": "item-id",
                "url": "https://github.com/AtlasReaper311/atlas-infra/pull/146",
                "reason": "open item no longer matches rollout board rules",
            },
            plan["actions"],
        )

    def test_write_report_creates_parent_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nested" / "report.json"
            estate_rollout_board.write_report(path, {"ok": True})

            self.assertEqual({"ok": True}, json.loads(path.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
