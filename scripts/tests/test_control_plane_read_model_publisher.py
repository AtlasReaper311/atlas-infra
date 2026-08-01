from __future__ import annotations

import copy
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

import control_plane_read_model_publisher as publisher
from control_plane_contracts import load_json, validate_instance


class MemoryTransport:
    def __init__(self, previous: bytes | None = None) -> None:
        self.value = previous
        self.calls: list[tuple[str, str]] = []

    def get(self, url: str, token: str) -> bytes | None:
        self.calls.append(("GET", url))
        return self.value

    def put(self, url: str, token: str, value: bytes) -> None:
        self.calls.append(("PUT", url))
        self.value = value


class ControlPlaneReadModelPublisherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.expected = ROOT / "tests/fixtures/control-plane-read-model/expected"
        cls.policy = ROOT / "policy/control-plane-read-model-publisher.json"
        cls.producer_policy = ROOT / "policy/control-plane-read-model.json"
        cls.model_schema = (
            ROOT / "contracts/ramone/v1/control-plane-read-model.schema.json"
        )
        cls.receipt_schema = (
            ROOT
            / "contracts/ramone/v1/control-plane-read-model-publication-receipt.schema.json"
        )
        cls.workflow = (
            ROOT / ".github/workflows/publish-control-plane-read-model.yml"
        )
        cls.now = datetime(2026, 7, 14, 10, 30, tzinfo=timezone.utc)
        cls.source_run_id = "123456789"
        cls.source_head_sha = "b" * 40

    def bundle(self, root: Path) -> Path:
        bundle = root / "bundle"
        bundle.mkdir()
        shutil.copy(
            self.expected / "read-model.json",
            bundle / "control-plane-read-model.json",
        )
        shutil.copy(
            self.expected / "dry-run-receipt.json",
            bundle / "dry-run-receipt.json",
        )
        return bundle

    @staticmethod
    def digest(path: Path) -> str:
        return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()

    def validate(self, bundle: Path, **overrides):
        model_path = bundle / "control-plane-read-model.json"
        model = load_json(model_path)
        arguments = {
            "bundle": bundle,
            "expected_artifact_sha256": self.digest(model_path),
            "expected_read_model_fingerprint": model["read_model_fingerprint"],
            "source_run_id": self.source_run_id,
            "source_head_sha": self.source_head_sha,
            "now": self.now,
            "policy_path": self.policy,
            "schema_path": self.model_schema,
            "producer_policy_path": self.producer_policy,
        }
        arguments.update(overrides)
        return publisher.validate_bundle(**arguments)

    def test_preflight_validates_exact_fixture_and_redacted_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            validation = self.validate(self.bundle(Path(directory)))
            receipt = publisher.validate_receipt(validation, self.now)
            self.assertEqual([], validate_instance(receipt, load_json(self.receipt_schema)))
            self.assertEqual("validated", receipt["status"])
            self.assertFalse(receipt["provider_write_performed"])
            self.assertEqual("not-performed", receipt["provider_write_outcome"])
            self.assertFalse(receipt["read_back_verified"])
            self.assertIsNone(receipt["error_code"])
            self.assertNotIn("token", json.dumps(receipt).lower())
            self.assertEqual("control-plane:read-model:v1", receipt["bounded_kv_key"])

    def test_wrong_exact_digest_or_fingerprint_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            bundle = self.bundle(Path(directory))
            with self.assertRaisesRegex(publisher.PublisherError, "SHA-256"):
                self.validate(bundle, expected_artifact_sha256="sha256:" + "0" * 64)
            with self.assertRaisesRegex(publisher.PublisherError, "approval input"):
                self.validate(
                    bundle,
                    expected_read_model_fingerprint="sha256:" + "0" * 64,
                )

    def test_bundle_inventory_and_stale_artifacts_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            bundle = self.bundle(Path(directory))
            (bundle / "extra.json").write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(publisher.PublisherError, "inventory mismatch"):
                self.validate(bundle)
        with tempfile.TemporaryDirectory() as directory:
            bundle = self.bundle(Path(directory))
            stale_now = datetime(2026, 7, 14, 10, 41, tzinfo=timezone.utc)
            with self.assertRaisesRegex(publisher.PublisherError, "stale"):
                self.validate(bundle, now=stale_now)

    def test_secret_bearing_model_and_writer_receipt_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            bundle = self.bundle(Path(directory))
            model_path = bundle / "control-plane-read-model.json"
            model = load_json(model_path)
            model["services"][0]["token"] = "not-a-real-secret"
            model_path.write_text(json.dumps(model), encoding="utf-8")
            with self.assertRaisesRegex(
                publisher.PublisherError, "forbidden or secret-bearing key"
            ):
                self.validate(
                    bundle,
                    expected_artifact_sha256=self.digest(model_path),
                )
        with tempfile.TemporaryDirectory() as directory:
            bundle = self.bundle(Path(directory))
            receipt_path = bundle / "dry-run-receipt.json"
            receipt = load_json(receipt_path)
            receipt["provider_write_performed"] = True
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            with self.assertRaisesRegex(publisher.PublisherError, "provider write"):
                self.validate(bundle)

    def test_publish_uses_only_fixed_get_put_get_and_exact_readback(self):
        with tempfile.TemporaryDirectory() as directory:
            validation = self.validate(self.bundle(Path(directory)))
            old = copy.deepcopy(validation.model)
            old["read_model_fingerprint"] = "sha256:" + "1" * 64
            previous = (json.dumps(old, sort_keys=True) + "\n").encode()
            transport = MemoryTransport(previous)
            receipt = publisher.publish_validated(
                validation,
                confirmation="publish-control-plane-read-model-v1",
                token="test-token-not-a-real-secret",
                now=self.now,
                policy_path=self.policy,
                transport=transport,
            )
            self.assertEqual(["GET", "PUT", "GET"], [item[0] for item in transport.calls])
            self.assertEqual(1, len({item[1] for item in transport.calls}))
            self.assertIn(
                "/storage/kv/namespaces/33fa7cbf66fc495ea0304a5f95ffc9a8/values/"
                "control-plane%3Aread-model%3Av1",
                transport.calls[0][1],
            )
            self.assertEqual([], validate_instance(receipt, load_json(self.receipt_schema)))
            self.assertTrue(receipt["provider_write_performed"])
            self.assertEqual("performed", receipt["provider_write_outcome"])
            self.assertTrue(receipt["read_back_verified"])
            self.assertIsNone(receipt["error_code"])
            self.assertTrue(receipt["previous_value_present"])
            self.assertNotIn("test-token", json.dumps(receipt))

    def test_readback_failure_retains_redacted_definite_write_receipt(self):
        class MismatchTransport(MemoryTransport):
            def get(self, url: str, token: str) -> bytes | None:
                self.calls.append(("GET", url))
                if len(self.calls) == 1:
                    return None
                return b"{}"

        with tempfile.TemporaryDirectory() as directory:
            validation = self.validate(self.bundle(Path(directory)))
            with self.assertRaises(publisher.PublicationFailure) as captured:
                publisher.publish_validated(
                    validation,
                    confirmation="publish-control-plane-read-model-v1",
                    token="test",
                    now=self.now,
                    policy_path=self.policy,
                    transport=MismatchTransport(),
                )
            receipt = captured.exception.receipt
            self.assertEqual([], validate_instance(receipt, load_json(self.receipt_schema)))
            self.assertEqual("failed", receipt["status"])
            self.assertTrue(receipt["provider_write_performed"])
            self.assertEqual("performed", receipt["provider_write_outcome"])
            self.assertFalse(receipt["read_back_verified"])
            self.assertEqual("read-back-mismatch", receipt["error_code"])

    def test_publish_rejects_missing_token_wrong_confirmation_and_stale_wait(self):
        with tempfile.TemporaryDirectory() as directory:
            validation = self.validate(self.bundle(Path(directory)))
            with self.assertRaisesRegex(publisher.PublisherError, "confirmation"):
                publisher.publish_validated(
                    validation,
                    confirmation="wrong",
                    token="test",
                    now=self.now,
                    policy_path=self.policy,
                    transport=MemoryTransport(),
                )
            with self.assertRaisesRegex(publisher.PublisherError, "token"):
                publisher.publish_validated(
                    validation,
                    confirmation="publish-control-plane-read-model-v1",
                    token="",
                    now=self.now,
                    policy_path=self.policy,
                    transport=MemoryTransport(),
                )
            with self.assertRaisesRegex(publisher.PublisherError, "became stale"):
                publisher.publish_validated(
                    validation,
                    confirmation="publish-control-plane-read-model-v1",
                    token="test",
                    now=datetime(2026, 7, 14, 10, 41, tzinfo=timezone.utc),
                    policy_path=self.policy,
                    transport=MemoryTransport(),
                )

    def test_workflow_is_manual_fixed_and_environment_protected(self):
        text = self.workflow.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", text)
        self.assertNotIn("schedule:", text)
        self.assertNotIn("pull_request:", text)
        self.assertNotIn("push:", text)
        self.assertIn("environment: ramone-control-plane-publish", text)
        self.assertIn("CF_RAMONE_CONTROL_PLANE_KV_WRITE_TOKEN", text)
        self.assertIn("--name ramone-control-plane-read-model", text)
        self.assertIn("actions: read", text)
        self.assertIn("contents: read", text)
        self.assertNotIn("namespace_id:", text)
        self.assertNotIn("kv_key:", text)
        self.assertNotIn("delete", text.lower())
        self.assertNotIn("bulk", text.lower())


if __name__ == "__main__":
    unittest.main()
