from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "github-provider-guard-wave-2b-inspect.sh"
PLAN = ROOT / "docs" / "github-provider-guard-wave-2b-plan.md"


class GithubProviderGuardWave2BTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = SCRIPT.read_text(encoding="utf-8")
        cls.plan = PLAN.read_text(encoding="utf-8")

    def test_scope_is_journey_watch_only(self) -> None:
        self.assertIn('REPOSITORY="atlas-journey-watch"', self.script)
        self.assertNotIn('REPOSITORY="atlas-gardener"', self.script)
        self.assertNotIn('REPOSITORY="atlas-interface-kit"', self.script)
        self.assertIn("Wave 2B is limited to `AtlasReaper311/atlas-journey-watch`.", self.plan)

    def test_current_identity_is_pinned(self) -> None:
        for value in (
            "a124d23ba4444522c206ae3c169165b4e0ef8019",
            "19154613",
            "Require native pull request validation",
            "acd9b0fdb85fc1d0575adb5f1ee6bea991e5a022",
            "Offline journey validation",
            "15368",
        ):
            self.assertIn(value, self.script)
            self.assertIn(value, self.plan)

    def test_selective_automerge_state_is_inspected(self) -> None:
        self.assertIn("DEPENDABOT_AUTOMERGE_ENABLED", self.script)
        self.assertIn('EXPECTED_VARIABLE_VALUE="true"', self.script)
        self.assertIn("autoMergeRequest", self.script)
        self.assertIn("8e6d08701823b02c4859bfc72af67fc8ace1f4b5", self.script)
        self.assertIn("dependabot_automerge_policy.py", self.script)

    def test_full_existing_ruleset_is_read(self) -> None:
        self.assertIn('/rulesets/${EXPECTED_RULESET_ID}', self.script)
        self.assertIn('/rules/branches/main', self.script)
        self.assertIn("qualifies_standard_guard_semantics", self.script)
        for rule in (
            "deletion",
            "non_fast_forward",
            "pull_request",
            "required_status_checks",
        ):
            self.assertIn(rule, self.script)

    def test_operator_is_read_only(self) -> None:
        forbidden = (
            "--method POST",
            "--method PUT",
            "--method PATCH",
            "--method DELETE",
            "gh variable set",
            "gh variable delete",
            "gh secret",
            "gh workflow run",
            "gh pr merge",
            "gh release create",
        )
        for token in forbidden:
            self.assertNotIn(token, self.script)
        self.assertIn('"provider_writes_performed": False', self.script)
        self.assertIn('"variables_written": False', self.script)
        self.assertIn('"secrets_read": False', self.script)

    def test_classic_protection_is_observed_not_mutated(self) -> None:
        self.assertIn("branches/main/protection", self.script)
        self.assertIn('{"status":"present"}', self.script)
        self.assertIn('{"status":"absent"}', self.script)

    def test_reconciliation_does_not_assume_replacement(self) -> None:
        self.assertIn("narrow in-place reconciliation", self.plan)
        self.assertIn("Replacement, deletion, disablement, or creation of a second overlapping ruleset is not an assumed outcome.", self.plan)
        self.assertIn("Any provider mutation requires a new explicit approval", self.plan)

    def test_wave_3_remains_unstarted(self) -> None:
        self.assertIn("Wave 3 and all later waves remain unstarted.", self.plan)
        self.assertIn('"wave_3_started": False', self.script)

    def test_cross_platform_sha256_support(self) -> None:
        self.assertIn("sha256sum", self.script)
        self.assertIn("shasum -a 256", self.script)


if __name__ == "__main__":
    unittest.main()
