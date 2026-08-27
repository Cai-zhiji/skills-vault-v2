import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from skills_vault.app_paths import AppPaths
from skills_vault.core import Vault, VaultError, load_data, write_data
from skills_vault.deployment import (
    apply_deployment,
    deployment_is_current,
    remove_deployment,
    state_deployments,
)
from skills_vault.platform_adapter import PlatformAdapter
from skills_vault.ops import create_backup, install, install_plan, restore_backup


class PlatformAdapterTests(unittest.TestCase):
    def test_platform_paths_and_default_deployment(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            windows = PlatformAdapter("windows", home, "amd64")
            linux = PlatformAdapter("linux", home, "x86_64")
            self.assertEqual(windows.agent_skill_dirs()["codex"], home / ".agents" / "skills")
            self.assertEqual(windows.agent_skill_dirs()["lux"], home / ".lux" / "skills")
            self.assertEqual(windows.default_deployment_type, "managed-copy")
            self.assertEqual(windows.file_deployment_type, "managed-copy-file")
            self.assertEqual(linux.default_deployment_type, "symlink")
            self.assertEqual(linux.file_deployment_type, "symlink-file")

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

    def test_deployment_rejects_destination_outside_managed_root(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            operation = self.make_operation(base, "managed-copy")
            managed_root = base / "home" / ".agents" / "skills"
            operation.update({
                "path": str(managed_root.parent / "escaped"),
                "allowed_parent": str(managed_root),
                "allowed_source_roots": [str(base / "vault")],
            })
            with self.assertRaises(VaultError):
                apply_deployment(operation)

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

    def test_managed_file_copy_detects_user_change_before_removal(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            operation = self.make_operation(base, "managed-copy-file")
            source = Path(operation["target"]) / "SKILL.md"
            operation.update({"path": str(base / "home" / ".lux" / "skills" / "demo.md"), "target": str(source), "platform": "lux"})
            row = apply_deployment(operation)
            destination = Path(row["path"])
            self.assertTrue(destination.is_file())
            self.assertTrue(deployment_is_current(row))
            destination.write_text("changed")
            with self.assertRaises(VaultError):
                remove_deployment(row)

    def test_symlink_deployment_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            operation = self.make_operation(base, "symlink")
            row = apply_deployment(operation)
            again = apply_deployment(operation, row)
            self.assertEqual(row, again)
            self.assertTrue(Path(row["path"]).is_symlink())

    def test_lux_skill_file_symlink_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            operation = self.make_operation(base, "symlink-file")
            operation.update({
                "path": str(base / "home" / ".lux" / "skills" / "demo.md"),
                "target": str(Path(operation["target"]) / "SKILL.md"),
                "platform": "lux",
            })
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
            (skill / "SKILL.json").write_text('{"version": 1, "skill": "demo", "watchers": []}')
            (root / "profiles").mkdir()
            (root / "annotations").mkdir()
            write_data(root / "registry.yaml", {"schema_version": 1, "sources": {}})
            write_data(root / "lock.yaml", {"schema_version": 1, "sources": {}})
            write_data(root / "annotations" / "skills.yaml", {"schema_version": 1, "skills": {}})
            write_data(
                root / "profiles" / "base.yaml",
                {"schema_version": 1, "platforms": ["codex", "claude", "lux"], "include": ["my/demo"]},
            )
            vault = Vault(root)
            vault.scan()
            adapter = PlatformAdapter("windows", base / "home", "amd64")

            result = install(vault, ["base"], assume_yes=True, adapter=adapter)
            self.assertTrue(Path(result["backup"]).is_dir())

            state = load_data(vault.state_dir / "install-state.json")
            self.assertEqual(state["schema_version"], 2)
            self.assertEqual(
                {row["deployment_type"] for row in state["deployments"]},
                {"managed-copy", "managed-copy-file"},
            )
            self.assertTrue((adapter.agent_skill_dirs()["codex"] / "demo" / "SKILL.md").is_file())
            self.assertTrue((adapter.agent_skill_dirs()["claude"] / "demo" / "SKILL.md").is_file())
            lux_md = adapter.agent_skill_dirs()["lux"] / "demo.md"
            self.assertTrue(lux_md.is_file())
            self.assertTrue((adapter.agent_skill_dirs()["lux"] / "demo.json").is_file())
            self.assertTrue((adapter.agent_skill_dirs()["lux"] / "demo" / "SKILL.md").is_file())

            (skill / "SKILL.md").write_text("---\nname: demo\ndescription: Updated.\n---\n")
            changed = install_plan(vault, ["base"], adapter)["changes"]["changed"]
            self.assertIn(str(lux_md), {row["path"] for row in changed})

            backup = create_backup(vault, adapter)
            lux_md.unlink()
            restore_backup(vault, backup.name, assume_yes=True, adapter=adapter)
            restored = load_data(vault.state_dir / "install-state.json")
            self.assertTrue(lux_md.is_file())
            self.assertIn("lux", {row["platform"] for row in restored["deployments"]})

            manifest_path = backup / "manifest.json"
            manifest = load_data(manifest_path)
            outside = base / "outside"
            outside.mkdir()
            (outside / "keep.txt").write_text("keep")
            manifest["targets"]["lux-skills"]["path"] = str(outside)
            write_data(manifest_path, manifest)
            restore_backup(vault, backup.name, assume_yes=True, adapter=adapter)
            self.assertEqual((outside / "keep.txt").read_text(), "keep")

            lux_md.write_text("user change")
            blocked = install_plan(vault, ["base"], adapter)["blocked"]
            self.assertIn(str(lux_md), {row["path"] for row in blocked})
            with self.assertRaises(VaultError):
                install(vault, ["base"], assume_yes=True, adapter=adapter)
            self.assertEqual(lux_md.read_text(), "user change")

            manifest_path = backup / "manifest.json"
            manifest = load_data(manifest_path)
            manifest["targets"]["unexpected"] = {"path": str(base / "outside"), "existed": True}
            write_data(manifest_path, manifest)
            with self.assertRaises(VaultError):
                restore_backup(vault, backup.name, assume_yes=True, adapter=adapter)
            self.assertEqual(lux_md.read_text(), "user change")

            (skill / "SKILL.json").write_text(
                '{"version": 1, "skill": "demo", "watchers": ["invalid"]}'
            )
            with self.assertRaises(VaultError):
                install_plan(vault, ["base"], adapter)

    def test_install_plan_blocks_unmanaged_lux_destination(self):
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
            write_data(
                root / "profiles" / "lux.yaml",
                {"schema_version": 1, "platform": "lux", "include": ["my/demo"]},
            )
            vault = Vault(root)
            vault.scan()
            adapter = PlatformAdapter("windows", base / "home", "amd64")
            collision = adapter.agent_skill_dirs()["lux"] / "demo.md"
            collision.parent.mkdir(parents=True)
            collision.write_text("unmanaged")

            plan = install_plan(vault, ["lux"], adapter)
            self.assertIn(str(collision), {row["path"] for row in plan["blocked"]})
            self.assertEqual(collision.read_text(), "unmanaged")

    def test_install_rolls_back_when_a_later_platform_component_fails(self):
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
            write_data(
                root / "profiles" / "base.yaml",
                {"schema_version": 1, "platforms": ["codex", "claude", "lux"], "include": ["my/demo"]},
            )
            vault = Vault(root)
            vault.scan()
            adapter = PlatformAdapter("windows", base / "home", "amd64")
            calls = 0

            def fail_second(operation, managed=None):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise VaultError("injected failure")
                return apply_deployment(operation, managed)

            with patch("skills_vault.ops.apply_deployment", side_effect=fail_second):
                with self.assertRaises(VaultError):
                    install(vault, ["base"], assume_yes=True, adapter=adapter)

            for target in adapter.agent_skill_dirs().values():
                self.assertFalse(target.exists(), str(target))


if __name__ == "__main__":
    unittest.main()
