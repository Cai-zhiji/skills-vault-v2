from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .platform_adapter import PlatformAdapter, current_platform


@dataclass(frozen=True)
class AppPaths:
    resource_root: Path
    config_root: Path
    log_root: Path
    cache_root: Path
    default_vault_root: Path

    @classmethod
    def for_desktop(
        cls,
        resource_root: Path,
        adapter: PlatformAdapter | None = None,
        environ: dict[str, str] | None = None,
    ) -> "AppPaths":
        platform = adapter or current_platform()
        env = environ if environ is not None else os.environ
        home = platform.home
        if platform.platform_id == "macos":
            config = home / "Library" / "Application Support" / "Skills Vault"
            cache = home / "Library" / "Caches" / "Skills Vault"
        elif platform.platform_id == "windows":
            local_app_data = Path(env.get("LOCALAPPDATA", home / "AppData" / "Local"))
            config = local_app_data / "Skills Vault"
            cache = config / "Cache"
        else:
            config = Path(env.get("XDG_CONFIG_HOME", home / ".config")) / "skills-vault"
            cache = Path(env.get("XDG_CACHE_HOME", home / ".cache")) / "skills-vault"
        documents = home / "Documents"
        return cls(
            resource_root=resource_root.resolve(),
            config_root=config,
            log_root=config / "logs",
            cache_root=cache,
            default_vault_root=documents / "Skills Vault",
        )

    @classmethod
    def for_development(cls, project_root: Path) -> "AppPaths":
        root = project_root.resolve()
        return cls(
            resource_root=root,
            config_root=root / ".vault" / "desktop",
            log_root=root / ".vault" / "logs",
            cache_root=root / ".vault" / "cache",
            default_vault_root=root,
        )
