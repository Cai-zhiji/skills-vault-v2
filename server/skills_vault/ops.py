from __future__ import annotations

import json
import os
import re
import secrets
import shutil
import subprocess
import tempfile
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .core import (
    Vault,
    VaultError,
    git,
    git_clean,
    git_commit,
    load_data,
    now_iso,
    parse_frontmatter,
    run,
    tree_fingerprint,
    valid_skill_name,
    write_data,
)
from .deployment import (
    apply_deployment,
    deployment_fingerprint,
    deployment_is_current,
    legacy_links,
    path_fingerprint,
    remove_deployment,
    remove_path,
    state_deployments,
)
from .platform_adapter import PlatformAdapter, SUPPORTED_PLATFORMS, current_platform
from .executable_resolver import environment_for, resolve_executable
from .skills_cli import update as update_skills_cli_source


class InstallRollbackError(VaultError):
    """Raised when an install fails and its automatic backup restore also fails."""


def _discovered_vault_deployments(
    vault: Vault, adapter: Optional[PlatformAdapter] = None
) -> List[Dict[str, Any]]:
    """Find Vault-owned symlinks even when install-state.json was lost.

    Restore/migration can restore the platform directories without restoring
    the corresponding state file.  Treating the filesystem as a secondary
    source of truth lets a subsequent install/uninstall reconcile those links
    without touching unrelated user files.
    """

    platform_adapter = adapter or current_platform()
    catalog = load_data(vault.root / "catalog" / "catalog.json", {"skills": []})
    targets: Dict[Path, Dict[str, Any]] = {}
    for entry in catalog.get("skills", []):
        if not entry.get("path"):
            continue
        skill_root = (vault.root / entry["path"]).resolve()
        if skill_root.is_dir():
            targets[skill_root] = entry
        skill_md = skill_root / "SKILL.md"
        if skill_md.is_file():
            targets[skill_md.resolve()] = entry
        watcher = skill_root / "SKILL.json"
        named_watcher = skill_root / f"{entry.get('name', '')}.json"
        if watcher.is_file():
            targets[watcher.resolve()] = entry
        elif named_watcher.is_file():
            targets[named_watcher.resolve()] = entry
    discovered: List[Dict[str, Any]] = []
    for platform_name, directory in platform_adapter.agent_skill_dirs().items():
        if not directory.is_dir():
            continue
        for destination in directory.iterdir():
            if not destination.is_symlink():
                continue
            target = destination.resolve(strict=False)
            if platform_name != "lux" and target.is_file():
                continue
            entry = targets.get(target)
            if not entry:
                try:
                    relative_target = target.relative_to(vault.root.resolve())
                except ValueError:
                    continue
                # A deleted Vault skill is no longer in the catalog, but its
                # stale symlink is still safely identifiable by its target.
                if not relative_target.parts or relative_target.parts[0] not in {"my-skills", "sources"}:
                    continue
                discovered.append(
                    {
                        "path": str(destination),
                        "target": str(target),
                        "skill_id": f"vault/{relative_target.as_posix()}",
                        "platform": platform_name,
                        "deployment_type": "symlink-file" if destination.suffix in {".md", ".json"} else "symlink",
                        "source_fingerprint": "missing",
                        "deployed_fingerprint": "missing",
                    }
                )
                continue
            discovered.append(
                {
                    "path": str(destination),
                    "target": str(target),
                    "skill_id": entry["id"],
                    "platform": platform_name,
                    "deployment_type": "symlink-file" if target.is_file() else "symlink",
                    "source_fingerprint": deployment_fingerprint(destination, "symlink-file" if target.is_file() else "symlink"),
                    "deployed_fingerprint": deployment_fingerprint(destination, "symlink-file" if target.is_file() else "symlink"),
                }
            )
    return discovered


def _normalized_home(value: Any) -> str:
    raw = str(value)
    normalized = raw.replace("\\", "/").rstrip("/")
    return normalized.casefold() if PureWindowsPath(raw).is_absolute() else normalized


def _deployment_home(row: Dict[str, Any]) -> Optional[str]:
    value = str(row.get("path") or "")
    platform = row.get("platform")
    markers = {
        "codex": {".agents"},
        "claude": {".claude"},
        # Old Lux rows remain valid only long enough to migrate their managed
        # deployments into Lux Neo's LUX_HOME.
        "lux": {".lux", ".lux_neo"},
    }
    platform_markers = markers.get(platform)
    if not value or not platform_markers:
        return None
    windows_path = PureWindowsPath(value)
    if windows_path.is_absolute():
        destination = windows_path
    else:
        posix_path = PurePosixPath(value)
        if not posix_path.is_absolute():
            return None
        destination = posix_path
    skills_root = destination.parent
    if skills_root.name != "skills" or skills_root.parent.name not in platform_markers:
        return None
    return _normalized_home(skills_root.parent.parent)


def _local_installation_id(adapter: PlatformAdapter) -> str:
    identity_root = adapter.home / ".skills-vault"
    if identity_root.is_symlink():
        raise VaultError(f"Installation identity directory must not be a symlink: {identity_root}")
    identity_root.mkdir(parents=True, exist_ok=True)
    if not identity_root.is_dir():
        raise VaultError(f"Installation identity directory is invalid: {identity_root}")
    identity_path = identity_root / "installation-id"
    if identity_path.is_symlink():
        raise VaultError(f"Installation identity must not be a symlink: {identity_path}")
    if not identity_path.exists():
        token = secrets.token_hex(16)
        try:
            with identity_path.open("x", encoding="ascii") as handle:
                handle.write(token)
        except FileExistsError:
            pass
    if not identity_path.is_file():
        raise VaultError(f"Installation identity is invalid: {identity_path}")
    value = identity_path.read_text(encoding="ascii").strip()
    if not re.fullmatch(r"[0-9a-f]{32}", value):
        raise VaultError(f"Installation identity is invalid: {identity_path}")
    return value


def _installation_metadata(adapter: PlatformAdapter) -> Dict[str, str]:
    return {
        "platform": adapter.platform_id,
        "home": str(adapter.home),
        "id": _local_installation_id(adapter),
    }


