from __future__ import annotations

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "github-provider-guard-wave-2a.sh"
PLAN = ROOT / "docs" / "github-provider-guard-wave-2-plan.md"


class GithubProviderGuardWave2ATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = SCRIPT.read_text(encoding="utf-8")
        cls.plan = PLAN.read_text(encoding="utf-8")

    def test_scope_is_exactly_gardener_and_interface_kit(self) -> None:
        match = re.search(r"REPOSITORIES='([^']+)'", self.script, re.DOTALL)
        self.assertIsNotNone(match)
        rows = match.group(1).splitlines()
        self.assertEqual(len(rows), 2)
        self.assertTrue(rows[0].startswith("atlas-gardener|22|open|"))
        self.assertTrue(rows[1].startswith("atlas-interface-kit|14|merged|"))
        self.assertNotIn("atlas-journey-watch|", match.group(1))

    def test_exact_main_and_validation_heads_are_pinned(self) -> None:
        for value in (
            "319465dcea68a8fefead3e7d90e82b79078cb34d",
            "5975733c5d4f05d66f957cb50a322905f7751d06",
            "21a1a168e3b25e916555ce4edd4229bd7c061ecb",
            "1f26360d938b589cf8a562ca308fd6ca3b4a2b3f",
        ):
            self.assertIn(value, self.script)

    def test_native_contexts_and_integration_are_exact(self) -> None:
        self.assertIn("|test\n", self.script)
        self.assertIn("|Validate interface kit'", self.script)
        self.assertIn('INTEGRATION_ID="15368"', self.script)

    def test_gardener_controller_state_is_pinned_and_read_only(self) -> None:
        self.assertIn('GARDENER_MODE="automerge-low-risk"', self.script)
        self.assertIn('GARDENER_WRITE_GATE="enabled"', self.script)
        self.assertIn("atlas-doc-viewer", self.script)
        self.assertIn("atlas-quota-watch", self.script)
        self.assertIn("site-pulse", self.script)
        self.assertIn("specular-sonify", self.script)
        self.assertIn("status", self.script)
        self.assertIn("/actions/variables/${name}", self.script)
        self.assertNotIn('/actions/variables/${name}" --method', self.script)

    def test_apply_requires_exact_confirmation(self) -> None:
        self.assertIn('MODE="${MODE:-inspect}"', self.script)
        self.assertIn("APPLY GITHUB PROVIDER GUARD WAVE 2A", self.script)
        self.assertNotIn("APPLY GITHUB PROVIDER GUARD WAVE 2B", self.script)

    def test_provider_write_surface_is_ruleset_create_only(self) -> None:
        self.assertEqual(self.script.count("--method POST"), 1)
        self.assertNotIn("--method PUT", self.script)
        self.assertNotIn("--method PATCH", self.script)
        self.assertNotIn("--method DELETE", self.script)
        apply_marker = self.script.index("PART 2: Apply exactly two approved Wave 2A rulesets")
        post_marker = self.script.index("--method POST")
        self.assertGreater(post_marker, apply_marker)

    def test_ruleset_shape_matches_proven_pattern(self) -> None:
        self.assertIn("bypass_actors: []", self.script)
        self.assertIn('include: ["~DEFAULT_BRANCH"]', self.script)
        self.assertIn('{type: "deletion"}', self.script)
        self.assertIn('{type: "non_fast_forward"}', self.script)
        self.assertIn('type: "pull_request"', self.script)
        self.assertIn("required_approving_review_count: 0", self.script)
        self.assertIn("required_review_thread_resolution: false", self.script)
        self.assertIn('type: "required_status_checks"', self.script)
        self.assertIn("strict_required_status_checks_policy: false", self.script)

    def test_runner_refuses_existing_protection_or_auto_merge_drift(self) -> None:
        self.assertIn(".allow_auto_merge == false", self.script)
        self.assertIn("rulesets?per_page=100", self.script)
        self.assertIn("branches/main/protection", self.script)
        self.assertIn("length) == 0", self.script)

    def test_cross_platform_sha256_support(self) -> None:
        self.assertIn("command -v sha256sum", self.script)
        self.assertIn("command -v shasum", self.script)
        self.assertIn("shasum -a 256", self.script)
        self.assertNotIn("sort -z", self.script)

    def test_plan_records_live_journey_watch_hold(self) -> None:
        self.assertIn("19154613", self.plan)
        self.assertIn("DEPENDABOT_AUTOMERGE_ENABLED", self.plan)
        self.assertIn("`true`", self.plan)
        self.assertIn("Wave 2A", self.plan)
        self.assertIn("Wave 2B", self.plan)
        self.assertIn("Wave 3", self.plan)


if __name__ == "__main__":
    unittest.main()
