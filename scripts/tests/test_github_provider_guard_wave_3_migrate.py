from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "github-provider-guard-wave-3-migrate.sh"
PLAN = ROOT / "docs" / "github-provider-guard-wave-3-plan.md"
RECEIPT = ROOT / "reports" / "github-provider-guard-wave-3-inspection-receipt.json"


class GithubProviderGuardWave3MigrateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = SCRIPT.read_text(encoding="utf-8")
        cls.plan = PLAN.read_text(encoding="utf-8")
        cls.receipt = RECEIPT.read_text(encoding="utf-8")

    def test_scope_is_exactly_five_reviewed_repositories(self) -> None:
        for repository in (
            "atlas-doc-viewer",
            "atlas-quota-watch",
            "site-pulse",
            "specular-sonify",
            "status",
        ):
            self.assertIn(repository, self.script)
            self.assertIn(repository, self.plan)
        self.assertNotIn("atlas-journey-watch|", self.script)

    def test_reviewed_inspection_receipt_is_pinned(self) -> None:
        self.assertIn(
            "a18e383a80637dd742108c271b25e30d9cf607a495b9c5680ea20d9c3f7056d8",
            self.plan,
        )
        self.assertIn(
            "a18e383a80637dd742108c271b25e30d9cf607a495b9c5680ea20d9c3f7056d8",
            self.receipt,
        )
        self.assertIn('"manifest_entries": 64', self.receipt)
        self.assertIn('"digest_mismatches": 0', self.receipt)

    def test_replacement_ruleset_preserves_both_required_checks(self) -> None:
        self.assertIn('GARDENER_BARRIER="Gardener native auto-merge barrier"', self.script)
        for context in (
            "Static document validation",
            "validate",
            "Worker validation",
            "Worker configuration validation",
            "Status site validation",
        ):
            self.assertIn(context, self.script)
        self.assertIn("required_status_checks", self.script)
        self.assertIn("Gardener native auto-merge barrier", self.plan)

    def test_existing_strict_status_policy_is_preserved(self) -> None:
        self.assertIn("atlas-doc-viewer|2b03d5843588f0415ecc735f6b33ca7527063137|Static document validation|true", self.script)
        self.assertIn("atlas-quota-watch|97304b7df2489a881aca422e494063d62f034a55|validate|true", self.script)
        self.assertIn("site-pulse|be661f348ce7bc96b98f868b9d0eb2c01fcc99af|Worker validation|true", self.script)
        self.assertIn("specular-sonify|2577b5cbfa852a7dda89f3b0d1e1ed640d4e1f53|Worker configuration validation|false", self.script)
        self.assertIn("status|4db1438b1a8859008461903105360a2f09376c02|Status site validation|true", self.script)
        self.assertIn("strict_required_status_checks_policy: $strict", self.script)

    def test_all_replacements_are_verified_before_classic_removal(self) -> None:
        create_index = self.script.index("PART 1: Create all five replacement rulesets")
        verify_index = self.script.index("PART 2: Re-verify every replacement")
        delete_index = self.script.index("PART 3: Remove only the superseded classic protections")
        self.assertLess(create_index, verify_index)
        self.assertLess(verify_index, delete_index)
        self.assertIn("verify_classic_protection", self.script)
        self.assertIn("verify_classic_absent", self.script)

    def test_mutation_surface_is_ruleset_create_then_classic_delete_only(self) -> None:
        self.assertEqual(self.script.count("--method POST"), 1)
        self.assertEqual(self.script.count("--method DELETE"), 1)
        self.assertNotIn("--method PUT", self.script)
        self.assertNotIn("--method PATCH", self.script)
        self.assertIn('/rulesets"', self.script)
        self.assertIn('/branches/main/protection"', self.script)

    def test_automation_and_runtime_boundaries_are_preserved(self) -> None:
        self.assertIn("ATLAS_GARDENER_AUTOMERGE_ENABLED", self.script)
        self.assertIn("DEPENDABOT_AUTOMERGE_ENABLED", self.script)
        self.assertIn(".allow_auto_merge == true", self.script)
        self.assertIn("ATLAS_GARDENER_WRITE_TARGETS_JSON", self.script)
        for forbidden in (
            "gh variable set",
            "gh variable delete",
            "gh secret",
            "gh pr merge",
            "gh workflow run",
            "gh release create",
        ):
            self.assertNotIn(forbidden, self.script)

    def test_apply_requires_exact_confirmation_and_records_closeout(self) -> None:
        self.assertIn('MODE="${MODE:-inspect}"', self.script)
        self.assertIn("APPLY GITHUB PROVIDER GUARD WAVE 3", self.script)
        self.assertIn("Wave 3 requires no further provider work", self.plan)

    def test_source_operator_misfire_is_recorded(self) -> None:
        self.assertIn("source-only placeholder", self.plan)
        self.assertIn("source-operator-misfire-corrected", self.receipt)
        self.assertIn("No Wave 3 target repository or provider state was changed", self.plan)

    def test_wave_4_was_unstarted_at_wave_3_closeout(self) -> None:
        self.assertIn("Wave 4 and all later waves remain unstarted and separately approval gated.", self.plan)
        self.assertIn('"wave_4_started": False', self.script)


if __name__ == "__main__":
    unittest.main()