def _state_is_from_another_installation(
    state: Dict[str, Any], adapter: PlatformAdapter
) -> bool:
    rows = state_deployments(state)
    installation = state.get("installation")
    if isinstance(installation, dict):
        recorded_home = installation.get("home")
        if not recorded_home:
            return False
        homes = {_deployment_home(row) for row in rows}
        if rows and (None in homes or homes != {_normalized_home(recorded_home)}):
            raise VaultError("Install state metadata does not match its deployment paths")
        return not adapter.installation_matches(installation)

    if not rows:
        return False
    homes = {_deployment_home(row) for row in rows}
    if None in homes or len(homes) != 1:
        raise VaultError("Install state contains invalid or mixed deployment roots")
    return next(iter(homes)) != _normalized_home(adapter.home)


def current_state_deployments(
    state: Dict[str, Any], adapter: Optional[PlatformAdapter] = None
) -> List[Dict[str, Any]]:
    platform_adapter = adapter or current_platform()
    if _state_is_from_another_installation(state, platform_adapter):
        return []
    return state_deployments(state)


def managed_current_state_deployments(
    state: Dict[str, Any], adapter: Optional[PlatformAdapter] = None
) -> List[Dict[str, Any]]:
    platform_adapter = adapter or current_platform()
    return [
        row
        for row in current_state_deployments(state, platform_adapter)
        if platform_adapter.manages_skill_path(row.get("platform"), row.get("path"))
    ]


def _known_deployments(
    vault: Vault,
    state: Dict[str, Any],
    adapter: Optional[PlatformAdapter] = None,
) -> List[Dict[str, Any]]:
    """Merge current-installation state with recoverable filesystem evidence."""

    platform_adapter = adapter or current_platform()
    rows = current_state_deployments(state, platform_adapter)
    by_path = {str(row.get("path")): row for row in rows if row.get("path")}
    for row in _discovered_vault_deployments(vault, platform_adapter):
        by_path.setdefault(row["path"], row)
    return list(by_path.values())


def deployment_in_managed_bounds(
    vault: Vault,
    row: Dict[str, Any],
    adapter: PlatformAdapter,
) -> bool:
    return bool(
        row.get("target")
        and adapter.manages_skill_path(row.get("platform"), row.get("path"))
    )


def confirm(question: str, assume_yes: bool = False) -> bool:
    if assume_yes:
        return True
    try:
        return input(f"{question} [y/N] ").strip().lower() in ("y", "yes")
    except EOFError:
        return False


def _is_ancestor(repo: Path, older: str, newer: str) -> bool:
    git_executable = resolve_executable("git", current_platform())
    if not git_executable:
        return False
    result = run([str(git_executable.path), "merge-base", "--is-ancestor", older, newer], cwd=repo, check=False)
    return result.returncode == 0


def _https_fallback(url: str) -> Optional[str]:
    match = re.fullmatch(r"git@github\.com:([^/]+)/(.+?)(?:\.git)?", url)
    if match:
        return f"https://github.com/{match.group(1)}/{match.group(2)}.git"
    return None


def _fetch(repo: Path, source: Dict[str, Any]) -> None:
    git_executable = resolve_executable("git", current_platform())
    if not git_executable:
        raise VaultError("Required program not found: git")
    fetch_env = dict(os.environ)
    fetch_env["GIT_TERMINAL_PROMPT"] = "0"
    try:
        run(
            [
                str(git_executable.path),
                "-c",
                "core.sshCommand=ssh -o ConnectTimeout=5 -o BatchMode=yes",
                "fetch",
                "--prune",
                "origin",
            ],
            cwd=repo,
            env=fetch_env,
        )
        return
    except VaultError as first_error:
        fallback = _https_fallback(source.get("url", ""))
        if not fallback:
            raise first_error
        branch = source.get("branch", "main")
        try:
            run(
                [
                    str(git_executable.path),
                    "-c",
                    "credential.interactive=never",
                    "fetch",
                    "--prune",
                    fallback,
                    f"+refs/heads/{branch}:refs/remotes/origin/{branch}",
                ],
                cwd=repo,
                env=fetch_env,
            )
        except VaultError:
            raise first_error


