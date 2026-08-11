import json
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
ROOT = SCRIPTS.parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import model_promotion_coverage


class FakeClient:
    def __init__(self, contents):
        self.contents = contents

    def rest_get_optional(self, path):
        marker = "/contents/"
        if marker not in path:
            raise AssertionError(path)
        repo = path.split("/repos/AtlasReaper311/", 1)[1].split("/contents/", 1)[0]
        content_path = path.split(marker, 1)[1]
        text = self.contents.get((repo, content_path))
        if text is None:
            return None
        import base64

        return {
            "type": "file",
            "encoding": "base64",
            "content": base64.b64encode(text.encode("utf-8")).decode("ascii"),
        }


class ModelPromotionCoverageTests(unittest.TestCase):
    def load_config(self):
        return json.loads(
            (ROOT / "policy" / "model-promotion-coverage.json").read_text(
                encoding="utf-8"
            )
        )

    def test_config_targets_private_user_project_two(self):
        config = model_promotion_coverage.load_config(
            ROOT / "policy" / "model-promotion-coverage.json"
        )

        self.assertEqual("AtlasReaper311", config["owner"])
        self.assertEqual(2, config["project_number"])
        self.assertEqual("atlas-eval-harness", config["eval_harness_repository"])
        self.assertEqual(5, len(config["capabilities"]))

    def test_build_rows_marks_missing_promotion_record_honestly(self):
        config = self.load_config()
        client = FakeClient(
            {
                ("atlas-postmortem", "src/atlas_postmortem/config.py"): (
                    'model: str = field(default_factory=lambda: os.environ.get("ATLAS_PM_MODEL", "qwen2.5:32b"))'
                ),
                (
                    "atlas-eval-harness",
                    "cases/postmortem-inc-20260713-104620.toml",
                ): 'task_type = "postmortem-drafting"',
            }
        )
        capability = next(
            item for item in config["capabilities"] if item["id"] == "postmortem-drafting"
        )

        live_model, evidence, warnings = model_promotion_coverage.resolve_live_model(
            client, capability, config["owner"]
        )
        cases, case_paths = model_promotion_coverage.eval_case_count(
            client, config, capability
        )
        promoted, promotion_evidence, missing = model_promotion_coverage.promotion_model(
            client, config, capability
        )

        self.assertEqual("qwen2.5:32b", live_model)
        self.assertIn("atlas-postmortem:src/atlas_postmortem/config.py", evidence)
        self.assertEqual([], warnings)
        self.assertEqual(1, cases)
        self.assertEqual(["cases/postmortem-inc-20260713-104620.toml"], case_paths)
        self.assertEqual("", promoted)
        self.assertEqual("", promotion_evidence)
        self.assertEqual(
            "Promotion record missing",
            model_promotion_coverage.coverage_status(
                capability,
                live_model=live_model,
                eval_cases=cases,
                promoted_model=promoted,
                missing_promotions=missing,
            ),
        )

    def test_low_risk_override_stays_visible_as_exempt(self):
        config = self.load_config()
        capability = next(
            item for item in config["capabilities"] if item["id"] == "session-summarisation"
        )

        self.assertEqual(
            "Exempt - low risk",
            model_promotion_coverage.coverage_status(
                capability,
                live_model="llama3.1:8b",
                eval_cases=0,
                promoted_model="",
                missing_promotions=[],
            ),
        )
        self.assertEqual(
            "Done",
            model_promotion_coverage.status_for("Monitor only", "Exempt - low risk"),
        )
        self.assertEqual(
            "Monitor only",
            model_promotion_coverage.action_for(capability, "Exempt - low risk"),
        )

    def test_no_eval_case_is_not_promoted(self):
        config = self.load_config()
        capability = next(
            item for item in config["capabilities"] if item["id"] == "ramone-rag-generation"
        )

        self.assertEqual(
            "No eval case",
            model_promotion_coverage.coverage_status(
                capability,
                live_model="llama3.1:8b",
                eval_cases=0,
                promoted_model="",
                missing_promotions=[],
            ),
        )
        self.assertEqual(
            "Add eval case",
            model_promotion_coverage.action_for(capability, "No eval case"),
        )
        self.assertEqual("Todo", model_promotion_coverage.status_for("Add eval case", "No eval case"))

    def test_action_is_computed_from_coverage(self):
        config = self.load_config()
        capability = config["capabilities"][0]

        self.assertEqual(
            "No action",
            model_promotion_coverage.action_for(capability, "Promoted - matches live"),
        )
        self.assertEqual(
            "Decide live/promoted mismatch",
            model_promotion_coverage.action_for(
                capability, "Promoted - does not match live"
            ),
        )
        self.assertEqual(
            "Create promotion record",
            model_promotion_coverage.action_for(capability, "Promotion record missing"),
        )

    def test_build_plan_creates_draft_items_and_fields(self):
        config = self.load_config()
        rows = [
            {
                "title": "Example",
                "body": "body",
                "capability_id": "example",
                "source": "AtlasReaper311/example",
                "risk": "High",
                "action_needed": "Add eval case",
                "next_step": "Add one case.",
                "live_model": "llama3.1:8b",
                "promoted_model": "",
                "eval_case_count": 0,
                "coverage_status": "No eval case",
                "status": "Todo",
                "last_verified": "2026-08-11",
            }
        ]
        project = {
            "id": "project-id",
            "title": "Model Promotion and Eval Coverage",
            "items": {"nodes": []},
        }

        plan = model_promotion_coverage.build_plan(project, rows, config)

        self.assertEqual(1, plan["summary"]["items_to_add"])
        self.assertIn({"action": "add_item", "title": "Example"}, plan["actions"])
        self.assertIn(
            {
                "action": "set_field",
                "item_id": "<after-add>",
                "title": "Example",
                "field": "Coverage Status",
                "value": "No eval case",
            },
            plan["actions"],
        )

    def test_build_plan_skips_unchanged_project_fields(self):
        config = self.load_config()
        row = {
            "title": "Example",
            "body": "body",
            "capability_id": "example",
            "source": "AtlasReaper311/example",
            "risk": "High",
            "action_needed": "Add eval case",
            "next_step": "Add one case.",
            "live_model": "llama3.1:8b",
            "promoted_model": "",
            "eval_case_count": 0,
            "coverage_status": "No eval case",
            "status": "Todo",
            "last_verified": "2026-08-11",
            "last_synced": "2026-08-11",
            "stale_days": 0,
            "evidence": "AtlasReaper311/example:.env.example",
            "attention": "Needs coverage",
        }
        project = {
            "id": "project-id",
            "title": "Model Promotion and Eval Coverage",
            "items": {
                "nodes": [
                    {
                        "id": "item-id",
                        "fieldValues": {
                            "nodes": [
                                {
                                    "__typename": "ProjectV2ItemFieldTextValue",
                                    "text": "example",
                                    "field": {"name": "Capability ID"},
                                },
                                {
                                    "__typename": "ProjectV2ItemFieldTextValue",
                                    "text": "AtlasReaper311/example",
                                    "field": {"name": "Source"},
                                },
                                {
                                    "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                    "name": "High",
                                    "field": {"name": "Risk"},
                                },
                                {
                                    "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                    "name": "Add eval case",
                                    "field": {"name": "Action Needed"},
                                },
                                {
                                    "__typename": "ProjectV2ItemFieldTextValue",
                                    "text": "Add one case.",
                                    "field": {"name": "Next Step"},
                                },
                                {
                                    "__typename": "ProjectV2ItemFieldTextValue",
                                    "text": "llama3.1:8b",
                                    "field": {"name": "Live Model"},
                                },
                                {
                                    "__typename": "ProjectV2ItemFieldNumberValue",
                                    "number": 0,
                                    "field": {"name": "Eval Case Count"},
                                },
                                {
                                    "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                    "name": "No eval case",
                                    "field": {"name": "Coverage Status"},
                                },
                                {
                                    "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                    "name": "Todo",
                                    "field": {"name": "Status"},
                                },
                                {
                                    "__typename": "ProjectV2ItemFieldDateValue",
                                    "date": "2026-08-11",
                                    "field": {"name": "Last Verified"},
                                },
                                {
                                    "__typename": "ProjectV2ItemFieldDateValue",
                                    "date": "2026-08-11",
                                    "field": {"name": "Last Synced"},
                                },
                                {
                                    "__typename": "ProjectV2ItemFieldNumberValue",
                                    "number": 0,
                                    "field": {"name": "Stale Days"},
                                },
                                {
                                    "__typename": "ProjectV2ItemFieldTextValue",
                                    "text": "AtlasReaper311/example:.env.example",
                                    "field": {"name": "Evidence"},
                                },
                                {
                                    "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                    "name": "Needs coverage",
                                    "field": {"name": "Attention"},
                                },
                            ]
                        },
                        "content": {
                            "__typename": "DraftIssue",
                            "id": "draft-id",
                            "title": "Example",
                            "body": "body",
                        },
                    }
                ]
            },
        }

        plan = model_promotion_coverage.build_plan(project, [row], config)

        self.assertEqual(0, plan["summary"]["field_updates"])
        self.assertEqual([], plan["actions"])


if __name__ == "__main__":
    unittest.main()
