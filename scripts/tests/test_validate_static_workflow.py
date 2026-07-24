from __future__ import annotations

import unittest
from pathlib import Path


WORKFLOW = (
    Path(__file__).resolve().parents[2]
    / ".github"
    / "workflows"
    / "validate-static.yml"
)


class ValidateStaticWorkflowTests(unittest.TestCase):
    def test_optional_exclude_file_stages_the_pages_artifact(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("publish_exclude_file:", text)
        self.assertIn('--exclude-from="${PUBLISH_EXCLUDE_FILE}"', text)
        self.assertIn('test -f "${publish_directory}/index.html"', text)
        self.assertIn('pages deploy "$PUBLISH_DIRECTORY"', text)
        self.assertNotIn("pages deploy . \\", text)

    def test_unfiltered_callers_keep_the_existing_repository_root_default(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn('echo "directory=." >> "${GITHUB_OUTPUT}"', text)
        self.assertIn("default: \"\"", text)


if __name__ == "__main__":
    unittest.main()
