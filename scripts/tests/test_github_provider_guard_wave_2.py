from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "github-provider-guard-wave-2-inspect.sh"
PLAN = ROOT / "docs" / "github-provider-guard-wave-2-plan.md"


class GithubProviderGuardWave2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script = SCRIPT.read_text(encoding="utf-8")
        cls.plan = PLAN.read_text(encoding="utf-8")

    def test_exact_repository_scope(self):
        for repository in (
            "atlas-gardener",
            "atlas-interface-kit",
            "atlas-journey-watch",
        ):
            self.assertIn(repository, self.script)
            self.assertIn(repository, self.plan)

    def test_exact_current_main_pins(self):
        for sha in (
            "319465dcea68a8fefead3e7d90e82b79078cb34d",
            "21a1a168e3b25e916555ce4edd4229bd7c061ecb",
            "a124d23ba4444522c206ae3c169165b4e0ef8019",
        ):
            self.assertIn(sha, self.script)

    def test_exact_native_contexts(self):
        for context in (
            '"test"',
            '"Validate interface kit"',
            '"Offline journey validation"',
        ):
            self.assertIn(context, self.script)
        self.assertIn('INTEGRATION_ID="15368"', self.script)

    def test_validation_evidence_is_pinned(self):
        for value in (
            '"22"',
            '"5975733c5d4f05d66f957cb50a322905f7751d06"',
            '"14"',
            '"1f26360d938b589cf8a562ca308fd6ca3b4a2b3f"',
            '"12"',
            '"acd9b0fdb85fc1d0575adb5f1ee6bea991e5a022"',
        ):
            self.assertIn(value, self.script)

    def test_expected_auto_merge_states_are_explicit(self):
        self.assertIn(
            'verify_repository \\\n  "atlas-gardener" \\\n  "319465dcea68a8fefead3e7d90e82b79078cb34d" \\\n  "false"',
            self.script,
        )
        self.assertIn(
            'verify_repository \\\n  "atlas-interface-kit" \\\n  "21a1a168e3b25e916555ce4edd4229bd7c061ecb" \\\n  "false"',
            self.script,
        )
        self.assertIn(
            'verify_repository \\\n  "atlas-journey-watch" \\\n  "a124d23ba4444522c206ae3c169165b4e0ef8019" \\\n  "true"',
            self.script,
        )

    def test_specialist_non_secret_variables_are_inspected(self):
        for variable in (
            "ATLAS_GARDENER_MODE",
            "ATLAS_GARDENER_WRITE_GATE",
            "ATLAS_GARDENER_WRITE_TARGETS_JSON",
            "DEPENDABOT_AUTOMERGE_ENABLED",
        ):
            self.assertIn(variable, self.script)
        self.assertNotIn("/actions/secrets", self.script)

    def test_specialist_workflows_are_captured(self):
        for path in (
            ".github/workflows/controller.yml",
            ".github/workflows/release.yml",
            ".github/workflows/dependabot-automerge.yml",
            ".github/workflows/release-watch.yml",
        ):
            self.assertIn(path, self.script)

    def test_operator_is_read_only(self):
        forbidden = (
            "--method POST",
            "--method PUT",
            "--method PATCH",
            "--method DELETE",
            "gh variable set",
            "gh variable delete",
            "gh secret",
            "gh pr merge",
            "gh workflow run",
        )
        for token in forbidden:
            self.assertNotIn(token, self.script)
        self.assertIn("provider_writes_performed: false", self.script)
        self.assertIn("Provider writes performed: none.", self.script)

    def test_plan_splits_wave_2a_and_2b(self):
        self.assertIn("### Wave 2A candidates", self.plan)
        self.assertIn("### Wave 2B held pending automation-state evidence", self.plan)
        self.assertIn(
            "No provider-write approval is implied by approval to merge this inspection authority.",
            self.plan,
        )

    def test_cross_platform_sha256_support(self):
        self.assertIn("sha256sum", self.script)
        self.assertIn("shasum -a 256", self.script)


if __name__ == "__main__":
    unittest.main()
