import stat
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
from skills_vault.ops import (
    create_backup,
    current_state_deployments,
    install,
    install_plan,
    restore_backup,
)


class PlatformAdapterTests(unittest.TestCase):
    def test_platform_paths_and_default_deployment(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            windows = PlatformAdapter("windows", home, "amd64")
            linux = PlatformAdapter("linux", home, "x86_64")
            self.assertEqual(windows.agent_skill_dirs()["codex"], home / ".agents" / "skills")
            self.assertEqual(windows.agent_skill_dirs()["lux"], home / ".lux_neo" / "skills")
            self.assertEqual(windows.default_deployment_type, "managed-copy")
            self.assertEqual(windows.file_deployment_type, "managed-copy-file")
            self.assertEqual(linux.default_deployment_type, "symlink")
            self.assertEqual(linux.file_deployment_type, "symlink-file")

    def test_managed_skill_path_check_is_lexical_and_platform_scoped(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "home"
            adapter = PlatformAdapter("windows", home, "amd64")
            self.assertTrue(
                adapter.manages_skill_path("lux", home / ".lux_neo" / "skills" / "demo.md")
            )
            self.assertTrue(
                adapter.manages_skill_path("lux", home / ".lux" / "skills" / "legacy.md")
            )
            self.assertFalse(
                adapter.manages_skill_path("lux", home / ".lux_neo" / "outside" / "demo.md")
            )
            self.assertFalse(
                adapter.manages_skill_path("unknown", home / ".lux_neo" / "skills" / "demo.md")
            )

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

    def test_managed_copy_removes_readonly_files(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            operation = self.make_operation(base, "managed-copy")
            readonly = Path(operation["target"]) / ".git" / "objects" / "pack" / "demo.idx"
            readonly.parent.mkdir(parents=True)
            readonly.write_text("pack")
            readonly.chmod(stat.S_IREAD)
            row = apply_deployment(operation)
            destination = Path(row["path"])
            self.assertTrue((destination / ".git" / "objects" / "pack" / "demo.idx").is_file())

            self.assertTrue(remove_deployment(row))
            self.assertFalse(destination.exists())

    def test_managed_file_copy_detects_user_change_before_removal(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            operation = self.make_operation(base, "managed-copy-file")
            source = Path(operation["target"]) / "SKILL.md"
            operation.update({"path": str(base / "home" / ".lux_neo" / "skills" / "demo.md"), "target": str(source), "platform": "lux"})
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
                "path": str(base / "home" / ".lux_neo" / "skills" / "demo.md"),
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
            manifest["targets"]["lux-neo-skills"]["path"] = str(outside)
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

    def test_install_migrates_managed_lux_desktop_rows_to_lux_neo(self):
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
            old_root = adapter.legacy_lux_skill_dir
            legacy_rows = [
                apply_deployment(
                    {
                        "path": str(old_root / "demo"),
                        "target": str(skill),
                        "skill_id": "my/demo",
                        "platform": "lux",
                        "component": "resources",
                        "deployment_type": "managed-copy",
                        "allowed_parent": str(old_root),
                        "allowed_source_roots": [str(root)],
                    }
                ),
                apply_deployment(
                    {
                        "path": str(old_root / "demo.md"),
                        "target": str(skill / "SKILL.md"),
                        "skill_id": "my/demo",
                        "platform": "lux",
                        "component": "skill",
                        "deployment_type": "managed-copy-file",
                        "allowed_parent": str(old_root),
                        "allowed_source_roots": [str(root)],
                    }
                ),
            ]
            (old_root / "keep.txt").write_text("unmanaged")
            write_data(
                vault.state_dir / "install-state.json",
                {"schema_version": 2, "deployments": legacy_rows, "links": legacy_rows},
            )
            with patch("pathlib.Path.home", return_value=adapter.home):
                before = vault.resolve_profile_details(["lux"], "lux")
            self.assertEqual(before["status"]["my/demo"]["state"], "saved-not-installed")

            result = install(vault, ["lux"], assume_yes=True, adapter=adapter)

            neo_root = adapter.agent_skill_dirs()["lux"]
            self.assertTrue((neo_root / "demo.md").is_file())
            self.assertTrue((neo_root / "demo" / "SKILL.md").is_file())
            self.assertFalse((old_root / "demo.md").exists())
            self.assertFalse((old_root / "demo").exists())
            self.assertEqual((old_root / "keep.txt").read_text(), "unmanaged")
            manifest = load_data(Path(result["backup"]) / "manifest.json")
            self.assertIn("lux-skills", manifest["targets"])
            self.assertIn("lux-neo-skills", manifest["targets"])
            state = load_data(vault.state_dir / "install-state.json")
            self.assertTrue(state["deployments"])
            self.assertTrue(all(".lux_neo" in row["path"] for row in state["deployments"]))
            post_migration = load_data(create_backup(vault, adapter) / "manifest.json")
            self.assertNotIn("lux-skills", post_migration["targets"])

    def test_install_ignores_and_preserves_foreign_legacy_state(self):
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
            foreign_state = {
                "schema_version": 2,
                "installed_at": "2026-08-26T09:13:07+08:00",
                "deployments": [
                    {
                        "path": "/Users/previous/.agents/skills/demo",
                        "target": "/Users/previous/Documents/Skills Vault/my-skills/demo",
                        "skill_id": "my/demo",
                        "platform": "codex",
                        "deployment_type": "symlink",
                    },
                    {
                        "path": "/Users/previous/.claude/skills/demo",
                        "target": "/Users/previous/Documents/Skills Vault/my-skills/demo",
                        "skill_id": "my/demo",
                        "platform": "claude",
                        "deployment_type": "symlink",
                    },
                ],
            }
            write_data(vault.state_dir / "install-state.json", foreign_state)
            adapter = PlatformAdapter("windows", base / "home", "amd64")

            result = install(vault, ["lux"], assume_yes=True, adapter=adapter)

            backup = Path(result["backup"])
            self.assertEqual(load_data(backup / "previous-install-state.json"), foreign_state)
            state = load_data(vault.state_dir / "install-state.json")
            self.assertEqual(state["installation"]["platform"], "windows")
            self.assertEqual(state["installation"]["home"], str(adapter.home))
            self.assertEqual(
                state["installation"]["id"],
                (adapter.home / ".skills-vault" / "installation-id").read_text(),
            )
            self.assertEqual({row["platform"] for row in state["deployments"]}, {"lux"})
            self.assertTrue((adapter.agent_skill_dirs()["lux"] / "demo.md").is_file())

    def test_same_home_state_from_another_machine_is_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            adapter = PlatformAdapter("windows", base / "home", "amd64")
            identity = adapter.home / ".skills-vault" / "installation-id"
            identity.parent.mkdir(parents=True)
            identity.write_text("a" * 32)
            state = {
                "schema_version": 2,
                "installation": {
                    "platform": "windows",
                    "home": str(adapter.home),
                    "id": "f" * 32,
                },
                "deployments": [
                    {
                        "path": str(adapter.agent_skill_dirs()["codex"] / "demo"),
                        "target": str(base / "vault" / "my-skills" / "demo"),
                        "skill_id": "my/demo",
                        "platform": "codex",
                    }
                ],
            }

            self.assertEqual(current_state_deployments(state, adapter), [])
            self.assertNotEqual(
                (adapter.home / ".skills-vault" / "installation-id").read_text(),
                state["installation"]["id"],
            )

    def test_mixed_current_and_out_of_bounds_state_remains_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "vault"
            (root / ".vault").mkdir(parents=True)
            adapter = PlatformAdapter("windows", base / "home", "amd64")
            current = adapter.agent_skill_dirs()["codex"] / "demo"
            write_data(
                root / ".vault" / "install-state.json",
                {
                    "schema_version": 2,
                    "installation": {
                        "platform": "linux",
                        "home": "/home/foreign",
                        "id": "f" * 32,
                    },
                    "deployments": [
                        {
                            "path": str(current),
                            "target": str(root / "my-skills" / "demo"),
                            "skill_id": "my/demo",
                            "platform": "codex",
                        },
                        {
                            "path": str(base / "other-home" / ".agents" / "skills" / "escape"),
                            "target": str(root / "my-skills" / "escape"),
                            "skill_id": "my/escape",
                            "platform": "codex",
                        },
                    ],
                },
            )
            vault = Vault(root)

            with self.assertRaisesRegex(VaultError, "metadata does not match"):
                create_backup(vault, adapter)

    def test_foreign_metadata_with_only_current_paths_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            adapter = PlatformAdapter("windows", base / "home", "amd64")
            state = {
                "schema_version": 2,
                "installation": {
                    "platform": "linux",
                    "home": "/home/foreign",
                    "id": "f" * 32,
                },
                "deployments": [
                    {
                        "path": str(adapter.agent_skill_dirs()["codex"] / "demo"),
                        "target": str(base / "vault" / "my-skills" / "demo"),
                        "skill_id": "my/demo",
                        "platform": "codex",
                    }
                ],
            }

            with self.assertRaisesRegex(VaultError, "metadata does not match"):
                current_state_deployments(state, adapter)

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
