from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .core import VaultError, run
from .executable_resolver import ResolvedExecutable, environment_for, resolve_executable
from .platform_adapter import PlatformAdapter, current_platform


DEPENDENCY_META: Dict[str, Dict[str, Any]] = {
    "git": {
        "label": "Git",
        "capabilities": ["添加和更新 Git 来源", "本地版本历史"],
        "official_url": "https://git-scm.com/downloads",
    },
    "node": {
        "label": "Node.js",
        "capabilities": ["运行外部 Skills CLI 来源"],
        "official_url": "https://nodejs.org/en/download",
    },
    "npm": {
        "label": "npm",
        "capabilities": ["运行外部 Skills CLI 来源"],
        "official_url": "https://docs.npmjs.com/downloading-and-installing-node-js-and-npm",
    },
    "npx": {
        "label": "npx",
        "capabilities": ["发现、安装和更新 Skills CLI 来源"],
        "official_url": "https://docs.npmjs.com/cli/commands/npx",
    },
    "skills-cli": {
        "label": "Skills CLI",
        "capabilities": ["发现、安装和更新外部 Skills 来源"],
        "official_url": "https://skills.sh/",
    },
}


def _command(adapter: PlatformAdapter, executable: Path, *args: str) -> List[str]:
    if adapter.is_windows and executable.suffix.lower() in (".cmd", ".bat"):
        return [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/s", "/c", str(executable), *args]
    return [str(executable), *args]


def _version(adapter: PlatformAdapter, executable: ResolvedExecutable) -> Optional[str]:
    result = run(
        _command(adapter, executable.path, "--version"),
        check=False,
        env=environment_for(executable),
        timeout=10,
    )
    value = ((result.stdout or "") + "\n" + (result.stderr or "")).strip().splitlines()
    return value[0][:160] if value else None


def dependency_status(adapter: Optional[PlatformAdapter] = None) -> Dict[str, Any]:
    platform = adapter or current_platform()
    dependencies: List[Dict[str, Any]] = []
    discovered: Dict[str, Optional[ResolvedExecutable]] = {}
    for dependency in ("git", "node", "npm", "npx"):
        executable = resolve_executable(dependency, platform)
        discovered[dependency] = executable
        metadata = DEPENDENCY_META[dependency]
        dependencies.append(
            {
                "id": dependency,
                **metadata,
                "status": "available" if executable else "missing",
                "path": str(executable.path) if executable else None,
                "version": _version(platform, executable) if executable else None,
                "resolution_source": executable.source if executable else None,
            }
        )
    npx = discovered["npx"]
    dependencies.append(
        {
            "id": "skills-cli",
            **DEPENDENCY_META["skills-cli"],
            "status": "unverified" if npx else "missing",
            "path": str(npx.path) if npx else None,
            "version": None,
            "resolution_source": npx.source if npx else None,
            "notes": [
                "启动检测不会访问网络；首次来源操作时才由 npx 验证 Skills CLI。"
                if npx
                else "安装 Node.js/npm/npx 后即可按需运行，无需全局安装。"
            ],
        }
    )
    installers = []
    for provider in ("winget", "brew", "apt-get", "dnf"):
        executable = resolve_executable(provider, platform)
        if executable:
            installers.append({"id": provider, "path": str(executable.path), "resolution_source": executable.source})
    return {
        "platform": platform.platform_id,
        "architecture": platform.machine,
        "dependencies": dependencies,
        "installers": installers,
        "offline": True,
    }


def dependency_install_plan(
    dependency: str,
    adapter: Optional[PlatformAdapter] = None,
) -> Dict[str, Any]:
    platform = adapter or current_platform()
    dependency = str(dependency).strip().lower()
    if dependency not in ("git", "node"):
        raise VaultError("Only Git and Node.js have managed installation plans")
    metadata = DEPENDENCY_META[dependency]
    command: List[str] = []
    provider: Optional[str] = None
    can_execute = False
    requires_elevation = False
    if platform.platform_id == "windows":
        executable = resolve_executable("winget", platform)
        if executable:
            provider = "winget"
            package = "Git.Git" if dependency == "git" else "OpenJS.NodeJS.LTS"
            command = [
                str(executable.path),
                "install",
                "--id",
                package,
                "--exact",
                "--accept-package-agreements",
                "--accept-source-agreements",
                "--disable-interactivity",
            ]
            can_execute = True
    elif platform.platform_id == "macos":
        executable = resolve_executable("brew", platform)
        if executable:
            provider = "homebrew"
            command = [str(executable.path), "install", "git" if dependency == "git" else "node"]
            can_execute = True
    else:
        provider = "system-package-manager"
        package = "git" if dependency == "git" else "nodejs"
        package_manager = None
        for manager_name in ("apt-get", "dnf"):
            package_manager = resolve_executable(manager_name, platform)
            if package_manager:
                break
        if package_manager:
            provider = package_manager.name
            command = ["sudo", str(package_manager.path), "install", package]
        else:
            command = ["sudo", "apt-get", "install", package]
        requires_elevation = True
    return {
        "dependency": dependency,
        "label": metadata["label"],
        "provider": provider,
        "command": command,
        "display_command": " ".join(command),
        "can_execute": can_execute,
        "requires_elevation": requires_elevation,
        "official_url": metadata["official_url"],
        "notes": [
            "应用不会自动提权；无法安全自动执行时只提供官方安装入口和命令。",
            "安装由系统包管理器完成，不会修改 Vault 内容。",
        ],
    }


def execute_dependency_install(plan: Dict[str, Any]) -> Dict[str, Any]:
    if not plan.get("can_execute") or plan.get("requires_elevation"):
        raise VaultError("This dependency installation plan requires manual action")
    command = [str(part) for part in plan.get("command") or []]
    if not command:
        raise VaultError("Dependency installation command is missing")
    result = run(command, timeout=900)
    output = ((result.stdout or "") + "\n" + (result.stderr or "")).strip()
    return {
        "dependency": plan["dependency"],
        "provider": plan.get("provider"),
        "status": "complete",
        "output": output[-12000:],
    }