def update_plan(vault: Vault, source_filter: Optional[Sequence[str]] = None) -> List[Dict[str, Any]]:
    selected = set(source_filter or vault.registry["sources"].keys())
    unknown = selected - set(vault.registry["sources"])
    if unknown:
        raise VaultError(f"Unknown sources: {', '.join(sorted(unknown))}")
    rows: List[Dict[str, Any]] = []
    for source_id, source in vault.registry["sources"].items():
        if source_id not in selected:
            continue
        repo = vault.source_path(source)
        if vault.source_kind(source) == "local-copy":
            revision = vault.source_revision(source)
            rows.append(
                {
                    "source_id": source_id,
                    "source_kind": "local-copy",
                    "status": "local-copy" if revision else "missing",
                    "head": revision,
                    "target": revision,
                    "branch": None,
                    "dirty": False,
                    "commits": [],
                    "changes": [],
                    "risk_signals": [],
                    "notes": ["本地复制来源不会自动从原目录更新。"],
                }
            )
            continue
        if vault.source_kind(source) == "skills-cli":
            revision = vault.source_revision(source)
            if not revision or not vault.source_skill_root(source).is_dir():
                rows.append({"source_id": source_id, "source_kind": "skills-cli", "status": "missing", "path": str(repo)})
                continue
            if source.get("hold"):
                rows.append(
                    {
                        "source_id": source_id,
                        "source_kind": "skills-cli",
                        "status": "held",
                        "head": revision,
                        "target": revision,
                        "branch": None,
                        "dirty": False,
                        "commits": [],
                        "changes": [],
                        "risk_signals": [],
                    }
                )
                continue
            rows.append(
                {
                    "source_id": source_id,
                    "source_kind": "skills-cli",
                    "status": "self-managed",
                    "head": revision,
                    "target": "latest-from-source",
                    "branch": None,
                    "dirty": False,
                    "commits": [],
                    "changes": [],
                    "risk_signals": ["external-cli-update"],
                    "notes": ["由 npx skills update 管理；该来源不参与 Git commit 锁定。"],
                }
            )
            continue
        if not (repo / ".git").exists():
            rows.append({"source_id": source_id, "status": "missing", "path": str(repo)})
            continue
        _fetch(repo, source)
        head = git_commit(repo)
        branch = source.get("branch", "main")
        if source.get("hold"):
            rows.append(
                {
                    "source_id": source_id,
                    "source_kind": "git",
                    "status": "held",
                    "head": head,
                    "target": head,
                    "branch": branch,
                    "dirty": not git_clean(repo),
                    "commits": [],
                    "changes": [],
                    "risk_signals": [],
                }
            )
            continue
        target_ref = source.get("pin") or f"refs/remotes/origin/{branch}"
        target = git(repo, "rev-parse", target_ref, check=False)
        if not target:
            rows.append({"source_id": source_id, "status": "missing-remote-ref", "head": head})
            continue
        if head == target:
            status = "up-to-date"
        elif _is_ancestor(repo, head, target):
            status = "fast-forward"
        else:
            status = "diverged"
        commits = []
        changes = []
        if head != target:
            commits = git(repo, "log", "--format=%h %cI %s", f"{head}..{target}", check=False).splitlines()
            changes = git(repo, "diff", "--name-status", head, target, check=False).splitlines()
        risk_signals = set()
        for change in changes:
            path = change.split("\t")[-1]
            if path.endswith("SKILL.md"):
                risk_signals.add("skill-instructions")
            if "/scripts/" in f"/{path}" or Path(path).suffix in (".sh", ".py", ".js", ".ts", ".ps1"):
                risk_signals.add("executable-code")
            if path.endswith("agents/openai.yaml") or "plugin" in path or "hook" in path:
                risk_signals.add("agent-metadata")
            if change.startswith("D"):
                risk_signals.add("deletions")
        rows.append(
            {
                "source_id": source_id,
                "source_kind": "git",
                "status": status,
                "head": head,
                "target": target,
                "branch": branch,
                "target_ref": target_ref,
                "dirty": not git_clean(repo),
                "commits": commits,
                "changes": changes,
                "risk_signals": sorted(risk_signals),
            }
        )
    return rows


def save_update_report(vault: Vault, rows: List[Dict[str, Any]], applied: bool) -> Tuple[Path, Path]:
    stamp = now_iso().replace(":", "-")
    base = vault.root / "catalog" / "updates" / stamp
    payload = {
        "schema_version": 1,
        "generated_at": now_iso(),
        "applied": applied,
        "sources": rows,
    }
    write_data(base.with_suffix(".json"), payload)
    lines = ["# Upstream update report", "", f"Generated: {payload['generated_at']}", "", f"Applied: **{applied}**", ""]
    for row in rows:
        lines.extend([f"## {row['source_id']}", "", f"Status: `{row['status']}`", ""])
        if row.get("head"):
            lines.append(f"- Current: `{row['head']}`")
        if row.get("target"):
            lines.append(f"- Target: `{row['target']}`")
        if row.get("risk_signals"):
            lines.append(f"- Risks: {', '.join(row['risk_signals'])}")
        if row.get("commits"):
            lines.extend(["", "Commits:", "", *[f"- {item}" for item in row["commits"]]])
        if row.get("changes"):
            lines.extend(["", "Files:", "", "```text", *row["changes"], "```"])
        lines.append("")
    md_path = base.with_suffix(".md")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return base.with_suffix(".json"), md_path


def apply_updates(vault: Vault, rows: List[Dict[str, Any]], assume_yes: bool = False) -> bool:
    blocked = [row for row in rows if row["status"] in ("missing", "missing-remote-ref", "diverged")]
    if blocked:
        detail = ", ".join(f"{row['source_id']}={row['status']}" for row in blocked)
        raise VaultError(f"Cannot update blocked sources: {detail}")
    git_candidates = [row for row in rows if row["status"] == "fast-forward"]
    cli_candidates = [row for row in rows if row["status"] == "self-managed"]
    candidates = git_candidates + cli_candidates
    if not candidates:
        save_update_report(vault, rows, applied=False)
        return False
    dirty = [row["source_id"] for row in git_candidates if row.get("dirty")]
    if dirty:
        raise VaultError(f"Refusing to update dirty sources: {', '.join(dirty)}")
    summary = ", ".join(
        f"{row['source_id']} ({len(row['commits'])} commits)"
        if row["status"] == "fast-forward"
        else f"{row['source_id']} (skills CLI)"
        for row in candidates
    )
    if not confirm(f"Apply source updates to {summary}?", assume_yes):
        save_update_report(vault, rows, applied=False)
        return False

    old_lock = load_data(vault.lock_path)
    transaction = {
        "schema_version": 1,
        "created_at": now_iso(),
        "status": "applying",
        "old_lock": old_lock,
        "sources": {
            row["source_id"]: (
                {
                    "kind": "git",
                    "old_commit": row["head"],
                    "new_commit": row["target"],
                }
                if row.get("source_kind", "git") == "git"
                else {
                    "kind": "skills-cli",
                    "old_revision": row["head"],
                    "target": row["target"],
                }
            )
            for row in candidates
        },
    }
    transaction_path = vault.state_dir / "transactions" / f"{transaction['created_at'].replace(':', '-')}.json"
    write_data(transaction_path, transaction)
    applied: List[Tuple[str, Path, str]] = []
    cli_backups: List[Tuple[str, Path, Path]] = []
    try:
        for row in git_candidates:
            source = vault.registry["sources"][row["source_id"]]
            repo = vault.source_path(source)
            git(repo, "merge", "--ff-only", row["target"])
            applied.append((row["source_id"], repo, row["head"]))
        for row in cli_candidates:
            source = vault.registry["sources"][row["source_id"]]
            repo = vault.source_path(source)
            allowed_parent = (vault.root / "sources" / "skills-cli").resolve()
            if allowed_parent not in repo.parents:
                raise VaultError(f"Refusing to update skills-cli source outside {allowed_parent}: {repo}")
            backup_root = Path(tempfile.mkdtemp(prefix=f"skills-vault-{row['source_id']}-"))
            backup = backup_root / "source"
            shutil.copytree(repo, backup, symlinks=True)
            cli_backups.append((row["source_id"], repo, backup))
            update_result = update_skills_cli_source(repo)
            row["changes"] = [
                f"skills: {', '.join(update_result.get('before', []))}",
                f"updated: {', '.join(update_result.get('after', []))}",
            ]
            row["target"] = vault.source_revision(source)
        vault.update_lock()
        vault.scan()
        errors, _ = lint_vault(vault)
        if errors:
            raise VaultError("Post-update lint failed:\n" + "\n".join(f"- {item}" for item in errors))
        transaction["status"] = "complete"
        transaction["completed_at"] = now_iso()
        write_data(transaction_path, transaction)
        save_update_report(vault, rows, applied=True)
        for _, _, backup in cli_backups:
            shutil.rmtree(backup.parent, ignore_errors=True)
        return True
    except Exception:
        for _, repo, old_commit in reversed(applied):
            git(repo, "reset", "--hard", old_commit)
        for _, repo, backup in reversed(cli_backups):
            if repo.exists():
                shutil.rmtree(repo)
            shutil.copytree(backup, repo, symlinks=True)
            shutil.rmtree(backup.parent, ignore_errors=True)
        write_data(vault.lock_path, old_lock)
        transaction["status"] = "rolled-back"
        transaction["completed_at"] = now_iso()
        write_data(transaction_path, transaction)
        vault.scan()
        raise


