import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from skills_vault.core import Vault, write_data
from skills_vault.dependencies import dependency_install_plan, dependency_status
from skills_vault.executable_resolver import ResolvedExecutable
from skills_vault.platform_adapter import PlatformAdapter
from skills_vault.services import ServiceError, git_source_preview


class DependencyTests(unittest.TestCase):
    def test_offline_status_does_not_execute_skills_cli(self):
        adapter = PlatformAdapter("windows", Path("C:/Users/Test"), "amd64")
        paths = {
            "git": Path("C:/Tools/git.exe"),
            "node": Path("C:/Tools/node.exe"),
            "npm": Path("C:/Tools/npm.cmd"),
            "npx": Path("C:/Tools/npx.cmd"),
            "winget": Path("C:/Windows/winget.exe"),
        }
        with patch.object(PlatformAdapter, "executable", side_effect=lambda name: paths.get(name)), patch(
            "skills_vault.dependencies._version", return_value="1.0.0"
        ):
            result = dependency_status(adapter)
        by_id = {row["id"]: row for row in result["dependencies"]}
        self.assertEqual(by_id["git"]["status"], "available")
        self.assertEqual(by_id["skills-cli"]["status"], "unverified")
        self.assertTrue(result["offline"])

    def test_install_plans_only_auto_execute_trusted_providers(self):
        windows = PlatformAdapter("windows", Path("C:/Users/Test"), "amd64")
        linux = PlatformAdapter("linux", Path("/home/test"), "x86_64")
        with patch(
            "skills_vault.dependencies.resolve_executable",
            return_value=ResolvedExecutable("winget", Path("C:/Windows/winget.exe"), "PATH"),
        ):
            plan = dependency_install_plan("git", windows)
        self.assertTrue(plan["can_execute"])
        self.assertIn("Git.Git", plan["command"])
        linux_plan = dependency_install_plan("node", linux)
        self.assertFalse(linux_plan["can_execute"])
        self.assertTrue(linux_plan["requires_elevation"])

    def test_missing_git_returns_structured_service_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "vault"
            (root / "profiles").mkdir(parents=True)
            (root / "my-skills").mkdir()
            (root / "annotations").mkdir()
            write_data(root / "registry.yaml", {"schema_version": 1, "sources": {}})
            write_data(root / "lock.yaml", {"schema_version": 1, "sources": {}})
            write_data(root / "annotations" / "skills.yaml", {"schema_version": 1, "skills": {}})
            vault = Vault(root)
            vault.scan()
            adapter = PlatformAdapter("windows", Path(directory) / "home")
            with patch("skills_vault.services.current_platform", return_value=adapter), patch(
                "skills_vault.services.resolve_executable", return_value=None
            ), self.assertRaises(ServiceError) as caught:
                git_source_preview(vault, "demo", "https://example.com/demo.git")
            self.assertEqual(caught.exception.code, "dependency_missing")
            self.assertEqual(caught.exception.details["dependency"], "git")


if __name__ == "__main__":
    unittest.main()
