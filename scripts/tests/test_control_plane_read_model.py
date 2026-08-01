from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

import control_plane_read_model as read_model
from control_plane_contracts import canonical_json, load_json, validate_instance


class ControlPlaneReadModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary_sources = ROOT / 'tests/fixtures/control-plane-summary/sources'
        cls.collection_sources = ROOT / 'tests/fixtures/control-plane-read-model/collections'
        cls.authority_root = ROOT / 'tests/fixtures/control-plane-read-model/authorities'
        cls.policy = ROOT / 'policy/control-plane-read-model.json'
        cls.schema = ROOT / 'contracts/ramone/v1/control-plane-read-model.schema.json'
        cls.source_schema = ROOT / 'contracts/ramone/v1/control-plane-read-model-source.schema.json'
        cls.summary_schema = ROOT / 'contracts/v1/control-plane-summary.schema.json'
        cls.now = datetime(2026, 7, 14, 10, 30, tzinfo=timezone.utc)
        cls.revision = 'a' * 40

    def build(self, **overrides):
        args = {
            'summary_sources': self.summary_sources,
            'collection_sources': self.collection_sources,
            'authority_root': self.authority_root,
            'policy_path': self.policy,
            'schema_path': self.schema,
            'source_schema_path': self.source_schema,
            'summary_schema_path': self.summary_schema,
            'now': self.now,
            'source_revision': self.revision,
        }
        args.update(overrides)
        return read_model.build_read_model(**args)

    def test_build_is_deterministic_and_schema_valid(self):
        first, first_receipt = self.build()
        second, second_receipt = self.build()
        self.assertEqual(first, second)
        self.assertEqual(first_receipt, second_receipt)
        self.assertEqual([], validate_instance(first, load_json(self.schema)))
        self.assertEqual(21, len(first['sources']))
        self.assertEqual(False, first_receipt['provider_write_performed'])
        self.assertEqual('control-plane:read-model:v1', first_receipt['bounded_kv_key'])
        self.assertEqual(1, first_receipt['collection_counts']['services'])
        expected_root = ROOT / 'tests/fixtures/control-plane-read-model/expected'
        self.assertEqual(load_json(expected_root / 'read-model.json'), first)
        self.assertEqual(load_json(expected_root / 'dry-run-receipt.json'), first_receipt)

    def test_fingerprints_cover_sources_and_complete_model(self):
        model, _ = self.build()
        source_expected = 'sha256:' + hashlib.sha256(canonical_json(model['sources']).encode()).hexdigest()
        self.assertEqual(source_expected, model['source_fingerprint'])
        payload = copy.deepcopy(model)
        actual = payload.pop('read_model_fingerprint')
        expected = 'sha256:' + hashlib.sha256(canonical_json(payload).encode()).hexdigest()
        self.assertEqual(expected, actual)

    def test_missing_or_unexpected_sources_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'collections'
            shutil.copytree(self.collection_sources, target)
            (target / 'services.json').unlink()
            with self.assertRaisesRegex(read_model.ProducerError, 'inventory mismatch'):
                self.build(collection_sources=target)
            shutil.copy(self.collection_sources / 'services.json', target / 'services.json')
            (target / 'extra.json').write_text('{}', encoding='utf-8')
            with self.assertRaisesRegex(read_model.ProducerError, 'inventory mismatch'):
                self.build(collection_sources=target)

    def test_secret_bearing_and_machine_local_values_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'collections'
            shutil.copytree(self.collection_sources, target)
            document = load_json(target / 'services.json')
            document['items'][0]['token'] = 'fixture'
            (target / 'services.json').write_text(json.dumps(document), encoding='utf-8')
            with self.assertRaisesRegex(read_model.ProducerError, 'forbidden or secret-bearing key'):
                self.build(collection_sources=target)

            shutil.rmtree(target)
            shutil.copytree(self.collection_sources, target)
            document = load_json(target / 'services.json')
            document['items'][0]['display_name'] = 'http://127.0.0.1:8123'
            (target / 'services.json').write_text(json.dumps(document), encoding='utf-8')
            with self.assertRaisesRegex(read_model.ProducerError, 'machine-local'):
                self.build(collection_sources=target)

    def test_non_public_identity_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'collections'
            shutil.copytree(self.collection_sources, target)
            document = load_json(target / 'backups.json')
            document['items'][0]['service_id'] = 'private-service'
            (target / 'backups.json').write_text(json.dumps(document), encoding='utf-8')
            with self.assertRaisesRegex(read_model.ProducerError, 'non-public service identity'):
                self.build(collection_sources=target)

    def test_expired_collection_becomes_stale(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'collections'
            shutil.copytree(self.collection_sources, target)
            document = load_json(target / 'services.json')
            document['stale_after'] = '2026-07-14T10:01:00Z'
            document['state'] = 'healthy'
            document['items'][0]['state'] = 'healthy'
            (target / 'services.json').write_text(json.dumps(document), encoding='utf-8')
            model, _ = self.build(collection_sources=target)
            self.assertEqual('stale', model['services'][0]['state'])
            source = next(item for item in model['sources'] if item['source_id'] == 'services')
            self.assertEqual('stale', source['state'])
            self.assertNotEqual('healthy', model['state'])

    def test_malformed_summary_source_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'summary'
            shutil.copytree(self.summary_sources, target)
            document = load_json(target / 'health.json')
            document['data']['components_total'] = '34'
            (target / 'health.json').write_text(json.dumps(document), encoding='utf-8')
            with self.assertRaisesRegex(read_model.ProducerError, 'contains malformed data'):
                self.build(summary_sources=target)

    def test_policy_maximum_age_caps_the_model(self):
        model, _ = self.build()
        self.assertEqual('2026-07-14T10:40:00Z', model['stale_after'])

    def test_collection_producer_and_dependencies_must_be_public(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'collections'
            shutil.copytree(self.collection_sources, target)
            document = load_json(target / 'services.json')
            document['producer'] = 'AtlasReaper311/private-repository'
            (target / 'services.json').write_text(json.dumps(document), encoding='utf-8')
            with self.assertRaisesRegex(read_model.ProducerError, 'producer is not public'):
                self.build(collection_sources=target)

            shutil.rmtree(target)
            shutil.copytree(self.collection_sources, target)
            document = load_json(target / 'services.json')
            document['items'][0]['dependencies'].append('private-service')
            (target / 'services.json').write_text(json.dumps(document), encoding='utf-8')
            with self.assertRaisesRegex(read_model.ProducerError, 'non-public dependency identity'):
                self.build(collection_sources=target)

    def test_invalid_revision_and_oversized_output_are_rejected(self):
        with self.assertRaisesRegex(read_model.ProducerError, 'source_revision'):
            self.build(source_revision='main')
        with tempfile.TemporaryDirectory() as directory:
            policy = load_json(self.policy)
            policy['output']['max_bytes'] = 1024
            policy_path = Path(directory) / 'policy.json'
            policy_path.write_text(json.dumps(policy), encoding='utf-8')
            with self.assertRaisesRegex(read_model.ProducerError, 'exceeds 1024 bytes'):
                self.build(policy_path=policy_path)

    def test_cli_writes_only_local_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'read-model.json'
            receipt = Path(directory) / 'receipt.json'
            command = [
                sys.executable,
                str(SCRIPTS / 'control_plane_read_model.py'),
                '--summary-sources', str(self.summary_sources),
                '--collection-sources', str(self.collection_sources),
                '--authority-root', str(self.authority_root),
                '--policy', str(self.policy),
                '--schema', str(self.schema),
                '--source-schema', str(self.source_schema),
                '--summary-schema', str(self.summary_schema),
                '--source-revision', self.revision,
                '--now', '2026-07-14T10:30:00Z',
                '--output', str(output),
                '--receipt', str(receipt),
            ]
            completed = subprocess.run(command, check=True, text=True, capture_output=True)
            self.assertIn('provider_write_performed=false', completed.stdout)
            self.assertTrue(output.is_file())
            self.assertTrue(receipt.is_file())
            self.assertFalse(load_json(receipt)['provider_write_performed'])


if __name__ == '__main__':
    unittest.main()
