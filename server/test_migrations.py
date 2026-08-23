import tempfile
import unittest
from pathlib import Path

from skills_vault.core import Vault, load_data, write_data
from skills_vault.migrations import (
    apply_import,
    apply_web_v2_migration,
    create_vault,
    import_plan,
    inspect_candidate,
    vault_create_plan,
    web_v2_migration_plan,
)
from skills_vault.services import create_original_apply, create_original_preview


def write_skill(path: Path, name: str, description: str = "Demo skill.") -> None:
    path.mkdir(parents=True)
    (path / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n\nDo it.\n",
        encoding="utf-8",
    )


class VaultInitializationTests(unittest.TestCase):
    def test_create_empty_vault_without_git(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "新 Vault"
            plan = vault_create_plan(destination)
            self.assertTrue(plan["will_create_directory"])
            vault = create_vault(destination)
            self.assertEqual(load_data(destination / "vault.json")["schema_version"], 1)
            self.assertEqual(vault.catalog()["counts"]["skills"], 0)
            self.assertFalse((destination / ".git").exists())
            self.assertEqual(inspect_candidate(destination)["kind"], "vault")

    def test_original_skill_creation_uses_one_time_preview(self):
        with tempfile.TemporaryDirectory() as directory:
            vault = create_vault(Path(directory) / "vault")
            preview = create_original_preview(vault, "my-demo", "Demo description.")
            self.assertEqual(preview["files"], ["SKILL.md"])
            result = create_original_apply(vault, preview["preview_token"])
            self.assertEqual(result["skill_id"], "my/my-demo")
            with self.assertRaises(Exception):
                create_original_apply(vault, preview["preview_token"])


class CandidateImportTests(unittest.TestCase):
    def test_personal_import_copies_selected_skills_and_preserves_source(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "旧 Skills"
            write_skill(source / "alpha", "alpha")
            write_skill(source / "beta", "beta")
            vault = create_vault(base / "vault")
            candidate = inspect_candidate(source)
            self.assertEqual(candidate["kind"], "skills-folder")

            plan = import_plan(vault, source, "personal", skill_names=["alpha"])
            result = apply_import(vault, plan)

            self.assertEqual(result["skills"], ["my/alpha"])
            self.assertTrue((vault.root / "my-skills" / "alpha" / "SKILL.md").is_file())
            self.assertTrue((source / "alpha" / "SKILL.md").is_file())

    def test_source_import_registers_non_git_folder_as_local_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "community"
            write_skill(source / "skills" / "demo", "demo")
            vault = create_vault(base / "vault")

            plan = import_plan(vault, source, "source", source_id="community")
            apply_import(vault, plan)

            registered = vault.registry["sources"]["community"]
            self.assertEqual(registered["kind"], "local-copy")
            self.assertEqual(vault.catalog()["skills"][0]["id"], "community/demo")
            self.assertTrue((source / "skills" / "demo" / "SKILL.md").is_file())


class WebV2MigrationTests(unittest.TestCase):
    def make_web_vault(self, root: Path) -> Vault:
        vault = create_vault(root)
        (root / "vault.json").unlink()
        write_skill(root / "my-skills" / "personal", "personal")
        write_data(root / ".vault" / "tokens" / "old.json", {"token": "secret"})
        write_data(root / ".vault" / "run" / "pid.json", {"pid": 1})
        write_data(root / ".vault" / "transactions" / "old.json", {"operation": "old"})
        write_data(root / ".vault" / "install-state.json", {"links": [{"path": "old"}]})
        vault.scan()
        return vault

    def test_web_v2_migration_copies_facts_and_archives_history(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "web-v2"
            self.make_web_vault(source)
            destination = base / "desktop-vault"

            plan = web_v2_migration_plan(source, destination)
            result = apply_web_v2_migration(plan)

            self.assertTrue(result["personal_fingerprints_match"])
            self.assertTrue((destination / "my-skills" / "personal" / "SKILL.md").is_file())
            self.assertFalse((destination / ".vault" / "tokens").exists())
            self.assertFalse((destination / ".vault" / "run").exists())
            self.assertFalse((destination / ".vault" / "install-state.json").exists())
            self.assertTrue(list((destination / ".vault" / "legacy").rglob("old.json")))
            self.assertTrue((source / ".vault" / "tokens" / "old.json").is_file())


if __name__ == "__main__":
    unittest.main()
