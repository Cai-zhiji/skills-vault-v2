import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from skills_vault.dependencies import dependency_status
from skills_vault.executable_resolver import resolve_executable
from skills_vault.platform_adapter import PlatformAdapter


class ExecutableResolverTests(unittest.TestCase):
    def test_resolves_nvm_toolchain_when_gui_path_is_minimal(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            node_bin = home / ".nvm" / "versions" / "node" / "v22.20.0" / "bin"
            node_bin.mkdir(parents=True)
            for name in ("node", "npm", "npx"):
                executable = node_bin / name
                executable.write_text("#!/bin/sh\n", encoding="utf-8")
                executable.chmod(0o755)
            adapter = PlatformAdapter("darwin", home, "arm64")
            with patch.dict(os.environ, {"PATH": "/usr/bin:/bin"}, clear=False), patch(
                "skills_vault.executable_resolver.shutil.which", return_value=None
            ):
                resolved = resolve_executable("npx", adapter)
            self.assertIsNotNone(resolved)
            self.assertEqual(resolved.path, node_bin / "npx")
            self.assertEqual(resolved.source, "nvm")

    def test_dependency_status_uses_resolver_outside_path(self):
        adapter = PlatformAdapter("darwin", Path("/Users/test"), "arm64")
        npx = Path("/Users/test/.nvm/versions/node/v22.20.0/bin/npx")
        with patch("skills_vault.dependencies.current_platform", return_value=adapter), patch(
            "skills_vault.dependencies.resolve_executable",
            side_effect=lambda name, _adapter: type(
                "Resolved", (), {"path": npx, "source": "nvm"}
            )()
            if name in ("node", "npm", "npx")
            else None,
        ), patch("skills_vault.dependencies._version", return_value="v22.20.0"):
            result = dependency_status()
        rows = {row["id"]: row for row in result["dependencies"]}
        self.assertEqual(rows["npx"]["status"], "available")
        self.assertEqual(rows["npx"]["resolution_source"], "nvm")


if __name__ == "__main__":
    unittest.main()
