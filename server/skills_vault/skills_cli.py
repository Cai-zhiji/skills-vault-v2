"""Adapter for sources installed and updated by the external `skills` CLI."""
from __future__ import annotations

import os
import re
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from .core import VaultError, parse_frontmatter, run
from .executable_resolver import ResolvedExecutable, environment_for, resolve_executable
from .platform_adapter import PlatformAdapter


ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
TRANSIENT_NETWORK_RE = re.compile(
    r"SSL_ERROR_SYSCALL|sslv3 alert handshake failure|Could not resolve host|"
    r"Failed to connect|Connection reset|HTTP/2 stream|unexpected EOF",
    re.I,
)


def _home_directory() -> Path:
    return Path.home()


def _platform_adapter() -> PlatformAdapter:
    current = PlatformAdapter.current()
    return PlatformAdapter(current.system, _home_directory(), current.machine)


def _npx_resolution() -> ResolvedExecutable:
    resolved = resolve_executable("npx", _platform_adapter())
    if resolved:
        return resolved
    raise VaultError(
        "npx is required for skills-cli sources; install Node.js or set SKILLS_VAULT_NPX"
    )


def _npx_executable() -> Path:
    return _npx_resolution().path


def _environment() -> Dict[str, str]:
    env = environment_for(_npx_resolution())
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
    resolved = _npx_resolution()
    command = [str(resolved.path), "--yes", "skills", *args]
    if _platform_adapter().is_windows and resolved.path.suffix.lower() in (".cmd", ".bat"):
        return [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/s", "/c", *command]
    return command


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


def add_to_existing(
    source_url: str,
    workdir: Path,
    skills: Sequence[str],
    full_depth: bool = False,
) -> Dict[str, object]:
    """Append selected skills to an existing Vault-owned skills-cli project."""
    if not workdir.is_dir() or not (workdir / "skills-lock.json").is_file():
        raise VaultError(f"skills-cli source is not an installed project: {workdir}")
    selected = list(dict.fromkeys(str(skill).strip() for skill in skills if str(skill).strip()))
    if not selected:
        return {"before": installed_skills(workdir), "after": installed_skills(workdir), "output": "unchanged"}
    before = installed_skills(workdir)
    args = ["add", source_url, "--skill", *selected, "--agent", "universal", "--copy", "-y"]
    if full_depth:
        args.append("--full-depth")
    result = _run_cli(_command(*args), workdir, 300)
    after = installed_skills(workdir)
    if not after or not (workdir / "skills-lock.json").is_file():
        raise VaultError("skills CLI append completed without a usable skills project")
    output = _plain_output((result.stdout or "") + "\n" + (result.stderr or ""))
    return {"before": before, "after": after, "output": output[-12000:]}


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
