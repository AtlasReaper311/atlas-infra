from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "github-provider-guard-wave-4a.sh"
PLAN = ROOT / "docs" / "github-provider-guard-wave-4-plan.md"
RECEIPT = ROOT / "reports" / "github-provider-guard-wave-4-inspection-receipt.json"


class GithubProviderGuardWave4ATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = SCRIPT.read_text(encoding="utf-8")
        cls.plan = PLAN.read_text(encoding="utf-8")
        cls.receipt = RECEIPT.read_text(encoding="utf-8")

    def test_scope_is_exactly_thirteen_create_first_repositories(self) -> None:
        repositories = (
            ".github",
            "atlas-api-index",
            "atlas-blackbox",
            "atlas-corpus",
            "atlas-daily-digest",
            "atlas-notify",
            "deploy-watch",
            "github-pulse",
            "ramone-edge",
            "ramone-memory",
            "ramone-voice-trigger",
            "specular-sentinel",
            "specular-telemetry",
        )
        matrix = self.script.split("REPOSITORIES=", 1)[1].split("\n\nrequire_command", 1)[0]
        self.assertEqual(matrix.count("\n"), 12)
        for repository in repositories:
            self.assertIn(repository, self.script)
            self.assertIn(repository, self.plan)
        self.assertNotIn("AtlasReaper311|1cc070", self.script)
        self.assertNotIn("atlas-dora|", self.script)

    def test_reviewed_inspection_receipt_is_pinned(self) -> None:
        archive = "0abbd15869a96a8f38f7f7945a914277b7995924710e9eb0a0580478a289e884"
        self.assertIn(archive, self.plan)
        self.assertIn(archive, self.receipt)
        self.assertIn('"manifest_entries": 171', self.receipt)
        self.assertIn('"digest_mismatches": 0', self.receipt)

    def test_runtime_native_contexts_are_preserved(self) -> None:
        for context in (
            "build",
            "Offline Worker validation",
            "Worker validation",
            "Test (Vitest)",
        ):
            self.assertIn(context, self.script)
        self.assertIn('INTEGRATION_ID="15368"', self.script)
        self.assertIn("strict_required_status_checks_policy: false", self.script)

    def test_community_defaults_has_no_invented_required_check(self) -> None:
        self.assertIn(".github|dd3818eeae486c95e1a1fc0860786db5c24308fa|NONE", self.script)
        self.assertIn('if [ "$native_context" = "NONE" ]', self.script)
        self.assertIn("For `.github` the ruleset contains only", self.plan)

    def test_provider_mutation_surface_is_create_only(self) -> None:
        self.assertEqual(self.script.count("--method POST"), 1)
        self.assertNotIn("--method PUT", self.script)
        self.assertNotIn("--method PATCH", self.script)
        self.assertNotIn("--method DELETE", self.script)
        self.assertIn('/rulesets"', self.script)

    def test_all_baselines_are_preflighted_before_apply_loop(self) -> None:
        preflight = self.script.index("PART 0: Preflight all 13 Wave 4A repositories")
        apply = self.script.index("PART 1: Create and verify one additive ruleset")
        self.assertLess(preflight, apply)
        self.assertIn("verify_baseline", self.script)
        self.assertIn("verify_ruleset", self.script)

    def test_automation_and_profile_boundaries_are_preserved(self) -> None:
        self.assertIn(".allow_auto_merge == false", self.script)
        self.assertIn("ATLAS_GARDENER_AUTOMERGE_ENABLED", self.script)
        self.assertIn("DEPENDABOT_AUTOMERGE_ENABLED", self.script)
        self.assertIn('"profile_repository_modified":false', self.script)
        for forbidden in (
            "gh variable set",
            "gh variable delete",
            "gh secret",
            "gh pr merge",
            "gh workflow run",
            "gh release create",
            "/AtlasReaper311/rulesets",
        ):
            self.assertNotIn(forbidden, self.script)

    def test_apply_requires_exact_confirmation(self) -> None:
        self.assertIn('MODE="${MODE:-inspect}"', self.script)
        self.assertIn("APPLY GITHUB PROVIDER GUARD WAVE 4A", self.script)
        self.assertIn("Any provider mutation requires a new explicit approval", self.plan)

    def test_scoreboard_projection_is_bounded(self) -> None:
        self.assertIn("245 / 15 / 0", self.plan)
        self.assertIn("258 / 2 / 0", self.plan)
        self.assertNotIn("260 / 0 / 0` after Wave 4A", self.plan)


if __name__ == "__main__":
    unittest.main()
