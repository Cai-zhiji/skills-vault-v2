from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
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
    write_data,
)
from .skills_cli import update as update_skills_cli_source


def confirm(question: str, assume_yes: bool = False) -> bool:
    if assume_yes:
        return True
    try:
        return input(f"{question} [y/N] ").strip().lower() in ("y", "yes")
    except EOFError:
        return False


def _is_ancestor(repo: Path, older: str, newer: str) -> bool:
    result = run(["git", "merge-base", "--is-ancestor", older, newer], cwd=repo, check=False)
    return result.returncode == 0


def _https_fallback(url: str) -> Optional[str]:
    match = re.fullmatch(r"git@github\.com:([^/]+)/(.+?)(?:\.git)?", url)
    if match:
        return f"https://github.com/{match.group(1)}/{match.group(2)}.git"
    return None


def _fetch(repo: Path, source: Dict[str, Any]) -> None:
    fetch_env = dict(os.environ)
    fetch_env["GIT_TERMINAL_PROMPT"] = "0"
    try:
        run(
            [
                "git",
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
                    "git",
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
    for platform in ("codex", "claude"):
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
        path = shutil.which(program)
        if path:
            version = run([program, "--version"], check=False).stdout.strip()
            checks.append(f"{program}: {version or path}")
        elif program in ("git", "npx"):
            errors.append(f"{program} is not installed")
        else:
            warnings.append(f"Optional executable not found: {program}")
    state = load_data(vault.state_dir / "install-state.json", {"links": []})
    for link in state.get("links", []):
        path = Path(link["path"])
        target = Path(link["target"])
        if not path.is_symlink():
            errors.append(f"Managed skill link is missing or not a symlink: {path}")
        elif path.resolve() != target.resolve():
            errors.append(f"Managed skill link points to the wrong target: {path}")
        else:
            checks.append(f"managed link ok: {path}")
    return list(dict.fromkeys(errors)), list(dict.fromkeys(warnings + checks))


def _remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


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
    if kind == "skills-cli" and not scan_root.is_dir():
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
        "self_managed": kind == "skills-cli",
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


def create_backup(vault: Vault) -> Path:
    stamp = now_iso().replace(":", "-")
    backup = vault.state_dir / "backups" / stamp
    suffix = 1
    while backup.exists():
        backup = vault.state_dir / "backups" / f"{stamp}-{suffix}"
        suffix += 1
    backup.mkdir(parents=True, exist_ok=False)
    home = Path.home()
    targets = {
        "agents-skills": home / ".agents" / "skills",
        "claude-skills": home / ".claude" / "skills",
        "claude-commands": home / ".claude" / "commands",
        "codex-skills-user": home / ".codex" / "skills",
    }
    manifest: Dict[str, Any] = {"schema_version": 1, "created_at": now_iso(), "targets": {}}
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


def _reset_user_skill_dirs() -> None:
    home = Path.home()
    for target in (home / ".agents" / "skills", home / ".claude" / "skills"):
        target.mkdir(parents=True, exist_ok=True)
        for child in list(target.iterdir()):
            _remove_path(child)
    legacy = home / ".codex" / "skills"
    legacy.mkdir(parents=True, exist_ok=True)
    for child in list(legacy.iterdir()):
        if child.name != ".system":
            _remove_path(child)
    commands = home / ".claude" / "commands"
    if commands.exists():
        for child in list(commands.iterdir()):
            _remove_path(child)


def install_plan(vault: Vault, profiles: Sequence[str]) -> Dict[str, Any]:
    platforms = {
        "codex": Path.home() / ".agents" / "skills",
        "claude": Path.home() / ".claude" / "skills",
    }
    operations = []
    notes = []
    for platform, destination in platforms.items():
        entries, platform_notes = vault.resolve_profile(profiles, platform)
        notes.extend(f"{platform}: {note}" for note in platform_notes)
        for entry in entries:
            operations.append(
                {
                    "platform": platform,
                    "skill_id": entry["id"],
                    "name": entry["name"],
                    "path": str(destination / entry["name"]),
                    "target": str((vault.root / entry["path"]).resolve()),
                }
            )
    current = load_data(vault.state_dir / "install-state.json", {"links": []}).get("links", [])
    current_by_path = {item.get("path"): item for item in current}
    desired_by_path = {item["path"]: item for item in operations}
    added = [item for path, item in desired_by_path.items() if path not in current_by_path]
    removed = [item for path, item in current_by_path.items() if path not in desired_by_path]
    changed = [
        item for path, item in desired_by_path.items()
        if path in current_by_path and current_by_path[path].get("target") != item.get("target")
    ]
    kept = [
        item for path, item in desired_by_path.items()
        if path in current_by_path and current_by_path[path].get("target") == item.get("target")
    ]
    return {
        "profiles": list(profiles),
        "operations": operations,
        "notes": notes,
        "changes": {"added": added, "removed": removed, "changed": changed, "kept": kept},
    }


def install(
    vault: Vault,
    profiles: Sequence[str],
    reset: bool = False,
    dry_run: bool = False,
    assume_yes: bool = False,
    backup_path: Optional[Path] = None,
) -> Dict[str, Any]:
    plan = install_plan(vault, profiles)
    if dry_run:
        return plan
    if reset and not confirm(
        "Back up and rebuild user-level Codex/Claude skills and Claude commands?", assume_yes
    ):
        raise VaultError("Install cancelled")
    backup = backup_path
    old_state = load_data(vault.state_dir / "install-state.json", {"links": []})
    managed_by_path = {
        str(item.get("path")): item
        for item in old_state.get("links", [])
        if item.get("path") and item.get("target")
    }
    created = []
    try:
        if reset:
            backup = backup or create_backup(vault)
            _reset_user_skill_dirs()
        desired_paths = {operation["path"] for operation in plan["operations"]}
        for link in old_state.get("links", []):
            path = Path(link["path"])
            if str(path) not in desired_paths and path.is_symlink() and path.resolve() == Path(link["target"]).resolve():
                path.unlink()

        for operation in plan["operations"]:
            destination = Path(operation["path"])
            target = Path(operation["target"])
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.is_symlink() and destination.resolve() == target.resolve():
                created.append(operation)
                continue
            if destination.exists() or destination.is_symlink():
                managed = managed_by_path.get(str(destination))
                if (
                    managed
                    and destination.is_symlink()
                    and destination.resolve() == Path(managed["target"]).resolve()
                ):
                    destination.unlink()
                else:
                    raise VaultError(
                        f"Destination is not managed by this install plan: {destination}. Use --reset or resolve it manually."
                    )
            destination.symlink_to(target, target_is_directory=True)
            created.append(operation)
    except Exception:
        for operation in created:
            path = Path(operation["path"])
            if path.is_symlink() and path.resolve() == Path(operation["target"]).resolve():
                path.unlink()
        if backup:
            _restore_backup_path(vault, backup)
        raise
    state = {
        "schema_version": 1,
        "installed_at": now_iso(),
        "profiles": list(profiles),
        "backup": str(backup) if backup else None,
        "links": [
            {
                "path": item["path"],
                "target": item["target"],
                "skill_id": item["skill_id"],
                "platform": item["platform"],
            }
            for item in created
        ],
    }
    write_data(vault.state_dir / "install-state.json", state)
    vault.activate_profiles(profiles)
    plan["backup"] = str(backup) if backup else None
    return plan


def uninstall(vault: Vault, assume_yes: bool = False) -> int:
    state_path = vault.state_dir / "install-state.json"
    state = load_data(state_path, {"links": []})
    links = state.get("links", [])
    if not links:
        return 0
    if not confirm(f"Remove {len(links)} Skills Vault-managed links?", assume_yes):
        raise VaultError("Uninstall cancelled")
    removed = 0
    for link in links:
        path = Path(link["path"])
        if path.is_symlink() and path.resolve() == Path(link["target"]).resolve():
            path.unlink()
            removed += 1
    write_data(state_path, {"schema_version": 1, "links": [], "uninstalled_at": now_iso()})
    return removed


def restore_backup(vault: Vault, backup_id: str, assume_yes: bool = False) -> Path:
    backup = vault.state_dir / "backups" / backup_id
    manifest_path = backup / "manifest.json"
    if not manifest_path.exists():
        raise VaultError(f"Backup not found: {backup_id}")
    if not confirm(f"Replace current user-level skill directories with backup {backup_id}?", assume_yes):
        raise VaultError("Restore cancelled")
    _restore_backup_path(vault, backup)
    write_data(vault.state_dir / "install-state.json", {"schema_version": 1, "links": [], "restored_at": now_iso(), "backup": backup_id})
    return backup


def _restore_backup_path(vault: Vault, backup: Path) -> None:
    manifest = load_data(backup / "manifest.json")
    for label, info in manifest["targets"].items():
        target = Path(info["path"])
        if not info.get("existed") and target.exists():
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
