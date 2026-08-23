from __future__ import annotations

import os
import platform as platform_module
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional


@dataclass(frozen=True)
class PlatformAdapter:
    """Centralizes operating-system paths and capabilities used by the domain layer."""

    system: str
    home: Path
    machine: str = ""

    @classmethod
    def current(cls) -> "PlatformAdapter":
        return cls(
            system=platform_module.system().lower(),
            home=Path.home(),
            machine=platform_module.machine().lower(),
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

    def agent_skill_dirs(self) -> Dict[str, Path]:
        return {
            "codex": self.home / ".agents" / "skills",
            "claude": self.home / ".claude" / "skills",
        }

    def backup_targets(self) -> Dict[str, Path]:
        return {
            "agents-skills": self.home / ".agents" / "skills",
            "claude-skills": self.home / ".claude" / "skills",
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
