import tempfile
import unittest
from pathlib import Path

from skills_vault.desktop_state import DesktopState, DesktopStateError
from skills_vault.migrations import create_vault


SKILL = """---
name: {name}
description: Imported skill.
---
"""


class DesktopStateTests(unittest.TestCase):
    def test_starts_in_onboarding_and_can_create_vault(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = DesktopState(root / "config", root / "Documents" / "Skills Vault")
            self.assertEqual(state.status()["mode"], "onboarding")

            preview = state.preview("create")
            result = state.apply(preview["preview_token"])

            self.assertEqual(result["status"], "complete")
            self.assertEqual(state.status()["mode"], "ready")
            self.assertTrue(Path(result["active_vault"], "vault.json").is_file())

    def test_open_rejects_web_v2_and_accepts_current_vault(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = DesktopState(root / "config", root / "default")
            current = create_vault(root / "current")
            web_v2 = root / "web-v2"
            create_vault(web_v2)
            (web_v2 / "vault.json").unlink()

            with self.assertRaises(DesktopStateError) as raised:
                state.preview("open", str(web_v2))
            self.assertEqual(raised.exception.code, "migration_required")

            result = state.apply(state.preview("open", str(current.root))["preview_token"])
            self.assertEqual(result["active_vault"], str(current.root))

    def test_import_creates_new_vault_and_keeps_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "old-skills" / "hello"
            source.mkdir(parents=True)
            (source / "SKILL.md").write_text(SKILL.format(name="hello"), encoding="utf-8")
            destination = root / "new-vault"
            state = DesktopState(root / "config", root / "default")

            preview = state.preview("import", str(source.parent), str(destination))
            result = state.apply(preview["preview_token"])

            self.assertEqual(result["imported_skills"], ["my/hello"])
            self.assertTrue((destination / "my-skills" / "hello" / "SKILL.md").is_file())
            self.assertTrue((source / "SKILL.md").is_file())


if __name__ == "__main__":
    unittest.main()