def rollback_source(vault: Vault, source_id: str, commit: Optional[str], assume_yes: bool = False) -> str:
    if source_id not in vault.registry["sources"]:
        raise VaultError(f"Unknown source: {source_id}")
    source = vault.registry["sources"][source_id]
    if vault.source_kind(source) != "git":
        raise VaultError("Rollback by commit applies only to strict Git sources")
    repo = vault.source_path(source)
    if not git_clean(repo):
        raise VaultError(f"Source {source_id} is dirty")
    target = commit
    if not target:
        transactions = sorted((vault.state_dir / "transactions").glob("*.json"), reverse=True)
        for path in transactions:
            data = load_data(path)
            if source_id in data.get("sources", {}):
                target = data["sources"][source_id]["old_commit"]
                break
    if not target:
        raise VaultError("No previous transaction found; supply --to COMMIT")
    resolved = git(repo, "rev-parse", f"{target}^{{commit}}", check=False)
    if not resolved:
        raise VaultError(f"Commit is not available in {source_id}: {target}")
    current = git_commit(repo)
    if current == resolved:
        return resolved
    if not confirm(f"Reset read-only source {source_id} from {current[:12]} to {resolved[:12]}?", assume_yes):
        raise VaultError("Rollback cancelled")
    git(repo, "reset", "--hard", resolved)
    vault.update_lock()
    vault.scan()
    return resolved


