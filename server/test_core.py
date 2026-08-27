import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from skills_vault import skills_cli
from skills_vault.core import (
    Vault,
    VaultError,
    classify,
    git,
    git_clean,
    load_data,
    parse_frontmatter,
    replace_frontmatter_name,
    tree_fingerprint,
    write_data,
)
from skills_vault.executable_resolver import ResolvedExecutable
from skills_vault.platform_adapter import PlatformAdapter
from skills_vault.ops import (
    _https_fallback,
    _reset_user_skill_dirs,
    _restore_backup_path,
    apply_updates,
    create_backup,
    install,
    install_plan,
    lint_vault,
    source_audit,
    update_plan,
)
from skills_vault.services import (
    ServiceError,
    compare_skills,
    delete_skills_apply,
    delete_skills_preview,
    install_apply,
    install_preview,
    managed_selection_payload,
    personal_catalog_state,
    restore_preview,
    scan_catalog,
    save_skill_guide,
    skill_guide_template,
    save_managed_selection,
    source_policy_apply,
    source_policy_preview,
    source_delete_apply,
    source_delete_preview,
    skills_cli_source_apply,
    skills_cli_source_preview,
    update_preview,
)


INTEGRATION_ROOT = os.environ.get("SKILLS_VAULT_TEST_ROOT")


class FrontmatterTests(unittest.TestCase):
    def test_parses_folded_description(self):
        metadata, body = parse_frontmatter(
            "---\nname: demo\ndescription: >\n  First line\n  second line\ndisable-model-invocation: true\n---\nBody\n"
        )
        self.assertEqual(metadata["name"], "demo")
        self.assertEqual(metadata["description"], "First line second line")
        self.assertTrue(metadata["disable-model-invocation"])
        self.assertEqual(body, "Body")

    def test_replaces_or_adds_name(self):
        text = "---\ndescription: useful\n---\nDo it.\n"
        changed = replace_frontmatter_name(text, "derived-name")
        metadata, _ = parse_frontmatter(changed)
        self.assertEqual(metadata["name"], "derived-name")

    def test_ordered_classification(self):
        rules = [
            {"pattern": "skills/published/*/SKILL.md", "as": "published"},
            {"pattern": "**/SKILL.md", "as": "unknown"},
        ]
        self.assertEqual(classify("skills/published/a/SKILL.md", rules), "published")
        self.assertEqual(classify("template/SKILL.md", rules), "unknown")

    def test_tree_fingerprint_changes_with_content(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "a.txt").write_text("a")
            before = tree_fingerprint(root)
            (root / "a.txt").write_text("b")
            self.assertNotEqual(before, tree_fingerprint(root))


