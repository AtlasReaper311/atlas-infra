import hashlib
import json
import unittest

import chaos_harness
import estate_policy


class EvidenceCanonicalTests(unittest.TestCase):
    def test_integral_floats_normalise_to_json_integer_form(self):
        value = {
            "score": 100.0,
            "weight": 1.0,
            "fraction": 0.5,
            "nested": [{"value": 42.0}],
        }

        expected = (
            b'{"fraction":0.5,"nested":[{"value":42}],'
            b'"score":100,"weight":1}'
        )

        self.assertEqual(expected, estate_policy.canonical_json_bytes(value))
        self.assertEqual(expected, chaos_harness.canonical_json_bytes(value))

    def test_fingerprint_is_stable_after_json_parse(self):
        value = {
            "schema": "test/v1",
            "score": 100.0,
            "weight": 1.0,
            "fraction": 0.5,
        }

        producer = hashlib.sha256(
            estate_policy.canonical_json_bytes(value)
        ).hexdigest()

        parsed = json.loads(
            estate_policy.canonical_json_bytes(value).decode("utf-8")
        )

        consumer = hashlib.sha256(
            estate_policy.canonical_json_bytes(parsed)
        ).hexdigest()

        self.assertEqual(producer, consumer)


if __name__ == "__main__":
    unittest.main()