def _profile_reference_errors(vault: Vault, catalog: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    by_id = {entry["id"]: entry for entry in catalog["skills"]}
    for name, path in vault.profile_files().items():
        try:
            profile = load_data(path)
        except VaultError as exc:
            errors.append(str(exc))
            continue
        for entry_id in profile.get("include", []):
            if entry_id not in by_id:
                errors.append(f"Profile {name} refers to missing skill {entry_id}")
            elif by_id[entry_id]["source_id"] != "my":
                source = vault.registry["sources"][by_id[entry_id]["source_id"]]
                if source.get("trust") not in ("trusted", "reviewed"):
                    errors.append(f"Profile {name} enables unreviewed source skill {entry_id}")
        for source_id in profile.get("include_source", []):
            if source_id not in vault.registry["sources"]:
                errors.append(f"Profile {name} refers to missing source {source_id}")
    for platform in SUPPORTED_PLATFORMS:
        for name in vault.profile_files():
            try:
                vault.resolve_profile([name], platform)
            except VaultError as exc:
                errors.append(str(exc))
    return errors


def _dependency_errors(catalog: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    by_id = {entry["id"]: entry for entry in catalog["skills"]}
    graph: Dict[str, List[str]] = {}
    for entry in catalog["skills"]:
        graph[entry["id"]] = list(entry.get("requires", []))
        for dependency in graph[entry["id"]]:
            if dependency not in by_id:
                errors.append(f"{entry['id']} requires missing skill {dependency}")
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str, trail: List[str]) -> None:
        if node in visiting:
            errors.append("Required dependency cycle: " + " -> ".join(trail + [node]))
            return
        if node in visited or node not in graph:
            return
        visiting.add(node)
        for child in graph[node]:
            visit(child, trail + [node])
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        visit(node, [])
    return errors


def lint_vault(vault: Vault) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    registry = vault.registry
    lock = load_data(vault.lock_path)
    for source_id, source in registry.get("sources", {}).items():
        repo = vault.source_path(source)
        if vault.source_kind(source) == "local-copy":
            if not vault.source_skill_root(source).is_dir():
                errors.append(f"Source {source_id} is missing at {vault.source_skill_root(source)}")
                continue
            observed = vault.source_revision(source)
            locked = lock.get("sources", {}).get(source_id, {}).get("revision")
            if observed != locked:
                errors.append(f"Source {source_id} content does not match lock revision")
            continue
        if vault.source_kind(source) == "skills-cli":
            if not vault.source_skill_root(source).is_dir():
                errors.append(f"Source {source_id} is missing at {vault.source_skill_root(source)}")
            if not (repo / "skills-lock.json").is_file():
                errors.append(f"Source {source_id} is missing skills-lock.json")
            continue
        if not (repo / ".git").exists():
            errors.append(f"Source {source_id} is missing at {repo}")
            continue
        if not git_clean(repo):
            errors.append(f"Source {source_id} has local changes")
        head = git_commit(repo)
        locked = lock.get("sources", {}).get(source_id, {}).get("commit")
        if head != locked:
            errors.append(f"Source {source_id} HEAD {head} does not match lock {locked}")
        remote = git(repo, "remote", "get-url", "origin", check=False)
        if remote and remote != source["url"]:
            errors.append(f"Source {source_id} remote is {remote}, registry says {source['url']}")

    catalog = vault.build_catalog()
    if catalog["duplicate_ids"]:
        for entry_id, paths in catalog["duplicate_ids"].items():
            errors.append(f"Duplicate stable ID {entry_id}: {', '.join(paths)}")
    for entry in catalog["skills"]:
        skill_md = vault.root / entry["path"] / "SKILL.md"
        metadata, _ = parse_frontmatter(skill_md.read_text(encoding="utf-8", errors="replace"))
        if not metadata.get("name"):
            errors.append(f"Missing frontmatter name: {skill_md}")
        if not metadata.get("description"):
            errors.append(f"Missing frontmatter description: {skill_md}")
        text = skill_md.read_text(encoding="utf-8", errors="replace")
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
            clean = target.split("#", 1)[0].strip().strip("<>")
            if not clean or clean.startswith(("http://", "https://", "mailto:", "/", "#")):
                continue
            clean = clean.split()[0]
            if any(char in clean for char in ("{", "}", "$", "*")):
                continue
            if not (skill_md.parent / clean).resolve().exists():
                warnings.append(f"Broken relative link in {entry['id']}: {target}")

    errors.extend(_profile_reference_errors(vault, catalog))
    errors.extend(_dependency_errors(catalog))
    existing_catalog = vault.root / "catalog" / "catalog.json"
    if existing_catalog.exists():
        previous = load_data(existing_catalog)
        if previous.get("fingerprint") != catalog.get("fingerprint"):
            errors.append("Generated catalog is stale; run vault scan")
    else:
        errors.append("Generated catalog is missing; run vault scan")
    return list(dict.fromkeys(errors)), list(dict.fromkeys(warnings))


def doctor(vault: Vault) -> Tuple[List[str], List[str]]:
    errors, warnings = lint_vault(vault)
    checks: List[str] = []
    programs = ["git", "codex", "claude"]
    if any(vault.source_kind(source) == "skills-cli" for source in vault.registry.get("sources", {}).values()):
        programs.append("npx")
    for program in programs:
        resolved = resolve_executable(program, current_platform())
        if resolved:
            version = run(
                [str(resolved.path), "--version"],
                check=False,
                env=environment_for(resolved),
            ).stdout.strip()
            checks.append(f"{program}: {version or resolved.path}")
        elif program in ("git", "npx"):
            errors.append(f"{program} is not installed")
        else:
            warnings.append(f"Optional executable not found: {program}")
    state = load_data(vault.state_dir / "install-state.json", {"links": []})
    for deployment in managed_current_state_deployments(state):
        path = Path(deployment["path"])
        if deployment_is_current(deployment):
            checks.append(f"managed {deployment.get('deployment_type', 'symlink')} ok: {path}")
        else:
            errors.append(
                f"Managed skill deployment is missing, changed, or points to the wrong target: {path}"
            )
    return list(dict.fromkeys(errors)), list(dict.fromkeys(warnings + checks))


def _remove_path(path: Path) -> None:
    remove_path(path)


def _copy_entry(source: Path, destination: Path) -> None:
    if source.is_symlink():
        destination.symlink_to(os.readlink(source), target_is_directory=source.resolve().is_dir())
    elif source.is_dir():
        shutil.copytree(source, destination, symlinks=True)
    else:
        shutil.copy2(source, destination)


def source_audit(vault: Vault, source_id: str) -> Dict[str, Any]:
    if source_id not in vault.registry["sources"]:
        raise VaultError(f"Unknown source: {source_id}")
    source = vault.registry["sources"][source_id]
    repo = vault.source_path(source)
    kind = vault.source_kind(source)
    scan_root = vault.source_skill_root(source)
    if kind == "git" and not (repo / ".git").exists():
        raise VaultError(f"Source is missing: {repo}")
    if kind in ("skills-cli", "local-copy") and not scan_root.is_dir():
        raise VaultError(f"Source is missing: {repo}")
    large_files = []
    escaping_links = []
    script_count = 0
    for path in scan_root.rglob("*"):
        if ".git" in path.parts:
            continue
        if path.is_symlink():
            try:
                path.resolve().relative_to(scan_root.resolve())
            except ValueError:
                escaping_links.append(path.relative_to(scan_root).as_posix())
        elif path.is_file():
            if path.stat().st_size > 10 * 1024 * 1024:
                large_files.append({"path": path.relative_to(scan_root).as_posix(), "bytes": path.stat().st_size})
            if path.suffix.lower() in (".sh", ".bash", ".zsh", ".ps1", ".py", ".js", ".ts", ".mjs"):
                script_count += 1
    licenses = [
        path.relative_to(scan_root).as_posix()
        for path in scan_root.rglob("*")
        if path.is_file() and path.name.lower().startswith(("license", "copying")) and ".git" not in path.parts
    ]
    return {
        "source_id": source_id,
        "kind": kind,
        "commit": vault.source_revision(source),
        "remote": git(repo, "remote", "get-url", "origin", check=False) if kind == "git" else source.get("url"),
        "dirty": not git_clean(repo) if kind == "git" else False,
        "trust": source.get("trust", "unreviewed"),
        "declared_license": source.get("license", "unknown"),
        "license_files": sorted(licenses),
        "has_submodules": (repo / ".gitmodules").exists() if kind == "git" else False,
        "self_managed": kind in ("skills-cli", "local-copy"),
        "large_files": large_files,
        "escaping_symlinks": escaping_links,
        "script_files": script_count,
        "warnings": [
            warning
            for condition, warning in (
                (not licenses, "no license file discovered"),
                (kind == "git" and (repo / ".gitmodules").exists(), "source contains Git submodules"),
                (bool(large_files), "source contains files larger than 10 MiB"),
                (bool(escaping_links), "source contains symlinks escaping its worktree"),
            )
            if condition
        ],
    }


def create_backup(vault: Vault, adapter: Optional[PlatformAdapter] = None) -> Path:
    stamp = now_iso().replace(":", "-")
    backup = vault.state_dir / "backups" / stamp
    suffix = 1
    while backup.exists():
        backup = vault.state_dir / "backups" / f"{stamp}-{suffix}"
        suffix += 1
    backup.mkdir(parents=True, exist_ok=False)
    platform = adapter or current_platform()
    install_state = load_data(vault.state_dir / "install-state.json", {"links": []})
    if state_deployments(install_state):
        write_data(backup / "previous-install-state.json", install_state)
    deployments = _known_deployments(vault, install_state, platform)
    if any(not deployment_in_managed_bounds(vault, row, platform) for row in deployments):
        raise VaultError("Install state contains a deployment outside managed platform roots")
    targets = platform.backup_targets()
    if not any(
        row.get("platform") == "lux" and platform.is_legacy_lux_skill_path(row.get("path"))
        for row in deployments
    ):
        targets.pop("lux-skills", None)
    manifest: Dict[str, Any] = {
        "schema_version": 1,
        "created_at": now_iso(),
        "targets": {},
        "deployments": deployments,
    }
    for label, target in targets.items():
        manifest["targets"][label] = {"path": str(target), "existed": target.exists()}
        if not target.exists():
            continue
        saved = backup / label
        saved.mkdir(parents=True)
        for child in target.iterdir():
            if label == "codex-skills-user" and child.name == ".system":
                continue
            _copy_entry(child, saved / child.name)
    write_data(backup / "manifest.json", manifest)
    return backup


def _reset_user_skill_dirs(adapter: Optional[PlatformAdapter] = None) -> None:
    platform = adapter or current_platform()
    for target in platform.agent_skill_dirs().values():
        target.mkdir(parents=True, exist_ok=True)
        for child in list(target.iterdir()):
            _remove_path(child)
    legacy = platform.home / ".codex" / "skills"
    legacy.mkdir(parents=True, exist_ok=True)
    for child in list(legacy.iterdir()):
        if child.name != ".system":
            _remove_path(child)
    commands = platform.home / ".claude" / "commands"
    if commands.exists():
        for child in list(commands.iterdir()):
            _remove_path(child)


def _validate_lux_watcher(
    watcher_path: Path,
    payload: Any,
    skill_name: str,
    skill_root: Path,
) -> None:
    if not isinstance(payload, dict) or set(payload) - {"version", "skill", "watchers"}:
        raise VaultError(f"Lux Neo watcher has an invalid schema: {watcher_path}")
    watchers = payload.get("watchers")
    if payload.get("version") != 1 or payload.get("skill") != skill_name or not isinstance(watchers, list):
        raise VaultError(f"Lux Neo watcher has an invalid schema: {watcher_path}")

    allowed_fields = {
        "id", "name", "enabled", "promptRef", "triggers", "cooldownTurns",
        "cooldownMs", "maxRunsPerSession", "maxInjectsPerSession",
        "recentCanvasBlocks", "recentToolCalls",
    }
    numeric_fields = {
        "cooldownTurns", "cooldownMs", "maxRunsPerSession", "maxInjectsPerSession",
        "recentCanvasBlocks", "recentToolCalls",
    }
    trigger_fields = {
        "user_message_contains": {"type", "keywords", "caseSensitive"},
        "after_tool_call": {"type", "tools"},
        "on_idle": {"type"},
    }
    seen_ids = set()
    for watcher in watchers:
        if not isinstance(watcher, dict) or set(watcher) - allowed_fields:
            raise VaultError(f"Lux Neo watcher entry has an invalid schema: {watcher_path}")
        watcher_id = watcher.get("id")
        prompt_ref = watcher.get("promptRef")
        triggers = watcher.get("triggers")
        if (
            not isinstance(watcher_id, str)
            or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", watcher_id)
            or watcher_id in seen_ids
            or not isinstance(watcher.get("name"), str)
            or not watcher["name"].strip()
            or not isinstance(watcher.get("enabled"), bool)
            or not isinstance(prompt_ref, str)
            or Path(prompt_ref).name != prompt_ref
            or Path(prompt_ref).suffix.lower() not in {".md", ".txt"}
            or not isinstance(triggers, list)
            or not triggers
        ):
            raise VaultError(f"Lux Neo watcher entry has an invalid schema: {watcher_path}")
        seen_ids.add(watcher_id)
        for field in numeric_fields:
            value = watcher.get(field)
            if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value < 0):
                raise VaultError(f"Lux Neo watcher entry has an invalid schema: {watcher_path}")
        prompt_path = skill_root / prompt_ref
        if (
            prompt_path.is_symlink()
            or not prompt_path.is_file()
            or prompt_path.resolve().parent != skill_root
            or prompt_path.stat().st_size > 16 * 1024
        ):
            raise VaultError(f"Lux Neo watcher prompt is invalid: {prompt_path}")
        for trigger in triggers:
            if not isinstance(trigger, dict) or trigger.get("type") not in trigger_fields:
                raise VaultError(f"Lux Neo watcher trigger has an invalid schema: {watcher_path}")
            trigger_type = trigger["type"]
            if set(trigger) - trigger_fields[trigger_type]:
                raise VaultError(f"Lux Neo watcher trigger has an invalid schema: {watcher_path}")
            if trigger_type == "user_message_contains":
                keywords = trigger.get("keywords")
                if (
                    not isinstance(keywords, list)
                    or not keywords
                    or not all(isinstance(item, str) and item for item in keywords)
                    or ("caseSensitive" in trigger and not isinstance(trigger["caseSensitive"], bool))
                ):
                    raise VaultError(f"Lux Neo watcher trigger has an invalid schema: {watcher_path}")
            elif trigger_type == "after_tool_call":
                tools = trigger.get("tools")
                if not isinstance(tools, list) or not tools or not all(isinstance(item, str) and item for item in tools):
                    raise VaultError(f"Lux Neo watcher trigger has an invalid schema: {watcher_path}")


