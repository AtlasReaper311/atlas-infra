from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "github-provider-guard-wave-4b-reconcile.sh"
PLAN = ROOT / "docs" / "github-provider-guard-wave-4-plan.md"
RECEIPT = ROOT / "reports" / "github-provider-guard-wave-4-inspection-receipt.json"


class GithubProviderGuardWave4BTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = SCRIPT.read_text(encoding="utf-8")
        cls.plan = PLAN.read_text(encoding="utf-8")
        cls.receipt = RECEIPT.read_text(encoding="utf-8")

    def test_dora_identity_and_ruleset_are_exact(self) -> None:
        self.assertIn('REPOSITORY="atlas-dora"', self.script)
        self.assertIn('EXPECTED_MAIN_SHA="fff7c2c5453240dafd693e8a4de645beab523031"', self.script)
        self.assertIn('EXPECTED_RULESET_ID="19581236"', self.script)
        self.assertIn('EXPECTED_RULESET_NAME="Atlas Gardener native auto-merge barrier"', self.script)
        self.assertIn('"ruleset_id": 19581236', self.receipt)

    def test_reconciliation_preserves_existing_required_checks(self) -> None:
        self.assertIn('EXPECTED_NATIVE_CONTEXT="check"', self.script)
        self.assertIn('EXPECTED_BARRIER_CONTEXT="Gardener native auto-merge barrier"', self.script)
        self.assertIn('include: ["refs/heads/main"]', self.script)
        self.assertIn("strict_required_status_checks_policy: false", self.script)
        self.assertIn("adds only", self.plan)

    def test_provider_mutation_surface_is_existing_ruleset_update_only(self) -> None:
        self.assertEqual(self.script.count("--method PUT"), 1)
        self.assertNotIn("--method POST", self.script)
        self.assertNotIn("--method DELETE", self.script)
        self.assertNotIn("--method PATCH", self.script)
        self.assertIn('/rulesets/${EXPECTED_RULESET_ID}', self.script)

    def test_baseline_requires_required_status_only_before_update(self) -> None:
        self.assertIn('([.rules[].type] | sort) == ["required_status_checks"]', self.script)
        self.assertIn('([.rules[] | select(.type == "required_status_checks")][0].parameters.strict_required_status_checks_policy == false)', self.script)

    def test_reconciled_rules_add_only_guard_types(self) -> None:
        for rule_type in ("deletion", "non_fast_forward", "pull_request", "required_status_checks"):
            self.assertIn(rule_type, self.script)
        self.assertIn("required_approving_review_count: 0", self.script)
        self.assertIn("required_review_thread_resolution: false", self.script)

    def test_gardener_and_repository_automation_are_preserved(self) -> None:
        self.assertIn('EXPECTED_GARDENER_VARIABLE_VALUE="false"', self.script)
        self.assertIn("ATLAS_GARDENER_WRITE_TARGETS_JSON", self.script)
        self.assertIn(".allow_auto_merge == false", self.script)
        self.assertIn("DEPENDABOT_AUTOMERGE_ENABLED", self.script)
        for forbidden in (
            "gh variable set",
            "gh variable delete",
            "gh secret",
            "gh pr merge",
            "gh workflow run",
            "gh release create",
        ):
            self.assertNotIn(forbidden, self.script)

    def test_profile_repository_is_held(self) -> None:
        self.assertNotIn("AtlasReaper311/AtlasReaper311", self.script)
        self.assertIn("explicitly held", self.plan)
        self.assertIn('"provider_change_authorised": false', self.receipt)

    def test_apply_requires_exact_confirmation_and_wave_order(self) -> None:
        self.assertIn("APPLY GITHUB PROVIDER GUARD WAVE 4B", self.script)
        self.assertIn("Wave 4B remains separately provider-write gated after Wave 4A", self.plan)
        self.assertIn("258 / 2 / 0", self.plan)
        self.assertIn("259 / 1 / 0", self.plan)


if __name__ == "__main__":
    unittest.main()
