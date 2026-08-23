import os
import unittest

from skills_vault.runtime import parent_is_alive, session_token, startup_id


class RuntimeTests(unittest.TestCase):
    def test_runtime_identifiers_are_random_and_high_entropy(self) -> None:
        first = session_token()
        second = session_token()
        self.assertNotEqual(first, second)
        self.assertGreaterEqual(len(first), 40)
        self.assertEqual(len(startup_id()), 32)

    def test_current_process_is_alive(self) -> None:
        self.assertTrue(parent_is_alive(os.getpid()))
        self.assertFalse(parent_is_alive(-1))


if __name__ == "__main__":
    unittest.main()
