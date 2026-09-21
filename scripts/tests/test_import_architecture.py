from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]


class ImportArchitectureTests(unittest.TestCase):
    def _run_python(self, *arguments: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment.pop("PYTHONPATH", None)
        return subprocess.run(
            [sys.executable, *arguments],
            cwd=cwd,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_repository_root_package_import_works_without_pythonpath(self):
        result = self._run_python(
            "-c",
            "from scripts import control_plane_contracts; "
            "from scripts import model_promotion_public_projection",
        )
        self.assertEqual(0, result.returncode, result.stderr)

    def test_direct_cli_import_path_still_works(self):
        result = self._run_python(
            "scripts/model_promotion_public_projection.py",
            "check",
            "--root",
            ".",
        )
        self.assertEqual(0, result.returncode, result.stderr)

    def test_missing_package_dependency_is_not_swallowed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / "scripts"
            package.mkdir()
            (package / "__init__.py").write_text("", encoding="utf-8")
            shutil.copy2(
                ROOT / "scripts/control_plane_contracts.py",
                package / "control_plane_contracts.py",
            )

            result = self._run_python(
                "-c",
                "import scripts.control_plane_contracts",
                cwd=root,
            )

        self.assertNotEqual(0, result.returncode)
        self.assertIn("model_promotion_public_projection_rules", result.stderr)
