import json
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import dependabot_automerge_policy as policy


BASE_METADATA = {
    "enabled": "true",
    "dependency_name": "playwright",
    "dependency_type": "direct:development",
    "update_type": "version-update:semver-patch",
    "package_ecosystem": "npm",
    "previous_version": "1.2.3",
    "new_version": "1.2.4",
    "dependency_group": "",
    "maintainer_changes": "false",
}


class Response:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class DependabotAutomergePolicyTests(unittest.TestCase):
    def decision(self, **changes):
        metadata = dict(BASE_METADATA)
        metadata.update(changes)
        return policy.metadata_decision(**metadata)

    def test_only_opted_in_npm_patch_development_updates_are_eligible(self):
        self.assertTrue(self.decision().eligible)
        self.assertFalse(self.decision(enabled="false").eligible)
        self.assertFalse(self.decision(package_ecosystem="pip").eligible)
        self.assertFalse(self.decision(dependency_type="direct:production").eligible)
        self.assertFalse(
            self.decision(update_type="version-update:semver-minor").eligible
        )

    def test_groups_maintainer_changes_and_pre_one_versions_are_ineligible(self):
        self.assertFalse(self.decision(dependency_group="npm-minor-patch").eligible)
        self.assertFalse(self.decision(maintainer_changes="true").eligible)
        self.assertFalse(self.decision(previous_version="0.9.9").eligible)
        self.assertFalse(self.decision(new_version="0.9.10").eligible)

    def test_osv_active_advisory_blocks_update(self):
        decision = policy.evaluate_policy(
            **BASE_METADATA,
            osv_lookup=lambda _name, _version: (True, "osv-active-advisory"),
        )
        self.assertFalse(decision.eligible)
        self.assertEqual("osv-active-advisory", decision.reason)

    def test_osv_outage_blocks_update_without_raising(self):
        decision = policy.evaluate_policy(
            **BASE_METADATA,
            osv_lookup=lambda _name, _version: (None, "osv-unavailable"),
        )
        self.assertFalse(decision.eligible)
        self.assertEqual("osv-unavailable", decision.reason)

    def test_osv_clear_update_is_eligible(self):
        decision = policy.evaluate_policy(
            **BASE_METADATA,
            osv_lookup=lambda _name, _version: (False, "osv-clear"),
        )
        self.assertTrue(decision.eligible)
        self.assertEqual("eligible", decision.reason)

    def test_query_osv_ignores_withdrawn_advisories(self):
        vulnerable, reason = policy.query_osv(
            "playwright",
            "1.2.4",
            opener=lambda *_args, **_kwargs: Response(
                {"vulns": [{"id": "OSV-1", "withdrawn": "2026-01-01"}]}
            ),
        )
        self.assertFalse(vulnerable)
        self.assertEqual("osv-clear", reason)

    def test_query_osv_fails_closed_on_invalid_json(self):
        class InvalidResponse(Response):
            def read(self):
                return b"not-json"

        vulnerable, reason = policy.query_osv(
            "playwright",
            "1.2.4",
            opener=lambda *_args, **_kwargs: InvalidResponse({}),
        )
        self.assertIsNone(vulnerable)
        self.assertEqual("osv-unavailable", reason)

    def test_reusable_workflow_revokes_only_policy_created_auto_merge(self):
        workflow = (
            Path(__file__).resolve().parents[2]
            / ".github"
            / "workflows"
            / "dependabot-review.yml"
        ).read_text(encoding="utf-8")

        self.assertIn('gh pr merge "$PR_URL" --disable-auto', workflow)
        self.assertIn('= "github-actions[bot]"', workflow)
        self.assertNotIn("gh pr review --approve", workflow)


if __name__ == "__main__":
    unittest.main()
