"""Adapter for sources installed and updated by the external `skills` CLI."""
from __future__ import annotations

import os
import re
import shutil
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from .core import VaultError, parse_frontmatter, run


ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
TRANSIENT_NETWORK_RE = re.compile(
    r"SSL_ERROR_SYSCALL|sslv3 alert handshake failure|Could not resolve host|"
    r"Failed to connect|Connection reset|HTTP/2 stream|unexpected EOF",
    re.I,
)


def _version_key(path: Path) -> tuple[int, ...]:
    values = tuple(int(value) for value in re.findall(r"\d+", path.parent.parent.name))
    return values or (0,)


def _home_directory() -> Path:
    return Path.home()


def _npx_executable() -> Path:
    """Find npx even when launchd starts the UI with its minimal default PATH."""
    candidates: List[Path] = []
    configured = os.environ.get("SKILLS_VAULT_NPX")
    if configured:
        candidates.append(Path(configured).expanduser())
    discovered = shutil.which("npx")
    if discovered:
        candidates.append(Path(discovered))
    nvm_bin = os.environ.get("NVM_BIN")
    if nvm_bin:
        candidates.append(Path(nvm_bin) / "npx")
    home = _home_directory()
    candidates.extend(
        sorted(
            (home / ".nvm" / "versions" / "node").glob("*/bin/npx"),
            key=_version_key,
            reverse=True,
        )
    )
    candidates.extend(
        [
            home / ".volta" / "bin" / "npx",
            home / ".fnm" / "aliases" / "default" / "bin" / "npx",
            Path("/opt/homebrew/bin/npx"),
            Path("/usr/local/bin/npx"),
        ]
    )
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            # Keep the launcher path: npx is commonly a symlink whose target lives
            # under npm/lib, while its sibling `node` is in the launcher directory.
            return candidate.absolute()
    raise VaultError(
        "npx is required for skills-cli sources; install Node.js or set SKILLS_VAULT_NPX"
    )


def _environment() -> Dict[str, str]:
    env = dict(os.environ)
    node_bin = str(_npx_executable().parent)
    path_parts = [part for part in env.get("PATH", "").split(os.pathsep) if part]
    env["PATH"] = os.pathsep.join([node_bin, *[part for part in path_parts if part != node_bin]])
    env.update(
        {
            "CI": "1",
            "NO_COLOR": "1",
            "TERM": "dumb",
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    return env


def _command(*args: str) -> List[str]:
    return [str(_npx_executable()), "--yes", "skills", *args]


def _plain_output(value: str) -> str:
    return ANSI_RE.sub("", value).replace("\r", "")


def _run_cli(args: Sequence[str], cwd: Path, timeout: int):
    for attempt in range(1, 4):
        try:
            return run(args, cwd=cwd, env=_environment(), timeout=timeout)
        except VaultError as exc:
            if attempt == 3 or not TRANSIENT_NETWORK_RE.search(str(exc)):
                raise
            time.sleep(attempt)
    raise AssertionError("unreachable")


def _parse_skill_names(output: str) -> List[str]:
    names = re.findall(r"Skill:\s*([^\n]+)", output)
    if not names:
        names = re.findall(
            r"^[ \t]*(?:│[ \t]*)?([a-z0-9][a-z0-9-]{1,63})[ \t]*$",
            output,
            re.M | re.I,
        )
    return list(dict.fromkeys(name.strip() for name in names if name.strip()))


def discover(source_url: str, full_depth: bool = False) -> Dict[str, object]:
    """Resolve a source without installing it and return its advertised skill names."""
    with tempfile.TemporaryDirectory(prefix="skills-vault-discover-") as directory:
        args = ["add", source_url, "--list"]
        if full_depth:
            args.append("--full-depth")
        result = _run_cli(_command(*args), Path(directory), 180)
    output = _plain_output((result.stdout or "") + "\n" + (result.stderr or ""))
    names = _parse_skill_names(output)
    advertised = re.search(r"Found\s+(\d+)\s+skills?", output, re.I)
    if not names:
        if advertised and int(advertised.group(1)):
            raise VaultError("skills CLI found skills but Vault could not parse their names")
        raise VaultError("skills CLI did not discover any skills at this source")
    return {"skills": names, "output": output[-12000:]}


def installed_skills(workdir: Path) -> List[str]:
    skill_root = workdir / ".agents" / "skills"
    if not skill_root.is_dir():
        return []
    names: List[str] = []
    for skill_md in sorted(skill_root.glob("*/SKILL.md")):
        metadata, _ = parse_frontmatter(skill_md.read_text(encoding="utf-8", errors="replace"))
        names.append(str(metadata.get("name") or skill_md.parent.name))
    return names


def install(
    source_url: str,
    workdir: Path,
    full_depth: bool = False,
    skills: Optional[Sequence[str]] = None,
) -> Dict[str, object]:
    """Install selected advertised skills as copies inside a Vault-owned project directory."""
    workdir.mkdir(parents=True, exist_ok=False)
    selected = list(skills or ["*"])
    args = ["add", source_url, "--skill", *selected, "--agent", "universal", "--copy", "-y"]
    if full_depth:
        args.append("--full-depth")
    result = _run_cli(_command(*args), workdir, 300)
    names = installed_skills(workdir)
    if not names or not (workdir / "skills-lock.json").is_file():
        raise VaultError("skills CLI completed without a usable .agents/skills tree and skills-lock.json")
    output = _plain_output((result.stdout or "") + "\n" + (result.stderr or ""))
    return {"skills": names, "output": output[-12000:]}


def update(workdir: Path) -> Dict[str, object]:
    """Let the external CLI update its own copied skills and lock metadata."""
    if not (workdir / "skills-lock.json").is_file():
        raise VaultError(f"skills-cli lock is missing: {workdir / 'skills-lock.json'}")
    before = installed_skills(workdir)
    result = _run_cli(
        _command("update", "--project", "--yes"),
        workdir,
        300,
    )
    after = installed_skills(workdir)
    if not after:
        raise VaultError("skills CLI update removed every installed skill")
    output = _plain_output((result.stdout or "") + "\n" + (result.stderr or ""))
    return {"before": before, "after": after, "output": output[-12000:]}
