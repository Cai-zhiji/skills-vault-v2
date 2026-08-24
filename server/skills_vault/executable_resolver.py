from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from .platform_adapter import PlatformAdapter


@dataclass(frozen=True)
class ResolvedExecutable:
    name: str
    path: Path
    source: str


_EXPLICIT_ENV = {
    "git": "SKILLS_VAULT_GIT",
    "node": "SKILLS_VAULT_NODE",
    "npm": "SKILLS_VAULT_NPM",
    "npx": "SKILLS_VAULT_NPX",
}


def _version_key(path: Path) -> tuple[int, ...]:
    values = tuple(int(value) for value in re.findall(r"\d+", path.parent.parent.name))
    return values or (0,)


def _candidate_names(name: str, adapter: PlatformAdapter) -> Iterable[str]:
    yield name
    if adapter.is_windows and not name.lower().endswith((".exe", ".cmd", ".bat")):
        yield from (f"{name}.exe", f"{name}.cmd", f"{name}.bat")


def _is_executable(path: Path, adapter: PlatformAdapter) -> bool:
    return path.is_file() and (adapter.is_windows or os.access(path, os.X_OK))


def _known_candidates(name: str, adapter: PlatformAdapter) -> Iterable[tuple[Path, str]]:
    home = adapter.home
    if name in ("node", "npm", "npx"):
        versioned = sorted(
            (
                path
                for path in (home / ".nvm" / "versions" / "node").glob("*/bin")
                if path.is_dir()
            ),
            key=_version_key,
            reverse=True,
        )
        for directory in versioned:
            for candidate in _candidate_names(name, adapter):
                yield directory / candidate, "nvm"
        for directory, source in (
            (home / ".volta" / "bin", "volta"),
            (home / ".fnm" / "aliases" / "default" / "bin", "fnm"),
        ):
            for candidate in _candidate_names(name, adapter):
                yield directory / candidate, source
        if adapter.platform_id == "macos":
            for directory in (Path("/opt/homebrew/bin"), Path("/usr/local/bin")):
                for candidate in _candidate_names(name, adapter):
                    yield directory / candidate, "system"
        elif adapter.is_windows:
            windows_dirs = [
                home / "AppData" / "Roaming" / "npm",
                Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "nodejs",
                Path(os.environ.get("ProgramFiles", "")) / "nodejs",
                Path(os.environ.get("ProgramFiles(x86)", "")) / "nodejs",
            ]
            for directory in windows_dirs:
                for candidate in _candidate_names(name, adapter):
                    yield directory / candidate, "system"
        else:
            for directory in (Path("/usr/local/bin"), Path("/usr/bin")):
                for candidate in _candidate_names(name, adapter):
                    yield directory / candidate, "system"


def resolve_executable(name: str, adapter: PlatformAdapter) -> Optional[ResolvedExecutable]:
    explicit = os.environ.get(_EXPLICIT_ENV.get(name, ""), "").strip()
    if explicit:
        candidate = Path(explicit).expanduser()
        if _is_executable(candidate, adapter):
            return ResolvedExecutable(name, candidate.absolute(), "explicit")

    for candidate_name in _candidate_names(name, adapter):
        discovered = shutil.which(candidate_name)
        if discovered:
            path = Path(discovered)
            if _is_executable(path, adapter):
                return ResolvedExecutable(name, path.absolute(), "PATH")

    for candidate, source in _known_candidates(name, adapter):
        if _is_executable(candidate, adapter):
            return ResolvedExecutable(name, candidate.absolute(), source)
    return None


def environment_for(executable: ResolvedExecutable) -> dict[str, str]:
    environment = dict(os.environ)
    directory = str(executable.path.parent)
    parts = [part for part in environment.get("PATH", "").split(os.pathsep) if part]
    environment["PATH"] = os.pathsep.join([directory, *[part for part in parts if part != directory]])
    return environment