class V2CatalogAndUpdateTests(unittest.TestCase):
    def make_personal_vault(self, root: Path) -> Vault:
        (root / "annotations").mkdir(parents=True)
        (root / "profiles").mkdir()
        (root / "catalog").mkdir()
        skill = root / "my-skills" / "demo"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\nname: demo\ndescription: Demo skill.\n---\n\nRun demo.\n",
            encoding="utf-8",
        )
        write_data(root / "registry.yaml", {"schema_version": 1, "sources": {}})
        write_data(root / "lock.yaml", {"schema_version": 1, "sources": {}})
        write_data(
            root / "annotations" / "skills.yaml",
            {"schema_version": 1, "skills": {}},
        )
        return Vault(root)

    def test_personal_catalog_state_detects_change_and_scan_closes_it(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            vault = self.make_personal_vault(root)
            vault.scan()
            self.assertTrue(personal_catalog_state(vault)["fresh"])
            skill_md = root / "my-skills" / "demo" / "SKILL.md"
            skill_md.write_text(skill_md.read_text() + "Changed.\n", encoding="utf-8")
            self.assertEqual(personal_catalog_state(vault)["changed"], ["my/demo"])
            result = scan_catalog(vault)
            self.assertEqual(result["changed"], ["my/demo"])
            self.assertTrue(result["catalog_state"]["fresh"])

    def test_catalog_omits_unsafe_and_windows_reserved_skill_names(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            vault = self.make_personal_vault(root)
            skill_md = root / "my-skills" / "demo" / "SKILL.md"
            for name in ("../../outside", "con"):
                skill_md.write_text(f"---\nname: {name}\ndescription: unsafe\n---\n")
                self.assertEqual(vault.scan()["skills"], [])

    def test_legacy_profile_without_platform_does_not_enable_lux(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            vault = self.make_personal_vault(root)
            write_data(root / "profiles" / "legacy.yaml", {"schema_version": 1, "include": ["my/demo"]})
            vault.scan()
            self.assertEqual(vault.resolve_profile_details(["legacy"], "lux")["direct"], [])

    def test_legacy_catalog_is_rebuilt_with_lux_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            vault = self.make_personal_vault(root)
            write_data(root / "catalog" / "catalog.json", {"schema_version": 1, "skills": []})
            catalog = vault.catalog()
            skill = catalog["skills"][0]
            self.assertEqual(catalog["schema_version"], 2)
            self.assertIn("lux", skill["compatibility"]["platforms"])
            self.assertEqual(skill["invocation"]["lux"], "/skill load demo")

    def test_update_preview_excludes_dirty_fast_forward_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            vault = self.make_personal_vault(root)
            vault.scan()
            rows = [
                {
                    "source_id": "dirty",
                    "source_kind": "git",
                    "status": "fast-forward",
                    "head": "a",
                    "target": "b",
                    "dirty": True,
                    "commits": ["b update"],
                    "changes": [],
                    "risk_signals": [],
                },
                {
                    "source_id": "safe",
                    "source_kind": "git",
                    "status": "fast-forward",
                    "head": "a",
                    "target": "b",
                    "dirty": False,
                    "commits": ["b update"],
                    "changes": [],
                    "risk_signals": [],
                },
            ]
            with patch("skills_vault.services.update_plan", return_value=rows):
                preview = update_preview(vault)
            self.assertEqual(preview["actionable_source_ids"], ["safe"])
            self.assertEqual(preview["blocked_source_ids"], ["dirty"])
            statuses = {row["source_id"]: row["status"] for row in preview["sources"]}
            self.assertEqual(statuses["dirty"], "blocked-dirty")
            token = vault.state_dir / "tokens" / f"{preview['preview_token']}.json"
            token.unlink()

    def test_personal_skill_guide_uses_template_and_records_save(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            vault = self.make_personal_vault(root)
            catalog = vault.scan()
            skill = next(item for item in catalog["skills"] if item["id"] == "my/demo")
            template = skill_guide_template(skill)
            self.assertIn("## 8. 维护记录", template)
            result = save_skill_guide(vault, "my/demo", template)
            guide = root / "docs" / "skill-guides" / "my--demo.md"
            self.assertTrue(result["created"])
            self.assertEqual(guide.read_text(encoding="utf-8"), template)
            transaction = vault.state_dir / "transactions" / f"{result['transaction_id']}.json"
            self.assertEqual(load_data(transaction)["operation"], "skill.guide.save")


@unittest.skipUnless(
    INTEGRATION_ROOT,
    "set SKILLS_VAULT_TEST_ROOT to run read/write integration tests",
)
class RepositoryIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(str(INTEGRATION_ROOT)).resolve()
        cls.vault = Vault(cls.root)
        cls.catalog = cls.vault.scan()

    def test_expected_inventory(self):
        self.assertGreaterEqual(self.catalog["counts"]["skills"], 80)
        self.assertGreaterEqual(self.catalog["counts"]["published"], 40)
        ids = {entry["id"] for entry in self.catalog["skills"]}
        self.assertIn("mattpocock/grill-me", ids)
        self.assertIn("anthropic/pdf", ids)
        self.assertIn("academic/scientific-toolkit-skill", ids)
        self.assertIn("my/cloudbase", ids)

    def test_legacy_base_profile_remains_codex_and_claude_only(self):
        with patch.object(Vault, "disabled_source_ids", return_value=set()):
            for platform in ("codex", "claude"):
                entries, _ = self.vault.resolve_profile(["base", "academic"], platform)
                names = [entry["name"] for entry in entries]
                self.assertEqual(len(names), len(set(names)))
                self.assertIn("grilling", names)
                self.assertIn("scientific-toolkit-skill", names)

    def test_install_plan_is_cross_platform(self):
        with patch.object(Vault, "disabled_source_ids", return_value=set()):
            plan = install_plan(self.vault, ["base"])
        platforms = {operation["platform"] for operation in plan["operations"]}
        self.assertEqual(platforms, {"codex", "claude"})

    def test_profile_details_explain_selection_and_install_state(self):
        details = self.vault.resolve_profile_details(["base"], "codex")
        self.assertIn("mattpocock/tdd", details["status"])
        self.assertTrue(details["status"]["mattpocock/tdd"]["reasons"])
        self.assertEqual(details["status"]["mattpocock/tdd"]["reasons"][0]["type"], "profile")

    def test_conflict_compare_returns_unified_diff(self):
        result = compare_skills(self.vault, "anthropic/pdf", "academic/pdf")
        self.assertTrue(result["same_name"])
        self.assertIn("---", "\n".join(result["diff"]))

    def test_install_preview_is_tokenized(self):
        preview = install_preview(self.vault, ["base"])
        self.assertTrue(preview["preview_token"])
        token_path = self.vault.state_dir / "tokens" / f"{preview['preview_token']}.json"
        self.assertTrue(token_path.exists())
        token_path.unlink()

    def test_lint_has_no_errors(self):
        errors, _ = lint_vault(self.vault)
        matt_repo = self.root / "sources" / "mattpocock-skills"
        if git_clean(matt_repo):
            self.assertEqual(errors, [])
        else:
            self.assertIn("Source mattpocock has local changes", errors)

    def test_source_audit_is_traceable(self):
        audit = source_audit(self.vault, "mattpocock")
        self.assertEqual(audit["declared_license"], "MIT")
        self.assertTrue(audit["license_files"])


class BackupTests(unittest.TestCase):
    def test_install_retargets_a_link_managed_by_previous_vault_root(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "vault"
            state = root / ".vault"
            state.mkdir(parents=True)
            (root / "profiles").mkdir()
            write_data(root / "profiles" / "base.yaml", {"schema_version": 1, "include": []})
            old_target = base / "old-vault" / "my-skills" / "demo"
            new_target = root / "my-skills" / "demo"
            old_target.mkdir(parents=True)
            new_target.mkdir(parents=True)
            destination = base / "home" / ".agents" / "skills" / "demo"
            destination.parent.mkdir(parents=True)
            destination.symlink_to(old_target, target_is_directory=True)
            write_data(
                state / "install-state.json",
                {
                    "schema_version": 1,
                    "links": [
                        {
                            "path": str(destination),
                            "target": str(old_target),
                            "skill_id": "my/demo",
                            "platform": "codex",
                        }
                    ],
                },
            )
            plan = {
                "profiles": ["base"],
                "operations": [
                    {
                        "path": str(destination),
                        "target": str(new_target),
                        "skill_id": "my/demo",
                        "platform": "codex",
                        "name": "demo",
                    }
                ],
                "notes": [],
                "changes": {"added": [], "removed": [], "changed": [], "kept": []},
            }
            vault = Vault(root)
            with patch("skills_vault.ops.install_plan", return_value=plan):
                install(
                    vault,
                    ["base"],
                    assume_yes=True,
                    adapter=PlatformAdapter("darwin", base / "home"),
                )
            self.assertTrue(destination.is_symlink())
            self.assertEqual(destination.resolve(), new_target.resolve())
            installed = load_data(state / "install-state.json")
            self.assertEqual(installed["links"][0]["target"], str(new_target))

    def test_backup_reset_and_restore_preserves_codex_system(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            home = base / "home"
            root = base / "vault"
            (root / ".vault").mkdir(parents=True)
            for relative in (".agents/skills", ".claude/skills", ".claude/commands", ".codex/skills/.system"):
                (home / relative).mkdir(parents=True)
            (home / ".agents/skills/a").write_text("agent")
            (home / ".claude/skills/c").write_text("claude")
            (home / ".claude/commands/old.md").write_text("command")
            (home / ".codex/skills/legacy").write_text("legacy")
            (home / ".codex/skills/.system/keep").write_text("system")
            vault = Vault(root)
            with patch("pathlib.Path.home", return_value=home):
                backup = create_backup(vault)
                _reset_user_skill_dirs()
                self.assertTrue((home / ".codex/skills/.system/keep").exists())
                self.assertFalse((home / ".codex/skills/legacy").exists())
                _restore_backup_path(vault, backup)
            self.assertEqual((home / ".agents/skills/a").read_text(), "agent")
            self.assertEqual((home / ".claude/commands/old.md").read_text(), "command")
            self.assertEqual((home / ".codex/skills/legacy").read_text(), "legacy")
            self.assertEqual((home / ".codex/skills/.system/keep").read_text(), "system")

    def test_install_reconciles_vault_symlinks_when_state_is_empty(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "vault"
            home = base / "home"
            skill = root / "my-skills" / "demo"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: demo\ndescription: Demo.\n---\n\nRun demo.\n",
                encoding="utf-8",
            )
            (root / "profiles").mkdir(parents=True)
            write_data(root / "profiles" / "base.yaml", {"schema_version": 1, "include": []})
            write_data(root / "registry.yaml", {"schema_version": 1, "sources": {}})
            write_data(root / "lock.yaml", {"schema_version": 1, "sources": {}})
            write_data(root / "annotations" / "skills.yaml", {"schema_version": 1, "skills": {}})
            write_data(
                root / "catalog" / "catalog.json",
                {
                    "schema_version": 2,
                    "fingerprint": "fixture",
                    "skills": [
                        {
                            "id": "my/demo",
                            "name": "demo",
                            "path": "my-skills/demo",
                            "classification": "published",
                            "requires": [],
                            "compatibility": {"level": "both", "platforms": ["codex", "claude", "lux"]},
                        }
                    ],
                },
            )
            destination = home / ".agents" / "skills" / "demo"
            destination.parent.mkdir(parents=True)
            destination.symlink_to(skill, target_is_directory=True)
            stale_destination = home / ".agents" / "skills" / "prompt-polisher"
            stale_destination.symlink_to(root / "my-skills" / "prompt-polisher", target_is_directory=True)
            write_data(root / ".vault" / "install-state.json", {"schema_version": 2, "deployments": [], "links": []})

            vault = Vault(root)
            adapter = PlatformAdapter(system="darwin", home=home)
            install(vault, ["base"], assume_yes=True, adapter=adapter)

            self.assertFalse(destination.exists())
            self.assertFalse(stale_destination.exists())
            state = load_data(root / ".vault" / "install-state.json")
            self.assertEqual(state["deployments"], [])

    def test_restore_preview_rejects_backup_path_traversal(self):
        with tempfile.TemporaryDirectory() as directory:
            vault = Vault(Path(directory))
            with self.assertRaises(ServiceError) as caught:
                restore_preview(vault, "../outside")
            self.assertEqual(caught.exception.code, "invalid_backup")

    def test_github_ssh_https_fallback(self):
        self.assertEqual(
            _https_fallback("git@github.com:owner/repo.git"),
            "https://github.com/owner/repo.git",
        )


class DeriveTests(unittest.TestCase):
    def test_derive_records_git_baseline_and_renames_skill(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "sources" / "upstream"
            skill = repo / "skills" / "demo"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: demo\ndescription: Demo upstream skill.\n---\n\nDo the thing.\n"
            )
            git(repo, "init", "-b", "main", ".")
            git(repo, "config", "user.email", "test@example.com")
            git(repo, "config", "user.name", "Test")
            git(repo, "add", ".")
            git(repo, "commit", "-m", "initial")
            commit = git(repo, "rev-parse", "HEAD")
            (root / "annotations").mkdir()
            (root / "profiles").mkdir()
            (root / "my-skills").mkdir()
            write_data(
                root / "registry.yaml",
                {
                    "schema_version": 1,
                    "sources": {
                        "up": {
                            "url": "local:test",
                            "path": "sources/upstream",
                            "branch": "main",
                            "classify": [{"pattern": "skills/*/SKILL.md", "as": "published"}],
                        }
                    },
                },
            )
            write_data(
                root / "lock.yaml",
                {"schema_version": 1, "generated_at": "test", "sources": {"up": {"commit": commit, "branch": "main"}}},
            )
            write_data(root / "annotations" / "skills.yaml", {"schema_version": 1, "skills": {}})
            vault = Vault(root)
            vault.scan()
            destination = vault.derive("up/demo", "my-demo")
            metadata, _ = parse_frontmatter((destination / "SKILL.md").read_text())
            origin = json.loads((destination / ".vault-origin.json").read_text())
            self.assertEqual(metadata["name"], "my-demo")
            self.assertEqual(origin["base_commit"], commit)
            self.assertEqual(origin["source_skill_id"], "up/demo")


class ManagedSelectionTests(unittest.TestCase):
    def make_vault(self, root: Path) -> Vault:
        (root / "annotations").mkdir(parents=True)
        (root / "profiles").mkdir()
        (root / "catalog").mkdir()
        (root / "my-skills" / "one").mkdir(parents=True)
        (root / "my-skills" / "two").mkdir(parents=True)
        for name in ("one", "two"):
            (root / "my-skills" / name / "SKILL.md").write_text(
                f"---\nname: duplicate\ndescription: {name}\n---\n",
                encoding="utf-8",
            )
        write_data(root / "registry.yaml", {"schema_version": 1, "sources": {}})
        write_data(root / "lock.yaml", {"schema_version": 1, "sources": {}})
        write_data(root / "annotations" / "skills.yaml", {"schema_version": 1, "skills": {}})
        entries = []
        for name in ("one", "two"):
            entries.append(
                {
                    "id": f"my/{name}",
                    "name": "duplicate",
                    "path": f"my-skills/{name}",
                    "classification": "published",
                    "requires": [],
                    "compatibility": {"level": "both", "platforms": ["codex", "claude", "lux"]},
                }
            )
        write_data(
            root / "catalog" / "catalog.json",
            {
                "schema_version": 2,
                "fingerprint": "fixture",
                "generated_at": "test",
                "counts": {"skills": 2, "published": 2, "conflict_groups": 1, "duplicate_ids": 0},
                "conflicts": {"duplicate": ["my/one", "my/two"]},
                "skills": entries,
            },
        )
        return Vault(root)

    def test_same_name_selection_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            vault = self.make_vault(Path(directory))
            with self.assertRaises(ServiceError) as caught:
                save_managed_selection(vault, {"my/one": "both", "my/two": "codex"})
            self.assertEqual(caught.exception.code, "name_conflict")

    def test_ui_selection_creates_platform_profiles_and_tracks_platform_install(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            vault = self.make_vault(root)
            result = save_managed_selection(vault, {"my/one": "codex"})
            self.assertEqual(result["selections"], {"my/one": "codex"})
            self.assertEqual(vault.active_profiles(), ["ui-shared", "ui-codex", "ui-claude", "ui-lux"])
            install(
                vault,
                vault.active_profiles(),
                assume_yes=True,
                adapter=PlatformAdapter("windows", root / "home"),
            )
            codex = vault.resolve_profile_details(vault.active_profiles(), "codex")
            claude = vault.resolve_profile_details(vault.active_profiles(), "claude")
            self.assertTrue(codex["status"]["my/one"]["installed"])
            self.assertNotIn("my/one", claude["status"])

    def test_legacy_both_mode_does_not_enable_lux(self):
        with tempfile.TemporaryDirectory() as directory:
            vault = self.make_vault(Path(directory))
            result = save_managed_selection(vault, {"my/one": "both"})
            self.assertEqual(result["selections"], {"my/one": "both"})
            self.assertEqual(result["resolved"]["lux"]["direct"], [])

    def test_three_platform_combinations_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            vault = self.make_vault(Path(directory))
            for mode in ("all", "codex-lux", "claude-lux", "lux"):
                result = save_managed_selection(vault, {"my/one": mode})
                self.assertEqual(result["selections"], {"my/one": mode})

    def test_install_preview_expires_when_skill_content_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "vault"
            home = Path(directory) / "home"
            vault = self.make_vault(root)
            save_managed_selection(vault, {"my/one": "all"})
            with patch("pathlib.Path.home", return_value=home):
                preview = install_preview(vault, vault.active_profiles())
                skill_md = root / "my-skills" / "one" / "SKILL.md"
                skill_md.write_text(skill_md.read_text(encoding="utf-8") + "\nChanged.\n", encoding="utf-8")
                with self.assertRaises(ServiceError) as caught:
                    install_apply(vault, preview["preview_token"])
            self.assertEqual(caught.exception.code, "stale_preview")

    def test_ui_install_always_creates_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "vault"
            home = Path(directory) / "home"
            vault = self.make_vault(root)
            save_managed_selection(vault, {"my/one": "all"})
            with patch("pathlib.Path.home", return_value=home):
                preview = install_preview(vault, vault.active_profiles())
                result = install_apply(vault, preview["preview_token"])
            self.assertTrue((vault.state_dir / "backups" / result["backup_id"] / "manifest.json").exists())
            state = json.loads((vault.state_dir / "install-state.json").read_text())
            self.assertEqual({item["platform"] for item in state["links"]}, {"codex", "claude", "lux"})
            lux_md = home / ".lux" / "skills" / "duplicate.md"
            self.assertTrue(lux_md.is_file())
            self.assertTrue((home / ".lux" / "skills" / "duplicate" / "SKILL.md").is_file())
            self.assertEqual(vault.resolve_profile_details(vault.active_profiles(), "lux")["status"]["my/one"]["state"], "installed")
            lux_md.unlink()
            self.assertEqual(vault.resolve_profile_details(vault.active_profiles(), "lux")["status"]["my/one"]["state"], "drifted")


class SkillDeletionTests(unittest.TestCase):
    def make_vault(self, root: Path) -> Vault:
        (root / "annotations").mkdir(parents=True)
        (root / "profiles").mkdir()
        (root / "catalog").mkdir()
        skill = root / "my-skills" / "demo"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("---\nname: demo\ndescription: Demo.\n---\n\nDo it.\n")
        guide = root / "docs" / "skill-guides"
        guide.mkdir(parents=True)
        (guide / "my--demo.md").write_text("# demo\n")
        write_data(root / "registry.yaml", {"schema_version": 1, "sources": {}})
        write_data(root / "lock.yaml", {"schema_version": 1, "sources": {}})
        write_data(
            root / "annotations" / "skills.yaml",
            {
                "schema_version": 1,
                "skills": {
                    "my/demo": {"summary_zh": "示例"},
                    "my/keeper": {"recommends": ["my/demo"]},
                },
            },
        )
        write_data(root / "profiles" / "base.yaml", {"schema_version": 1, "include": ["my/demo"]})
        write_data(root / ".vault" / "active-profiles.json", {"schema_version": 1, "profiles": ["base"]})
        vault = Vault(root)
        vault.scan()
        return vault

    def test_personal_skill_delete_removes_all_managed_references(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "vault"
            home = Path(directory) / "home"
            vault = self.make_vault(root)
            managed = home / ".agents" / "skills" / "demo"
            managed.parent.mkdir(parents=True)
            managed.symlink_to(root / "my-skills" / "demo", target_is_directory=True)
            write_data(
                vault.state_dir / "install-state.json",
                {"schema_version": 1, "links": [{"path": str(managed), "target": str(root / "my-skills" / "demo"), "skill_id": "my/demo", "platform": "codex"}]},
            )
            preview = delete_skills_preview(vault, ["my/demo"])
            self.assertEqual(preview["counts"]["skills"], 1)
            self.assertEqual(preview["counts"]["links"], 1)
            with patch("pathlib.Path.home", return_value=home):
                result = delete_skills_apply(vault, preview["preview_token"])
            self.assertEqual(result["deleted"], ["my/demo"])
            self.assertFalse((root / "my-skills" / "demo").exists())
            self.assertFalse((root / "docs" / "skill-guides" / "my--demo.md").exists())
            self.assertFalse(managed.exists())
            self.assertNotIn("my/demo", load_data(root / "annotations" / "skills.yaml")["skills"])
            self.assertEqual(load_data(root / "annotations" / "skills.yaml")["skills"]["my/keeper"]["recommends"], [])
            self.assertEqual(load_data(root / "profiles" / "base.yaml")["include"], [])
            self.assertNotIn("my/demo", {entry["id"] for entry in vault.catalog()["skills"]})
            self.assertTrue(Path(result["archive"], "manifest.json").exists())

    def test_batch_preview_rejects_unknown_skill(self):
        with tempfile.TemporaryDirectory() as directory:
            vault = self.make_vault(Path(directory) / "vault")
            with self.assertRaises(ServiceError) as caught:
                delete_skills_preview(vault, ["my/demo", "my/missing"])
            self.assertEqual(caught.exception.code, "not_found")

    def test_upstream_skill_delete_uses_tombstone_and_keeps_git_clean(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "vault"
            home = Path(directory) / "home"
            repo = root / "sources" / "upstream"
            skill = repo / "skills" / "demo"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("---\nname: demo\ndescription: Demo upstream.\n---\n")
            git(repo, "init", "-b", "main", ".")
            git(repo, "config", "user.email", "test@example.com")
            git(repo, "config", "user.name", "Test")
            git(repo, "add", ".")
            git(repo, "commit", "-m", "initial")
            (root / "annotations").mkdir()
            (root / "profiles").mkdir()
            write_data(
                root / "registry.yaml",
                {"schema_version": 1, "sources": {"up": {"url": "local:test", "path": "sources/upstream", "branch": "main", "classify": [{"pattern": "skills/*/SKILL.md", "as": "published"}]}}},
            )
            write_data(root / "lock.yaml", {"schema_version": 1, "sources": {}})
            write_data(root / "annotations" / "skills.yaml", {"schema_version": 1, "skills": {}})
            write_data(root / "profiles" / "base.yaml", {"schema_version": 1, "include": ["up/demo"]})
            vault = Vault(root)
            vault.scan()
            preview = delete_skills_preview(vault, ["up/demo"])
            self.assertEqual(preview["items"][0]["source_action"], "hide-upstream-skill")
            with patch("pathlib.Path.home", return_value=home):
                delete_skills_apply(vault, preview["preview_token"])
            self.assertTrue(skill.exists())
            self.assertTrue(git_clean(repo))
            self.assertIn("up/demo", load_data(vault.deleted_skills_path)["skills"])
            self.assertNotIn("up/demo", {entry["id"] for entry in vault.catalog()["skills"]})


class SourcePolicyTests(unittest.TestCase):
    def make_vault(self, root: Path) -> Vault:
        repo = root / "sources" / "upstream"
        skill = repo / "skills" / "demo"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\nname: demo\ndescription: Demo upstream skill.\n---\n\nDo it.\n"
        )
        git(repo, "init", "-b", "main", ".")
        git(repo, "config", "user.email", "test@example.com")
        git(repo, "config", "user.name", "Test")
        git(repo, "add", ".")
        git(repo, "commit", "-m", "initial")
        (root / "annotations").mkdir()
        (root / "profiles").mkdir()
        write_data(
            root / "registry.yaml",
            {
                "schema_version": 1,
                "sources": {
                    "up": {
                        "url": "local:test",
                        "path": "sources/upstream",
                        "branch": "main",
                        "classify": [{"pattern": "skills/*/SKILL.md", "as": "published"}],
                    }
                },
            },
        )
        write_data(root / "lock.yaml", {"schema_version": 1, "sources": {}})
        write_data(root / "annotations" / "skills.yaml", {"schema_version": 1, "skills": {}})
        write_data(root / "profiles" / "ui-shared.yaml", {"schema_version": 1, "include": ["up/demo"]})
        write_data(root / "profiles" / "ui-codex.yaml", {"schema_version": 1, "platform": "codex", "include": []})
        write_data(root / "profiles" / "ui-claude.yaml", {"schema_version": 1, "platform": "claude", "include": []})
        write_data(
            root / ".vault" / "active-profiles.json",
            {"schema_version": 1, "profiles": ["ui-shared", "ui-codex", "ui-claude"]},
        )
        vault = Vault(root)
        vault.scan()
        return vault

    def test_source_switch_disables_links_and_preserves_profile_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "vault"
            home = Path(directory) / "home"
            vault = self.make_vault(root)
            links = []
            for platform, relative in (("codex", ".agents/skills"), ("claude", ".claude/skills")):
                link = home / relative / "demo"
                link.parent.mkdir(parents=True)
                link.symlink_to(root / "sources" / "upstream" / "skills" / "demo", target_is_directory=True)
                links.append({"path": str(link), "target": str(link.resolve()), "skill_id": "up/demo", "platform": platform})
            write_data(vault.state_dir / "install-state.json", {"schema_version": 1, "links": links})

            preview = source_policy_preview(vault, "up", False)
            self.assertEqual(preview["skill_count"], 1)
            self.assertEqual(len(preview["installed_links"]), 2)
            with patch("pathlib.Path.home", return_value=home):
                result = source_policy_apply(vault, preview["preview_token"])

            self.assertFalse(result["enabled"])
            self.assertFalse(vault.source_rows()[0]["enabled"])
            self.assertEqual(vault.resolve_profile(vault.active_profiles(), "codex")[0], [])
            self.assertEqual(managed_selection_payload(vault)["selections"], {"up/demo": "both"})
            self.assertTrue((root / "sources" / "upstream" / "skills" / "demo" / "SKILL.md").exists())
            self.assertFalse((home / ".agents" / "skills" / "demo").exists())
            self.assertFalse((home / ".claude" / "skills" / "demo").exists())

            enable = source_policy_preview(vault, "up", True)
            with patch("pathlib.Path.home", return_value=home):
                source_policy_apply(vault, enable["preview_token"])
            self.assertTrue(vault.source_rows()[0]["enabled"])
            self.assertTrue((home / ".agents" / "skills" / "demo" / "SKILL.md").is_file())
            self.assertTrue((home / ".claude" / "skills" / "demo" / "SKILL.md").is_file())

    def test_personal_source_cannot_use_repository_switch(self):
        with tempfile.TemporaryDirectory() as directory:
            vault = self.make_vault(Path(directory) / "vault")
            with self.assertRaises(ServiceError) as caught:
                source_policy_preview(vault, "my", False)
            self.assertEqual(caught.exception.code, "personal_source")


class SkillsCliSourceTests(unittest.TestCase):
    def make_vault(self, root: Path) -> Vault:
        (root / "annotations").mkdir(parents=True)
        (root / "profiles").mkdir()
        (root / "my-skills").mkdir()
        write_data(root / "registry.yaml", {"schema_version": 1, "sources": {}})
        write_data(root / "lock.yaml", {"schema_version": 1, "sources": {}})
        write_data(root / "annotations" / "skills.yaml", {"schema_version": 1, "skills": {}})
        vault = Vault(root)
        vault.scan()
        return vault

    def test_preview_and_apply_registers_self_managed_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "vault"
            vault = self.make_vault(root)
            with patch(
                "skills_vault.services.discover_skills_cli_source",
                return_value={"skills": ["demo", "other"], "output": "Found 2 skills"},
            ):
                preview = skills_cli_source_preview(
                    vault,
                    "demo-site",
                    "https://example.com/skills/",
                    True,
                    ["demo"],
                )

            self.assertEqual(preview["available_skills"], ["demo", "other"])
            self.assertEqual(preview["skills"], ["demo"])

            def fake_install(url: str, destination: Path, full_depth: bool, selected_skills):
                self.assertEqual(selected_skills, ["demo"])
                skill = destination / ".agents" / "skills" / "demo"
                skill.mkdir(parents=True)
                (skill / "SKILL.md").write_text(
                    "---\nname: demo\ndescription: External demo.\n---\n",
                    encoding="utf-8",
                )
                write_data(
                    destination / "skills-lock.json",
                    {"version": 1, "skills": {"demo": {"sourceUrl": url}}},
                )
                return {"skills": ["demo"], "output": "installed"}

            with patch("skills_vault.services.install_skills_cli_source", side_effect=fake_install):
                result = skills_cli_source_apply(vault, preview["preview_token"])

            source = vault.registry["sources"]["demo-site"]
            self.assertEqual(source["kind"], "skills-cli")
            self.assertEqual(source["update_policy"], "self-managed")
            self.assertEqual(result["skills"], ["demo-site/demo"])
            row = vault.source_rows()[0]
            self.assertEqual(row["kind"], "skills-cli")
            self.assertFalse(row["dirty"])
            self.assertIsNone(row["locked"])
            self.assertEqual(vault.catalog()["skills"][0]["source_kind"], "skills-cli")
            self.assertEqual(source_audit(vault, "demo-site")["self_managed"], True)
            plan = update_plan(vault)
            self.assertEqual(plan[0]["status"], "self-managed")
            with patch(
                "skills_vault.ops.update_skills_cli_source",
                return_value={"before": ["demo"], "after": ["demo"], "output": "up to date"},
            ):
                self.assertTrue(apply_updates(vault, plan, assume_yes=True))
            errors, _ = lint_vault(vault)
            self.assertEqual(errors, [])

    def test_discovery_parser_handles_skills_cli_tree_output(self):
        output = """\
│
◇  Found 2 skills
│
◇  Available Skills
│
│    ai-image-generation
│
│      Generate and edit images.
│
│    runcomfy-cli
│
│      Run any model.
"""
        self.assertEqual(
            skills_cli._parse_skill_names(output),
            ["ai-image-generation", "runcomfy-cli"],
        )

    def test_npx_resolver_finds_nvm_install_without_shell_path(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            node_bin = home / ".nvm" / "versions" / "node" / "v22.20.0" / "bin"
            node_bin.mkdir(parents=True)
            npx = node_bin / "npx"
            node = node_bin / "node"
            npx.write_text("#!/bin/sh\n", encoding="utf-8")
            node.write_text("#!/bin/sh\n", encoding="utf-8")
            npx.chmod(0o755)
            node.chmod(0o755)
            with patch("skills_vault.skills_cli._home_directory", return_value=home), patch(
                "skills_vault.executable_resolver.shutil.which", return_value=None
            ), patch.dict(
                os.environ,
                {"PATH": "/usr/bin:/bin", "NVM_BIN": "", "SKILLS_VAULT_NPX": ""},
                clear=False,
            ):
                command = skills_cli._command("add", "https://example.com", "--list")
                environment = skills_cli._environment()
            self.assertEqual(command[0], str(npx))
            self.assertEqual(environment["PATH"].split(os.pathsep)[0], str(node_bin))

    def test_cli_retries_transient_github_tls_failure(self):
        completed = type("Completed", (), {"stdout": "ok", "stderr": ""})()
        with patch(
            "skills_vault.skills_cli.run",
            side_effect=[VaultError("LibreSSL SSL_connect: SSL_ERROR_SYSCALL"), completed],
        ) as mocked_run, patch("skills_vault.skills_cli.time.sleep"):
            result = skills_cli._run_cli(["npx", "skills"], Path("/tmp"), 30)
        self.assertIs(result, completed)
        self.assertEqual(mocked_run.call_count, 2)

    def test_preview_rejects_unknown_requested_skill(self):
        with tempfile.TemporaryDirectory() as directory:
            vault = self.make_vault(Path(directory) / "vault")
            with patch(
                "skills_vault.services.discover_skills_cli_source",
                return_value={"skills": ["available"], "output": "Found 1 skills"},
            ), self.assertRaises(ServiceError) as caught:
                skills_cli_source_preview(
                    vault,
                    "demo-site",
                    "https://example.com/skills/",
                    False,
                    ["missing"],
                )
            self.assertEqual(caught.exception.code, "unknown_skill")

    def test_preview_generates_source_id_from_url(self):
        with tempfile.TemporaryDirectory() as directory:
            vault = self.make_vault(Path(directory) / "vault")
            with patch(
                "skills_vault.services.resolve_executable",
                return_value=ResolvedExecutable("npx", Path("/usr/bin/npx"), "PATH"),
            ), patch(
                "skills_vault.services.discover_skills_cli_source",
                return_value={"skills": ["demo"], "output": "Found 1 skills"},
            ):
                preview = skills_cli_source_preview(
                    vault,
                    None,
                    "https://github.com/owner/repo",
                )
            self.assertEqual(preview["source_id"], "owner-repo")
            self.assertEqual(preview["input_kind"], "reference")

    def test_preview_accepts_complete_skills_cli_command(self):
        with tempfile.TemporaryDirectory() as directory:
            vault = self.make_vault(Path(directory) / "vault")
            with patch(
                "skills_vault.services.resolve_executable",
                return_value=ResolvedExecutable("npx", Path("/usr/bin/npx"), "PATH"),
            ), patch(
                "skills_vault.services.discover_skills_cli_source",
                return_value={"skills": ["demo"], "output": "Found 1 skills"},
            ) as discover:
                preview = skills_cli_source_preview(
                    vault,
                    None,
                    "npx skills add owner/repo --skill demo",
                )
            discover.assert_called_once_with("owner/repo", False)
            self.assertEqual(preview["source_id"], "owner-repo")
            self.assertEqual(preview["skills"], ["demo"])

    def test_preview_merges_a_new_skill_into_an_existing_repository_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "vault"
            vault = self.make_vault(root)
            destination = root / "sources" / "skills-cli" / "skills-101-superpowers"
            installed = destination / ".agents" / "skills" / "twitter-automation"
            installed.mkdir(parents=True)
            (installed / "SKILL.md").write_text(
                "---\nname: twitter-automation\ndescription: Existing.\n---\n",
                encoding="utf-8",
            )
            write_data(destination / "skills-lock.json", {"version": 1})
            registry = vault.registry
            registry["sources"]["skills-101-superpowers"] = {
                "kind": "skills-cli",
                "url": "https://github.com/skills-101/superpowers",
                "path": "sources/skills-cli/skills-101-superpowers",
                "skill_root": ".agents/skills",
                "update_policy": "self-managed",
                "selected_skills": ["twitter-automation"],
            }
            write_data(vault.registry_path, registry)
            with patch(
                "skills_vault.services.resolve_executable",
                return_value=ResolvedExecutable("npx", Path("/usr/bin/npx"), "PATH"),
            ), patch(
                "skills_vault.services.discover_skills_cli_source",
                return_value={
                    "skills": ["twitter-automation", "ai-image-generation"],
                    "output": "Found 2 skills",
                },
            ):
                preview = skills_cli_source_preview(
                    vault,
                    None,
                    "npx skills add https://github.com/skills-101/superpowers --skill ai-image-generation",
                )
            self.assertEqual(preview["action"], "merge")
            self.assertEqual(preview["source_id"], "skills-101-superpowers")
            self.assertEqual(preview["skills_to_add"], ["ai-image-generation"])
            self.assertEqual(preview["skills_already_present"], [])

    def test_apply_merges_a_new_skill_without_replacing_existing_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "vault"
            vault = self.make_vault(root)
            destination = root / "sources" / "skills-cli" / "skills-101-superpowers"
            installed = destination / ".agents" / "skills" / "twitter-automation"
            installed.mkdir(parents=True)
            (installed / "SKILL.md").write_text(
                "---\nname: twitter-automation\ndescription: Existing.\n---\n",
                encoding="utf-8",
            )
            write_data(destination / "skills-lock.json", {"version": 1})
            registry = vault.registry
            registry["sources"]["skills-101-superpowers"] = {
                "kind": "skills-cli",
                "url": "https://github.com/skills-101/superpowers",
                "path": "sources/skills-cli/skills-101-superpowers",
                "skill_root": ".agents/skills",
                "update_policy": "self-managed",
                "selected_skills": ["twitter-automation"],
            }
            write_data(vault.registry_path, registry)
            with patch(
                "skills_vault.services.resolve_executable",
                return_value=ResolvedExecutable("npx", Path("/usr/bin/npx"), "PATH"),
            ), patch(
                "skills_vault.services.discover_skills_cli_source",
                return_value={"skills": ["twitter-automation", "ai-image-generation"], "output": "Found 2 skills"},
            ):
                preview = skills_cli_source_preview(
                    vault,
                    None,
                    "npx skills add https://github.com/skills-101/superpowers --skill ai-image-generation",
                )

            def fake_append(url: str, workdir: Path, skills, full_depth: bool):
                added = workdir / ".agents" / "skills" / "ai-image-generation"
                added.mkdir(parents=True)
                (added / "SKILL.md").write_text(
                    "---\nname: ai-image-generation\ndescription: Added.\n---\n",
                    encoding="utf-8",
                )
                return {"before": ["twitter-automation"], "after": ["twitter-automation", "ai-image-generation"], "output": "added"}

            with patch("skills_vault.services.add_skills_cli_source", side_effect=fake_append), patch(
                "skills_vault.services.resolve_executable",
                return_value=ResolvedExecutable("npx", Path("/usr/bin/npx"), "PATH"),
            ):
                result = skills_cli_source_apply(vault, preview["preview_token"])

            self.assertEqual(result["action"], "merge")
            self.assertTrue((installed / "SKILL.md").exists())
            self.assertTrue((destination / ".agents" / "skills" / "ai-image-generation" / "SKILL.md").exists())
            self.assertEqual(
                vault.registry["sources"]["skills-101-superpowers"]["selected_skills"],
                ["twitter-automation", "ai-image-generation"],
            )

    def test_external_source_rejects_localhost(self):
        with tempfile.TemporaryDirectory() as directory:
            vault = self.make_vault(Path(directory) / "vault")
            with self.assertRaises(ServiceError) as caught:
                skills_cli_source_preview(vault, "local", "http://127.0.0.1:8080/", False)
            self.assertEqual(caught.exception.code, "invalid_source_url")


class GitSourceServiceTests(unittest.TestCase):
    def make_vault(self, root: Path) -> Vault:
        (root / "annotations").mkdir(parents=True)
        (root / "profiles").mkdir()
        (root / "my-skills").mkdir()
        write_data(root / "registry.yaml", {"schema_version": 1, "sources": {}})
        write_data(root / "lock.yaml", {"schema_version": 1, "sources": {}})
        write_data(root / "annotations" / "skills.yaml", {"schema_version": 1, "skills": {}})
        vault = Vault(root)
        vault.scan()
        return vault

    def test_git_source_preview_and_apply_registers_strict_source(self):
        from skills_vault.services import git_source_apply, git_source_preview

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "vault"
            vault = self.make_vault(root)
            fake_skills = [{"name": "demo", "path": "skills/demo/SKILL.md", "description": "demo"}]
            with patch(
                "skills_vault.services._clone_and_list_skills",
                return_value={"skills": fake_skills, "commit": "abc123", "branch": "main"},
            ) as mocked_clone:
                preview = git_source_preview(vault, "git-demo", "https://github.com/example/skills.git", "main")
                mocked_clone.assert_called_once_with("https://github.com/example/skills.git")

            self.assertEqual(preview["kind"], "git")
            self.assertEqual(preview["skills"], fake_skills)
            self.assertEqual(preview["update_policy"], "strict")

            def fake_clone(command, **kwargs):
                # simulate `git clone` creating a real git repo with a SKILL.md
                destination = Path(command[-1])
                skill_dir = destination / "skills" / "demo"
                skill_dir.mkdir(parents=True)
                (skill_dir / "SKILL.md").write_text("---\nname: demo\ndescription: External demo.\n---\n", encoding="utf-8")
                git(destination, "init", check=False)
                git(destination, "config", "user.email", "test@example.com", check=False)
                git(destination, "config", "user.name", "test", check=False)
                git(destination, "add", "-A")
                git(destination, "commit", "-m", "init", check=False)
                completed = type("Completed", (), {"stdout": "", "stderr": ""})()
                return completed

            with patch("skills_vault.services.run", side_effect=fake_clone):
                result = git_source_apply(vault, preview["preview_token"])

            source = vault.registry["sources"]["git-demo"]
            self.assertEqual(source["kind"], "git")
            self.assertEqual(source["update_policy"], "strict")
            self.assertEqual(source["trust"], "unreviewed")
            self.assertEqual(result["source_id"], "git-demo")
            self.assertEqual(result["update_policy"], "strict")

    def test_git_source_rejects_ssh_localhost(self):
        from skills_vault.services import git_source_preview

        with tempfile.TemporaryDirectory() as directory:
            vault = self.make_vault(Path(directory) / "vault")
            with self.assertRaises(ServiceError) as caught:
                git_source_preview(vault, "local", "git@localhost:org/skills.git")
            self.assertEqual(caught.exception.code, "invalid_source_url")

    def test_source_review_updates_trust_license_and_timestamp(self):
        from skills_vault.services import source_review

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "vault"
            vault = self.make_vault(root)
            registry = vault.registry
            registry["sources"]["demo"] = {
                "kind": "git",
                "url": "https://github.com/example/skills.git",
                "path": "sources/demo",
                "branch": "main",
                "track": "branch",
                "trust": "unreviewed",
                "license": "unknown",
                "reviewed_at": None,
                "classify": [{"pattern": "**/SKILL.md", "as": "unknown"}],
            }
            write_data(vault.registry_path, registry)
            result = source_review(vault, "demo", trust="reviewed", license="MIT")
            self.assertEqual(result["trust"], "reviewed")
            self.assertEqual(result["license"], "MIT")
            self.assertIsNotNone(result["reviewed_at"])
            stored = vault.registry["sources"]["demo"]
            self.assertEqual(stored["trust"], "reviewed")
            self.assertEqual(stored["license"], "MIT")
            self.assertEqual(stored["reviewed_at"], result["reviewed_at"])
            with self.assertRaises(ServiceError) as caught:
                source_review(vault, "demo", trust="bogus")
            self.assertEqual(caught.exception.code, "invalid_trust")


class SourceDeletionTests(unittest.TestCase):
    def make_vault(self, root: Path) -> tuple[Vault, Path]:
        (root / "annotations").mkdir(parents=True)
        (root / "profiles").mkdir()
        (root / "my-skills").mkdir()
        source = root / "sources" / "skills-cli" / "empty-source"
        (source / ".agents" / "skills").mkdir(parents=True)
        write_data(source / "skills-lock.json", {"version": 1, "skills": {}})
        write_data(
            root / "registry.yaml",
            {
                "schema_version": 1,
                "sources": {
                    "empty-source": {
                        "kind": "skills-cli",
                        "url": "https://example.com/skills",
                        "path": "sources/skills-cli/empty-source",
                        "skill_root": ".agents/skills",
                        "update_policy": "self-managed",
                        "classify": [{"pattern": "*/SKILL.md", "as": "published"}],
                    }
                },
            },
        )
        write_data(
            root / "lock.yaml",
            {"schema_version": 1, "sources": {"empty-source": {"kind": "skills-cli", "revision": "old"}}},
        )
        write_data(root / "annotations" / "skills.yaml", {"schema_version": 1, "skills": {}})
        write_data(
            root / "profiles" / "base.yaml",
            {"schema_version": 1, "name": "base", "include_source": ["empty-source"], "include": []},
        )
        vault = Vault(root)
        write_data(
            vault.source_policies_path,
            {"schema_version": 1, "sources": {"empty-source": {"enabled": False}}},
        )
        write_data(
            vault.deleted_skills_path,
            {
                "schema_version": 1,
                "skills": {"empty-source/old-skill": {"source_id": "empty-source"}},
            },
        )
        vault.scan()
        return vault, source

    def test_deletes_zero_skill_source_and_residual_state(self):
        with tempfile.TemporaryDirectory() as directory:
            vault, source = self.make_vault(Path(directory) / "vault")
            preview = source_delete_preview(vault, "empty-source")
            self.assertEqual(preview["counts"]["skills"], 0)
            self.assertEqual(preview["counts"]["tombstones"], 1)

            result = source_delete_apply(vault, preview["preview_token"])

            self.assertNotIn("empty-source", vault.registry["sources"])
            self.assertNotIn("empty-source", load_data(vault.lock_path)["sources"])
            self.assertNotIn("empty-source", vault.source_policies().get("sources", {}))
            self.assertNotIn("empty-source/old-skill", load_data(vault.deleted_skills_path)["skills"])
            self.assertNotIn("empty-source", load_data(vault.profile_files()["base"])["include_source"])
            self.assertFalse(source.exists())
            self.assertTrue((Path(result["archive"]) / "source" / "skills-lock.json").is_file())
            self.assertEqual(vault.source_rows(), [])

    def test_source_delete_rolls_back_when_catalog_refresh_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            vault, source = self.make_vault(Path(directory) / "vault")
            preview = source_delete_preview(vault, "empty-source")
            with patch.object(vault, "scan", side_effect=VaultError("catalog failed")), self.assertRaises(
                ServiceError
            ) as caught:
                source_delete_apply(vault, preview["preview_token"])
            self.assertEqual(caught.exception.code, "source_delete_failed")
            self.assertTrue(source.is_dir())
            self.assertIn("empty-source", vault.registry["sources"])
            self.assertIn("empty-source", load_data(vault.lock_path)["sources"])


if __name__ == "__main__":
    unittest.main()
