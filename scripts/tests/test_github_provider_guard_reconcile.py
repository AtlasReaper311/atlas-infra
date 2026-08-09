from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import sys

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "github_provider_guard_reconcile.py"
WORKFLOW = ROOT / ".github" / "workflows" / "github-provider-guard-reconcile.yml"
CI_WORKFLOW = ROOT / ".github" / "workflows" / "github-provider-guard-reconciler-ci.yml"
DOC = ROOT / "docs" / "github-provider-guard-reconciler.md"

spec = importlib.util.spec_from_file_location("github_provider_guard_reconcile", SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class FakeClient:
    def __init__(self, states: dict[str, dict]) -> None:
        self.states = states
        self.posts: list[tuple[str, dict]] = []
        self.next_id = 9001

    @staticmethod
    def _repo_from_path(path: str) -> str:
        parts = path.split("/")
        return f"{parts[2]}/{parts[3]}"

    def get(self, path: str):
        repo = self._repo_from_path(path)
        state = self.states[repo]
        if path.endswith("?per_page=100"):
            return state.get("rulesets", [])
        if "/rulesets/" in path:
            ruleset_id = int(path.rsplit("/", 1)[1])
            for ruleset in state.get("rulesets", []):
                if ruleset.get("id") == ruleset_id:
                    return ruleset
            raise AssertionError(f"unknown ruleset {ruleset_id}")
        if "/rules/branches/" in path:
            return state.get("active_rules", [])
        if path.count("/") == 3:
            return state["metadata"]
        raise AssertionError(f"unexpected GET {path}")

    def get_optional(self, path: str):
        repo = self._repo_from_path(path)
        if "/protection" in path:
            return self.states[repo].get("protection")
        raise AssertionError(f"unexpected optional GET {path}")

    def post(self, path: str, payload: dict):
        repo = self._repo_from_path(path)
        self.posts.append((path, payload))
        ruleset_id = self.next_id
        self.next_id += 1
        created = json.loads(json.dumps(payload))
        created["id"] = ruleset_id
        self.states[repo].setdefault("rulesets", []).append(created)
        self.states[repo]["active_rules"] = [
            {"type": rule["type"], "ruleset_id": ruleset_id}
            for rule in payload["rules"]
        ]
        return {"id": ruleset_id}


def projection(*repositories: str) -> dict:
    return {
        "schema_version": module.PROJECTION_SCHEMA,
        "authority": module.AUTHORITY,
        "repository_count": len(repositories),
        "source_fingerprint": "sha256:test",
        "repositories": [
            {
                "repository": repository,
                "lifecycle": "active",
                "scope": "public",
                "provenance": "original",
                "runtime_service": False,
            }
            for repository in repositories
        ],
    }


def requirements(*repositories: str) -> dict:
    return {
        "schema_version": module.REQUIREMENTS_SCHEMA,
        "authority": module.AUTHORITY,
        "defaults": {"default_branch_guard": "required"},
        "repositories": {repository: {} for repository in repositories},
    }


def metadata(name: str) -> dict:
    return {
        "full_name": name,
        "default_branch": "main",
        "visibility": "public",
        "archived": False,
    }


def guard_ruleset(ruleset_id: int = 100) -> dict:
    payload = module.baseline_ruleset_payload()
    payload["id"] = ruleset_id
    return payload


class GithubProviderGuardReconcilerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.ci_workflow = CI_WORKFLOW.read_text(encoding="utf-8")
        cls.doc = DOC.read_text(encoding="utf-8")

    def test_projection_and_requirements_are_authoritative_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            projection_path = root / "projection.json"
            requirements_path = root / "requirements.json"
            projected = projection("AtlasReaper311/example")
            required = requirements("AtlasReaper311/example")
            projection_path.write_text(json.dumps(projected), encoding="utf-8")
            requirements_path.write_text(json.dumps(required), encoding="utf-8")
            loaded_projection = module.load_projection(projection_path)
            loaded_requirements = module.load_requirements(
                requirements_path, loaded_projection
            )
            self.assertTrue(
                module.guard_is_required(
                    loaded_requirements, "AtlasReaper311/example"
                )
            )

    def test_existing_ruleset_guard_is_compliant(self) -> None:
        repo = "AtlasReaper311/example"
        client = FakeClient(
            {
                repo: {
                    "metadata": metadata(repo),
                    "rulesets": [guard_ruleset()],
                    "active_rules": [],
                    "protection": None,
                }
            }
        )
        plan = module.inspect_repository(client, repo)
        self.assertEqual(plan.action, "compliant")
        self.assertEqual(plan.ruleset_id, 100)

    def test_classic_pull_request_guard_is_compliant(self) -> None:
        repo = "AtlasReaper311/example"
        client = FakeClient(
            {
                repo: {
                    "metadata": metadata(repo),
                    "rulesets": [],
                    "active_rules": [],
                    "protection": {"required_pull_request_reviews": {}},
                }
            }
        )
        plan = module.inspect_repository(client, repo)
        self.assertEqual(plan.action, "compliant")

    def test_empty_provider_state_is_create_candidate(self) -> None:
        repo = "AtlasReaper311/example"
        client = FakeClient(
            {
                repo: {
                    "metadata": metadata(repo),
                    "rulesets": [],
                    "active_rules": [],
                    "protection": None,
                }
            }
        )
        plan = module.inspect_repository(client, repo)
        self.assertEqual(plan.action, "create")

    def test_existing_insufficient_ruleset_blocks_automatic_migration(self) -> None:
        repo = "AtlasReaper311/example"
        client = FakeClient(
            {
                repo: {
                    "metadata": metadata(repo),
                    "rulesets": [
                        {
                            "id": 5,
                            "name": "Other rule",
                            "target": "branch",
                            "enforcement": "active",
                            "conditions": {
                                "ref_name": {
                                    "include": ["~DEFAULT_BRANCH"],
                                    "exclude": [],
                                }
                            },
                            "rules": [{"type": "required_status_checks"}],
                        }
                    ],
                    "active_rules": [{"type": "required_status_checks"}],
                    "protection": None,
                }
            }
        )
        plan = module.inspect_repository(client, repo)
        self.assertEqual(plan.action, "blocked")
        self.assertIn("automatic migration is forbidden", plan.reason)

    def test_apply_preflights_entire_scope_before_any_write(self) -> None:
        good = "AtlasReaper311/good"
        conflict = "AtlasReaper311/conflict"
        client = FakeClient(
            {
                good: {
                    "metadata": metadata(good),
                    "rulesets": [],
                    "active_rules": [],
                    "protection": None,
                },
                conflict: {
                    "metadata": metadata(conflict),
                    "rulesets": [
                        {
                            "id": 4,
                            "name": "Existing",
                            "target": "branch",
                            "enforcement": "active",
                            "conditions": {
                                "ref_name": {
                                    "include": ["~DEFAULT_BRANCH"],
                                    "exclude": [],
                                }
                            },
                            "rules": [{"type": "required_status_checks"}],
                        }
                    ],
                    "active_rules": [{"type": "required_status_checks"}],
                    "protection": None,
                },
            }
        )
        with self.assertRaises(module.ReconcileError):
            module.reconcile(
                client,
                projection(good, conflict),
                requirements(good, conflict),
                mode="apply",
                confirmation=module.APPLY_CONFIRMATION,
            )
        self.assertEqual(client.posts, [])

    def test_apply_requires_exact_confirmation(self) -> None:
        repo = "AtlasReaper311/example"
        client = FakeClient(
            {
                repo: {
                    "metadata": metadata(repo),
                    "rulesets": [],
                    "active_rules": [],
                    "protection": None,
                }
            }
        )
        with self.assertRaises(module.ReconcileError):
            module.reconcile(
                client,
                projection(repo),
                requirements(repo),
                mode="apply",
                confirmation="yes",
            )
        self.assertEqual(client.posts, [])

    def test_apply_creates_only_baseline_guard_and_verifies_it(self) -> None:
        repo = "AtlasReaper311/example"
        client = FakeClient(
            {
                repo: {
                    "metadata": metadata(repo),
                    "rulesets": [],
                    "active_rules": [],
                    "protection": None,
                }
            }
        )
        plans, writes = module.reconcile(
            client,
            projection(repo),
            requirements(repo),
            mode="apply",
            confirmation=module.APPLY_CONFIRMATION,
        )
        self.assertTrue(writes)
        self.assertEqual(len(client.posts), 1)
        self.assertEqual(plans[0].action, "created")
        payload = client.posts[0][1]
        self.assertEqual(payload["bypass_actors"], [])
        self.assertEqual(
            {rule["type"] for rule in payload["rules"]},
            {"deletion", "non_fast_forward", "pull_request"},
        )
        self.assertNotIn("required_status_checks", json.dumps(payload))

    def test_workflow_is_disabled_by_default_and_uses_dedicated_app(self) -> None:
        self.assertIn("ATLAS_PROVIDER_GUARD_RECONCILE_ENABLED", self.workflow)
        self.assertIn("ATLAS_PROVIDER_GUARD_APP_CLIENT_ID", self.workflow)
        self.assertIn("ATLAS_PROVIDER_GUARD_APP_PRIVATE_KEY", self.workflow)
        self.assertIn("permission-administration: write", self.workflow)
        self.assertIn("repositories: ${{ steps.provider-scope.outputs.repositories }}", self.workflow)
        self.assertIn("public-repository-classifications.json", self.workflow)
        self.assertIn(
            "actions/create-github-app-token@bcd2ba49218906704ab6c1aa796996da409d3eb1",
            self.workflow,
        )
        self.assertNotIn("ATLAS_GARDENER", self.workflow)

    def test_workflow_has_no_broad_builtin_token_permission(self) -> None:
        self.assertIn("permissions:\n  contents: read", self.workflow)
        self.assertNotIn("contents: write", self.workflow)
        self.assertNotIn("pull-requests: write", self.workflow)
        self.assertNotIn("actions: write", self.workflow)

    def test_ci_workflow_covers_reconciler_contract(self) -> None:
        for path in (
            ".github/workflows/github-provider-guard-reconcile.yml",
            "docs/github-provider-guard-reconciler.md",
            "policy/github-conformance-requirements.json",
            "policy/public-repository-classifications.json",
            "scripts/github_provider_guard_reconcile.py",
            "scripts/tests/test_github_provider_guard_reconcile.py",
        ):
            self.assertIn(path, self.ci_workflow)
        self.assertIn("Provider guard reconciler validation", self.ci_workflow)
        self.assertIn("permissions:\n  contents: read", self.ci_workflow)

    def test_documented_boundary_is_create_only(self) -> None:
        self.assertIn("Create-only contract", self.doc)
        self.assertIn("never:\n\n- updates or deletes a ruleset", self.doc)
        self.assertIn("does not discover repositories from account membership", self.doc)
        self.assertIn("Do not widen Atlas Gardener", self.doc)


if __name__ == "__main__":
    unittest.main()
