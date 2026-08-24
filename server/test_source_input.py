import unittest

from skills_vault.source_input import parse_source_input


class SourceInputTests(unittest.TestCase):
    def test_parses_skills_cli_command_without_name(self):
        spec = parse_source_input(
            "npx skills add owner/repo --skill docs --skill testing",
            "skills-cli",
        )
        self.assertEqual(spec.source_ref, "owner/repo")
        self.assertEqual(spec.source_id, "owner-repo")
        self.assertEqual(spec.skills, ["docs", "testing"])
        self.assertEqual(spec.input_kind, "skills-cli-command")

    def test_parses_git_clone_without_name(self):
        spec = parse_source_input(
            "git clone https://github.com/owner/repo.git",
            "git",
        )
        self.assertEqual(spec.source_url, "https://github.com/owner/repo.git")
        self.assertEqual(spec.source_id, "owner-repo")
        self.assertEqual(spec.input_kind, "git-command")

    def test_rejects_shell_chaining(self):
        with self.assertRaises(ValueError):
            parse_source_input("npx skills add owner/repo && touch /tmp/pwned", "skills-cli")

    def test_custom_id_remains_supported(self):
        spec = parse_source_input("https://github.com/owner/repo.git", "git", "my-source")
        self.assertEqual(spec.source_id, "my-source")


if __name__ == "__main__":
    unittest.main()