def _platform_install_operations(
    vault: Vault,
    adapter: PlatformAdapter,
    platform: str,
    destination: Path,
    entry: Dict[str, Any],
) -> List[Dict[str, Any]]:
    if not valid_skill_name(str(entry.get("name", ""))):
        raise VaultError(f"Invalid Skill name for deployment: {entry.get('name', '')}")
    source = (vault.root / entry["path"]).resolve()
    allowed_sources = ((vault.root / "my-skills").resolve(), (vault.root / "sources").resolve())
    if not any(source == root or root in source.parents for root in allowed_sources):
        raise VaultError(f"Skill deployment source escapes the Vault: {source}")
    base = {
        "platform": platform,
        "skill_id": entry["id"],
        "name": entry["name"],
        "allowed_parent": str(destination.resolve()),
        "allowed_source_roots": [str(root) for root in allowed_sources],
    }
    if platform != "lux":
        return [
            {
                **base,
                "path": str(destination / entry["name"]),
                "target": str(source),
                "deployment_type": adapter.default_deployment_type,
                "source_fingerprint": path_fingerprint(source),
            }
        ]

    operations = [
        {
            **base,
            "component": "resources",
            "path": str(destination / entry["name"]),
            "target": str(source),
            "deployment_type": adapter.default_deployment_type,
            "source_fingerprint": path_fingerprint(source),
        },
        {
            **base,
            "component": "skill",
            "path": str(destination / f"{entry['name']}.md"),
            "target": str(source / "SKILL.md"),
            "deployment_type": adapter.file_deployment_type,
            "source_fingerprint": path_fingerprint(source / "SKILL.md"),
        },
    ]
    watcher = source / "SKILL.json"
    named_watcher = source / f"{entry['name']}.json"
    watcher_source = watcher if watcher.is_file() else named_watcher
    if watcher_source.is_file():
        if watcher_source.is_symlink() or watcher_source.resolve().parent != source:
            raise VaultError(f"Lux Neo watcher must be a regular file inside the Skill: {watcher_source}")
        try:
            watcher_payload = json.loads(watcher_source.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise VaultError(f"Lux Neo watcher is not valid JSON: {watcher_source}") from exc
        _validate_lux_watcher(watcher_source, watcher_payload, entry["name"], source)
        operations.append(
            {
                **base,
                "component": "watcher",
                "path": str(destination / f"{entry['name']}.json"),
                "target": str(watcher_source),
                "deployment_type": adapter.file_deployment_type,
                "source_fingerprint": path_fingerprint(watcher_source),
            }
        )
    return operations


def install_plan(
    vault: Vault,
    profiles: Sequence[str],
    adapter: Optional[PlatformAdapter] = None,
) -> Dict[str, Any]:
    platform_adapter = adapter or current_platform()
    platforms = platform_adapter.agent_skill_dirs()
    operations = []
    notes = []
    for platform, destination in platforms.items():
        entries, platform_notes = vault.resolve_profile(profiles, platform)
        notes.extend(f"{platform}: {note}" for note in platform_notes)
        for entry in entries:
            operations.extend(
                _platform_install_operations(vault, platform_adapter, platform, destination, entry)
            )
    current = _known_deployments(
        vault,
        load_data(vault.state_dir / "install-state.json", {"links": []}),
        platform_adapter,
    )
    current_by_path = {str(item["path"]): item for item in current if item.get("path")}
    desired_by_path = {item["path"]: item for item in operations}

    blocked = []
    blocked_paths = set()
    for path, desired in desired_by_path.items():
        destination = Path(path)
        if path not in current_by_path and (destination.exists() or destination.is_symlink()):
            blocked.append({**desired, "reason": "destination-unmanaged"})
            blocked_paths.add(path)
    for path, row in current_by_path.items():
        destination = Path(str(path))
        if (destination.exists() or destination.is_symlink()) and not deployment_is_current(row):
            desired = desired_by_path.get(path, row)
            blocked.append({**desired, "reason": "destination-modified", "current": row})
            blocked_paths.add(path)

    added = [
        item for path, item in desired_by_path.items()
        if path not in current_by_path and path not in blocked_paths
    ]
    removed = [
        item for path, item in current_by_path.items()
        if path not in desired_by_path and path not in blocked_paths
    ]
    changed = [
        item for path, item in desired_by_path.items()
        if path in current_by_path
        and path not in blocked_paths
        and (
            not deployment_is_current(current_by_path[path])
            or current_by_path[path].get("target") != item.get("target")
            or current_by_path[path].get("deployment_type", "symlink") != item.get("deployment_type")
            or current_by_path[path].get("source_fingerprint") != item.get("source_fingerprint")
        )
    ]
    kept = [
        item for path, item in desired_by_path.items()
        if path in current_by_path
        and path not in blocked_paths
        and deployment_is_current(current_by_path[path])
        and current_by_path[path].get("target") == item.get("target")
        and current_by_path[path].get("deployment_type", "symlink") == item.get("deployment_type")
        and current_by_path[path].get("source_fingerprint") == item.get("source_fingerprint")
    ]
    return {
        "profiles": list(profiles),
        "operations": operations,
        "notes": notes,
        "blocked": blocked,
        "changes": {"added": added, "removed": removed, "changed": changed, "kept": kept},
    }


def install(
    vault: Vault,
    profiles: Sequence[str],
    reset: bool = False,
    dry_run: bool = False,
    assume_yes: bool = False,
    backup_path: Optional[Path] = None,
    adapter: Optional[PlatformAdapter] = None,
) -> Dict[str, Any]:
    platform_adapter = adapter or current_platform()
    plan = install_plan(vault, profiles, platform_adapter)
    if dry_run:
        return plan
    if plan.get("blocked"):
        paths = ", ".join(str(item.get("path")) for item in plan["blocked"])
        raise VaultError(f"Install is blocked by modified managed destinations: {paths}")
    if reset and not confirm(
        "Back up and rebuild user-level Codex, Claude Code, and Lux Neo skills plus Claude commands?", assume_yes
    ):
        raise VaultError("Install cancelled")
    backup = backup_path or create_backup(vault, platform_adapter)
    old_state = load_data(vault.state_dir / "install-state.json", {"links": []})
    old_deployments = _known_deployments(vault, old_state, platform_adapter)
    if any(not deployment_in_managed_bounds(vault, row, platform_adapter) for row in old_deployments):
        raise VaultError("Install state contains a deployment outside managed platform roots")
    managed_by_path = {
        str(item.get("path")): item
        for item in old_deployments
        if item.get("path") and item.get("target")
    }
    deployed: List[Dict[str, Any]] = []
    newly_created: List[Dict[str, Any]] = []
    try:
        if reset:
            _reset_user_skill_dirs(platform_adapter)
        desired_paths = {operation["path"] for operation in plan["operations"]}
        for current in old_deployments:
            if str(current.get("path")) not in desired_paths:
                remove_deployment(current)

        for operation in plan["operations"]:
            destination = Path(operation["path"])
            managed = managed_by_path.get(str(destination))
            existed = bool(managed and deployment_is_current(managed))
            row = apply_deployment(operation, managed)
            deployed.append(row)
            if not existed:
                newly_created.append(row)
    except Exception as install_error:
        for row in reversed(newly_created):
            try:
                remove_deployment(row)
            except Exception:
                pass
        if backup:
            try:
                _restore_backup_path(vault, backup, platform_adapter)
            except Exception as restore_error:
                raise InstallRollbackError(
                    f"Install failed ({install_error}); automatic restore from {backup.name} also failed ({restore_error})"
                ) from restore_error
        raise
    state = {
        "schema_version": 2,
        "installation": _installation_metadata(platform_adapter),
        "installed_at": now_iso(),
        "profiles": list(profiles),
        "backup": str(backup) if backup else None,
        "deployments": deployed,
        "links": legacy_links(deployed),
    }
    write_data(vault.state_dir / "install-state.json", state)
    vault.activate_profiles(profiles)
    plan["backup"] = str(backup) if backup else None
    return plan


def uninstall(vault: Vault, assume_yes: bool = False) -> int:
    state_path = vault.state_dir / "install-state.json"
    state = load_data(state_path, {"links": []})
    platform = current_platform()
    deployments = _known_deployments(vault, state, platform)
    if any(not deployment_in_managed_bounds(vault, row, platform) for row in deployments):
        raise VaultError("Install state contains a deployment outside managed platform roots")
    if not deployments:
        return 0
    if not confirm(f"Remove {len(deployments)} Skills Vault-managed deployments?", assume_yes):
        raise VaultError("Uninstall cancelled")
    removed = 0
    for deployment in deployments:
        if remove_deployment(deployment):
            removed += 1
    write_data(
        state_path,
        {
            "schema_version": 2,
            "installation": _installation_metadata(platform),
            "deployments": [],
            "links": [],
            "uninstalled_at": now_iso(),
        },
    )
    return removed


def validated_backup_path(vault: Vault, backup_id: str) -> Path:
    if (
        not backup_id
        or Path(backup_id).name != backup_id
        or "/" in backup_id
        or "\\" in backup_id
        or backup_id in {".", ".."}
    ):
        raise VaultError("Backup ID is invalid")
    root = (vault.state_dir / "backups").resolve()
    backup = (root / backup_id).resolve()
    if backup.parent != root:
        raise VaultError("Backup path escapes the Vault")
    return backup


def _validated_backup_manifest(
    vault: Vault,
    backup: Path,
    platform: PlatformAdapter,
) -> Dict[str, Any]:
    manifest = load_data(backup / "manifest.json")
    if manifest.get("schema_version") != 1:
        raise VaultError("Backup manifest schema is unsupported")
    allowed_targets = platform.backup_targets()
    manifest_targets = manifest.get("targets")
    if not isinstance(manifest_targets, dict) or not set(manifest_targets).issubset(allowed_targets):
        raise VaultError("Backup manifest contains unsupported targets")
    for label, info in manifest_targets.items():
        if not isinstance(info, dict) or not isinstance(info.get("existed"), bool):
            raise VaultError(f"Backup manifest target is invalid: {label}")
        if info["existed"] and not (backup / label).is_dir():
            raise VaultError(f"Backup payload is missing: {label}")
    deployments = manifest.get("deployments", [])
    if not isinstance(deployments, list) or any(
        not isinstance(row, dict) or not deployment_in_managed_bounds(vault, row, platform)
        for row in deployments
    ):
        raise VaultError("Backup manifest contains an unsafe deployment")
    return manifest


def restore_backup(
    vault: Vault,
    backup_id: str,
    assume_yes: bool = False,
    adapter: Optional[PlatformAdapter] = None,
) -> Path:
    platform = adapter or current_platform()
    backup = validated_backup_path(vault, backup_id)
    manifest_path = backup / "manifest.json"
    if not manifest_path.is_file():
        raise VaultError(f"Backup not found: {backup_id}")
    manifest = _validated_backup_manifest(vault, backup, platform)
    if not confirm(f"Replace current user-level skill directories with backup {backup_id}?", assume_yes):
        raise VaultError("Restore cancelled")
    _restore_backup_path(vault, backup, platform, manifest)
    manifest_deployments = manifest.get("deployments", [])
    deployments_by_path = {
        row["path"]: row
        for row in manifest_deployments
        if row.get("path") and deployment_is_current(row)
    }
    for row in _discovered_vault_deployments(vault, platform):
        deployments_by_path.setdefault(row["path"], row)
    deployments = list(deployments_by_path.values())
    write_data(
        vault.state_dir / "install-state.json",
        {
            "schema_version": 2,
            "installation": _installation_metadata(platform),
            "deployments": deployments,
            "links": legacy_links(deployments),
            "restored_at": now_iso(),
            "backup": backup_id,
        },
    )
    return backup


def _restore_backup_path(
    vault: Vault,
    backup: Path,
    adapter: Optional[PlatformAdapter] = None,
    manifest: Optional[Dict[str, Any]] = None,
) -> None:
    platform = adapter or current_platform()
    validated = manifest or _validated_backup_manifest(vault, backup, platform)
    allowed_targets = platform.backup_targets()
    for label, info in validated["targets"].items():
        target = allowed_targets[label]
        if not info.get("existed"):
            if target.exists():
                _remove_path(target)
            continue
        target.mkdir(parents=True, exist_ok=True)
        for child in list(target.iterdir()):
            if label == "codex-skills-user" and child.name == ".system":
                continue
            _remove_path(child)
        saved = backup / label
        if saved.exists():
            for child in saved.iterdir():
                _copy_entry(child, target / child.name)
