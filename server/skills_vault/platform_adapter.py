from __future__ import annotations

import os
import platform as platform_module
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional


SUPPORTED_PLATFORMS = ("codex", "claude", "lux")


@dataclass(frozen=True)
class PlatformAdapter:
    """Centralizes operating-system paths and capabilities used by the domain layer."""

    system: str
    home: Path
    machine: str = ""
    lux_neo_home: Optional[Path] = None

    @classmethod
    def current(cls) -> "PlatformAdapter":
        home = Path.home()
        configured_lux_home = os.environ.get("SKILLS_VAULT_LUX_NEO_HOME")
        runtime_lux_home = os.environ.get("LUX_HOME")
        if not configured_lux_home and runtime_lux_home:
            candidate = Path(runtime_lux_home).expanduser()
            candidate_parent = os.path.normcase(os.path.abspath(str(candidate.parent)))
            current_home = os.path.normcase(os.path.abspath(str(home)))
            if candidate.name == ".lux_neo" and candidate_parent == current_home:
                configured_lux_home = runtime_lux_home
        return cls(
            system=platform_module.system().lower(),
            home=home,
            machine=platform_module.machine().lower(),
            lux_neo_home=Path(configured_lux_home).expanduser() if configured_lux_home else None,
        )

    @property
    def platform_id(self) -> str:
        if self.system.startswith("win"):
            return "windows"
        if self.system == "darwin":
            return "macos"
        if self.system == "linux":
            return "linux"
        return self.system or "unknown"

    @property
    def is_windows(self) -> bool:
        return self.platform_id == "windows"

    @property
    def default_deployment_type(self) -> str:
        return "managed-copy" if self.is_windows else "symlink"

    @property
    def file_deployment_type(self) -> str:
        return "managed-copy-file" if self.is_windows else "symlink-file"

    @property
    def lux_neo_dir(self) -> Path:
        return self.lux_neo_home or self.home / ".lux_neo"

    @property
    def legacy_lux_skill_dir(self) -> Path:
        """Old Lux Desktop root, recognized only while removing managed legacy rows."""

        return self.home / ".lux" / "skills"

    def agent_skill_dirs(self) -> Dict[str, Path]:
        return {
            "codex": self.home / ".agents" / "skills",
            "claude": self.home / ".claude" / "skills",
            "lux": self.lux_neo_dir / "skills",
        }

    def managed_skill_roots(self, platform: object) -> tuple[Path, ...]:
        key = str(platform)
        root = self.agent_skill_dirs().get(key)
        if root is None:
            return ()
        if key == "lux":
            return (root, self.legacy_lux_skill_dir)
        return (root,)

    def is_legacy_lux_skill_path(self, value: object) -> bool:
        if not value:
            return False
        destination_parent = os.path.normcase(os.path.abspath(str(Path(str(value)).parent)))
        legacy_root = os.path.normcase(os.path.abspath(str(self.legacy_lux_skill_dir)))
        return destination_parent == legacy_root

    def manages_active_skill_path(self, platform: object, value: object) -> bool:
        root = self.agent_skill_dirs().get(str(platform))
        if root is None or not value:
            return False
        destination_parent = os.path.normcase(os.path.abspath(str(Path(str(value)).parent)))
        managed_root = os.path.normcase(os.path.abspath(str(root)))
        return destination_parent == managed_root

    def manages_skill_path(self, platform: object, value: object) -> bool:
        if self.manages_active_skill_path(platform, value):
            return True
        return str(platform) == "lux" and self.is_legacy_lux_skill_path(value)

    def installation_matches(self, installation: object) -> bool:
        if not isinstance(installation, dict):
            return True
        recorded_platform = installation.get("platform")
        recorded_home = installation.get("home")
        if recorded_platform and recorded_platform != self.platform_id:
            return False
        if recorded_home:
            current_home = os.path.normcase(os.path.abspath(str(self.home)))
            expected_home = os.path.normcase(os.path.abspath(str(recorded_home)))
            if current_home != expected_home:
                return False
        recorded_id = installation.get("id")
        if recorded_id:
            identity_path = self.home / ".skills-vault" / "installation-id"
            if identity_path.is_symlink() or not identity_path.is_file():
                return False
            try:
                return identity_path.read_text(encoding="ascii").strip() == recorded_id
            except (OSError, UnicodeError):
                return False
        return True

    def backup_targets(self) -> Dict[str, Path]:
        return {
            "agents-skills": self.home / ".agents" / "skills",
            "claude-skills": self.home / ".claude" / "skills",
            # Keep the historical label stable so older backups still restore
            # to the old Lux Desktop root rather than into Lux Neo.
            "lux-skills": self.legacy_lux_skill_dir,
            "lux-neo-skills": self.agent_skill_dirs()["lux"],
            "claude-commands": self.home / ".claude" / "commands",
            "codex-skills-user": self.home / ".codex" / "skills",
        }

    def executable(self, name: str) -> Optional[Path]:
        candidates = [name]
        if self.is_windows and not name.lower().endswith((".exe", ".cmd", ".bat")):
            candidates.extend([f"{name}.exe", f"{name}.cmd", f"{name}.bat"])
        for candidate in candidates:
            found = shutil.which(candidate)
            if found:
                return Path(found)
        return None

    def environment_path(self) -> str:
        return os.environ.get("PATH", "")


def current_platform() -> PlatformAdapter:
    return PlatformAdapter.current()
