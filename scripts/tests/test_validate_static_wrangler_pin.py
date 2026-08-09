from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "validate_static_wrangler_pin.py"
SPEC = importlib.util.spec_from_file_location("validate_static_wrangler_pin", SCRIPT)
assert SPEC and SPEC.loader
VALIDATE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = VALIDATE
SPEC.loader.exec_module(VALIDATE)

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "validate-static.yml"


def deploy_step(
    *,
    version_line: str = '          WRANGLER_VERSION: "4.116.0"',
    run_invocation: str = (
        '          npx --yes "wrangler@${WRANGLER_VERSION}" pages deploy '
        '"$PUBLISH_DIRECTORY" \\'
    ),
) -> str:
    return "\n".join(
        [
            "jobs:",
            "  deploy:",
            "    steps:",
            "      - name: Deploy with wrangler",
            "        id: deploy_step",
            "        env:",
            "          CLOUDFLARE_API_TOKEN: ${{ secrets.CF_PAGES_DEPLOY_TOKEN }}",
            version_line,
            "        run: |",
            "          set -euo pipefail",
            run_invocation,
            "            --project-name \"$PROJECT_NAME\"",
            "",
        ]
    )


class ValidateStaticWranglerPinTests(unittest.TestCase):
    def test_current_validate_static_workflow_passes(self) -> None:
        pin = VALIDATE.validate_workflow(WORKFLOW)
        self.assertRegex(pin.version, r"^[0-9]+\.[0-9]+\.[0-9]+$")
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(f'WRANGLER_VERSION: "{pin.version}"', text)
        self.assertIn('npx --yes "wrangler@${WRANGLER_VERSION}" pages deploy', text)

    def test_exact_version_matching_current_source_shape_passes(self) -> None:
        pin = VALIDATE.validate_workflow_text(deploy_step())
        self.assertEqual("4.116.0", pin.version)

    def test_floating_major_version_is_rejected(self) -> None:
        text = deploy_step(version_line='          WRANGLER_VERSION: "4"')
        with self.assertRaisesRegex(
            VALIDATE.WranglerPinValidationError,
            "exact x.y.z pin",
        ):
            VALIDATE.validate_workflow_text(text)

    def test_latest_tag_is_rejected(self) -> None:
        text = deploy_step(version_line='          WRANGLER_VERSION: "latest"')
        with self.assertRaisesRegex(
            VALIDATE.WranglerPinValidationError,
            "exact x.y.z pin",
        ):
            VALIDATE.validate_workflow_text(text)

    def test_unversioned_wrangler_invocation_is_rejected(self) -> None:
        text = deploy_step(
            run_invocation="          npx --yes wrangler pages deploy \"$PUBLISH_DIRECTORY\" \\"
        )
        with self.assertRaisesRegex(
            VALIDATE.WranglerPinValidationError,
            "wrangler@\\$\\{WRANGLER_VERSION\\}|unversioned wrangler",
        ):
            VALIDATE.validate_workflow_text(text)

    def test_literal_wrangler_at_4_invocation_is_rejected(self) -> None:
        text = deploy_step(
            run_invocation='          npx --yes "wrangler@4" pages deploy "$PUBLISH_DIRECTORY" \\'
        )
        with self.assertRaisesRegex(
            VALIDATE.WranglerPinValidationError,
            "WRANGLER_VERSION|floating major|mutable selector|must consume",
        ):
            VALIDATE.validate_workflow_text(text)

    def test_literal_wrangler_at_latest_invocation_is_rejected(self) -> None:
        text = deploy_step(
            version_line='          WRANGLER_VERSION: "4.116.0"',
            run_invocation=(
                '          npx --yes "wrangler@latest" pages deploy '
                '"$PUBLISH_DIRECTORY" \\'
            ),
        )
        with self.assertRaisesRegex(
            VALIDATE.WranglerPinValidationError,
            "must consume|mutable selector",
        ):
            VALIDATE.validate_workflow_text(text)

    def test_missing_version_declaration_is_rejected(self) -> None:
        text = deploy_step(version_line="          PROJECT_NAME: demo")
        with self.assertRaisesRegex(
            VALIDATE.WranglerPinValidationError,
            "missing an explicit WRANGLER_VERSION",
        ):
            VALIDATE.validate_workflow_text(text)

    def test_cli_accepts_current_workflow(self) -> None:
        self.assertEqual(0, VALIDATE.main(["--workflow", str(WORKFLOW)]))

    def test_non_vacuity_historical_floating_form_fails_on_disk(self) -> None:
        original = WORKFLOW.read_text(encoding="utf-8")
        mutated = original.replace(
            'WRANGLER_VERSION: "4.116.0"',
            'WRANGLER_VERSION: "4"',
            1,
        )
        self.assertNotEqual(original, mutated)
        with tempfile.TemporaryDirectory() as value:
            path = Path(value) / "validate-static.yml"
            path.write_text(mutated, encoding="utf-8")
            with self.assertRaisesRegex(
                VALIDATE.WranglerPinValidationError,
                "exact x.y.z pin",
            ):
                VALIDATE.validate_workflow(path)


if __name__ == "__main__":
    unittest.main()
