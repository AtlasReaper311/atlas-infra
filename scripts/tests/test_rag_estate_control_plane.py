import unittest

from scripts.validate_rag_estate_control_plane import validate


class RagEstateControlPlaneTests(unittest.TestCase):
    def test_control_plane_is_secret_free_and_fail_closed(self):
        self.assertEqual([], validate())


if __name__ == "__main__":
    unittest.main()
