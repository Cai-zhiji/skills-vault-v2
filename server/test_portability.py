import tempfile
import unittest
from pathlib import Path

from skills_vault.app_paths import AppPaths
from skills_vault.core import Vault, VaultError, load_data, write_data
from skills_vault.deployment import (
    apply_deployment,
    deployment_is_current,
    remove_deployment,
    state_deployments,
)
from skills_vault.platform_adapter import PlatformAdapter
from skills_vault.ops import install


class PlatformAdapterTests(unittest.TestCase):
    def test_platform_paths_and_default_deployment(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            windows = PlatformAdapter("windows", home, "amd64")
            linux = PlatformAdapter("linux", home, "x86_64")
            self.assertEqual(windows.agent_skill_dirs()["codex"], home / ".agents" / "skills")
            self.assertEqual(windows.default_deployment_type, "managed-copy")
            self.assertEqual(linux.default_deployment_type, "symlink")

    def test_desktop_paths_follow_platform_conventions(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            resources = home / "app"
            mac = AppPaths.for_desktop(resources, PlatformAdapter("darwin", home))
            windows = AppPaths.for_desktop(
                resources,
                PlatformAdapter("windows", home),
                {"LOCALAPPDATA": str(home / "Local Data")},
            )
            linux = AppPaths.for_desktop(
                resources,
                PlatformAdapter("linux", home),
                {"XDG_CONFIG_HOME": str(home / "cfg"), "XDG_CACHE_HOME": str(home / "tmp")},
            )
            self.assertEqual(mac.config_root, home / "Library" / "Application Support" / "Skills Vault")
            self.assertEqual(windows.config_root, home / "Local Data" / "Skills Vault")
            self.assertEqual(linux.config_root, home / "cfg" / "skills-vault")
            self.assertEqual(linux.default_vault_root, home / "Documents" / "Skills Vault")


class DeploymentTests(unittest.TestCase):
    def make_operation(self, base: Path, deployment_type: str):
        source = base / "vault" / "my-skills" / "demo"
        source.mkdir(parents=True)
        (source / "SKILL.md").write_text("---\nname: demo\ndescription: Demo.\n---\n")
        return {
            "path": str(base / "home" / ".agents" / "skills" / "demo"),
            "target": str(source),
            "skill_id": "my/demo",
            "platform": "codex",
            "deployment_type": deployment_type,
        }

    def test_v1_links_are_read_as_symlink_deployments(self):
        rows = state_deployments(
            {"links": [{"path": "/tmp/demo", "target": "/tmp/source", "skill_id": "my/demo", "platform": "codex"}]}
        )
        self.assertEqual(rows[0]["deployment_type"], "symlink")

    def test_managed_copy_detects_user_change_before_removal(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            row = apply_deployment(self.make_operation(base, "managed-copy"))
            destination = Path(row["path"])
            self.assertTrue(deployment_is_current(row))
            (destination / "SKILL.md").write_text("changed")
            self.assertFalse(deployment_is_current(row))
            with self.assertRaises(VaultError):
                remove_deployment(row)
            self.assertTrue(destination.exists())

    def test_symlink_deployment_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            operation = self.make_operation(base, "symlink")
            row = apply_deployment(operation)
            again = apply_deployment(operation, row)
            self.assertEqual(row, again)
            self.assertTrue(Path(row["path"]).is_symlink())

    def test_windows_install_uses_managed_copy_and_schema_v2(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "vault"
            skill = root / "my-skills" / "demo"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("---\nname: demo\ndescription: Demo.\n---\n")
            (root / "profiles").mkdir()
            (root / "annotations").mkdir()
            write_data(root / "registry.yaml", {"schema_version": 1, "sources": {}})
            write_data(root / "lock.yaml", {"schema_version": 1, "sources": {}})
            write_data(root / "annotations" / "skills.yaml", {"schema_version": 1, "skills": {}})
            write_data(root / "profiles" / "base.yaml", {"schema_version": 1, "include": ["my/demo"]})
            vault = Vault(root)
            vault.scan()
            adapter = PlatformAdapter("windows", base / "home", "amd64")

            install(vault, ["base"], assume_yes=True, adapter=adapter)

            state = load_data(vault.state_dir / "install-state.json")
            self.assertEqual(state["schema_version"], 2)
            self.assertEqual({row["deployment_type"] for row in state["deployments"]}, {"managed-copy"})
            self.assertTrue((adapter.agent_skill_dirs()["codex"] / "demo" / "SKILL.md").is_file())
            self.assertTrue((adapter.agent_skill_dirs()["claude"] / "demo" / "SKILL.md").is_file())


if __name__ == "__main__":
    unittest.main()
