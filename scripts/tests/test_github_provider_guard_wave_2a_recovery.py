from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "github-provider-guard-wave-2a-recovery.sh"


class GithubProviderGuardWave2ARecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script = SCRIPT.read_text(encoding="utf-8")

    def test_exact_recovery_scope(self):
        self.assertIn('GARDENER_RULESET_ID="20576711"', self.script)
        self.assertIn('INTERFACE_CONTEXT="Validate interface kit"', self.script)
        self.assertIn('MODE must be inspect or apply-interface-kit', self.script)
        self.assertIn(
            'APPLY GITHUB PROVIDER GUARD WAVE 2A INTERFACE KIT RECOVERY',
            self.script,
        )

    def test_only_interface_kit_has_provider_post(self):
        post_lines = [
            line
            for line in self.script.splitlines()
            if "--method POST" in line
        ]
        self.assertEqual(len(post_lines), 1)
        self.assertIn("atlas-interface-kit/rulesets", post_lines[0])
        self.assertNotIn("atlas-gardener/rulesets\" --input", self.script)

    def test_gardener_is_verified_not_recreated(self):
        self.assertIn(
            'verify_gardener_completed_state "${EVIDENCE_DIR}/atlas-gardener"',
            self.script,
        )
        self.assertIn(
            'verify_gardener_completed_state "${EVIDENCE_DIR}/atlas-gardener-after-interface-write"',
            self.script,
        )
        self.assertIn('required_status_checks == [{context:"test",integration_id:$integration_id}]', self.script)

    def test_helper_scope_is_local(self):
        for declaration in (
            'local repo_dir="$1"',
            'local output_file="$1"',
            'local ruleset_id',
        ):
            self.assertIn(declaration, self.script)

    def test_journey_watch_and_wave_3_are_write_excluded(self):
        self.assertNotIn("atlas-journey-watch/rulesets", self.script)
        self.assertNotIn("gh variable set", self.script)
        self.assertNotIn("gh workflow run", self.script)
        self.assertNotIn("gh pr merge", self.script)
        self.assertIn("atlas-journey-watch was not touched", self.script)
        self.assertIn("Wave 3 was not started", self.script)

    def test_recovery_defaults_read_only(self):
        self.assertIn('MODE="${MODE:-inspect}"', self.script)
        self.assertIn("Recovery inspection complete; no provider write performed.", self.script)


if __name__ == "__main__":
    unittest.main()
