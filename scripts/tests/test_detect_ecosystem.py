import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import detect_ecosystem


class FakeClient:
    def __init__(self, listings):
        self.listings = listings

    def get(self, path):
        content_path = path.split("/contents", 1)[1].split("?", 1)[0].lstrip("/")
        return self.listings[content_path]


def file(name):
    return {"name": name, "type": "file"}


def directory(name):
    return {"name": name, "type": "dir"}


class EcosystemDetectionTests(unittest.TestCase):
    def test_detects_root_immediate_and_yaml_workflows(self):
        client = FakeClient(
            {
                "": [
                    file("package.json"),
                    file("Dockerfile"),
                    directory("python"),
                    directory("rust"),
                    directory(".github"),
                ],
                "python": [file("pyproject.toml")],
                "rust": [file("Cargo.toml")],
                ".github": [directory("workflows")],
                ".github/workflows": [file("ci.yaml")],
            }
        )

        detected = detect_ecosystem.detect_ecosystem_locations(
            client, "AtlasReaper311/example", "trunk"
        )

        self.assertEqual(
            [item.ecosystem for item in detected],
            ["cargo", "docker", "github-actions", "npm", "pip"],
        )
        self.assertEqual(detected[-1].directories, ("/python",))

    def test_empty_repository_returns_empty_list(self):
        client = FakeClient({"": []})
        self.assertEqual(
            detect_ecosystem.detect_ecosystem_locations(
                client, "AtlasReaper311/empty", "main"
            ),
            [],
        )


if __name__ == "__main__":
    unittest.main()
