from __future__ import annotations

import argparse
import difflib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from .core import Vault, VaultError, git, load_data, now_iso, write_data
from .ops import (
    apply_updates,
    doctor,
    install,
    lint_vault,
    restore_backup,
    rollback_source,
    save_update_report,
    source_audit,
    uninstall,
    update_plan,
)
from .services import (
    _validate_git_source,
    skills_cli_source_apply,
    skills_cli_source_preview,
)
from .source_input import parse_source_input


def default_root() -> Path:
    return Path(__file__).resolve().parents[1]


def print_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def print_update_rows(rows: List[Dict[str, Any]]) -> None:
    for row in rows:
        print(f"{row['source_id']}: {row['status']}")
        if row.get("head") and row.get("target") and row["head"] != row["target"]:
            print(f"  {row['head'][:12]} -> {row['target'][:12]}")
            print(f"  commits={len(row.get('commits', []))} files={len(row.get('changes', []))}")
            if row.get("risk_signals"):
                print(f"  risks={','.join(row['risk_signals'])}")


def _source_arguments(values: Sequence[str]) -> tuple[Optional[str], str]:
    if len(values) == 2:
        return values[0], values[1]
    if not values:
        raise VaultError("Missing source URL or command")
    return None, " ".join(values)


def cmd_source(vault: Vault, args: argparse.Namespace) -> int:
    if args.source_command in ("list", "status"):
        rows = vault.source_rows()
        if args.json:
            print_json(rows)
        else:
            for row in rows:
                commit = row.get("commit") or "missing"
                flags = []
                if row.get("dirty"):
                    flags.append("dirty")
                if row.get("locked") and row.get("locked") != row.get("commit"):
                    flags.append("lock-mismatch")
                print(
                    f"{row['id']:<20} {commit[:12]:<12} {(row.get('branch') or 'self-managed'):<12} "
                    f"kind={row.get('kind', 'git')} trust={row['trust']} license={row['license']} {' '.join(flags)}"
                )
        return 0
    if args.source_command == "add":
        source_id, source_input = _source_arguments(args.inputs)
        try:
            spec = parse_source_input(source_input, "git", source_id, args.branch)
            source_id, source_url = _validate_git_source(spec.source_id, spec.source_url)
        except ValueError as exc:
            raise VaultError(str(exc)) from exc
        registry = vault.registry
        if source_id in registry["sources"]:
            raise VaultError(f"Source ID already exists: {source_id}")
        destination = vault.root / "sources" / source_id
        if args.adopt:
            if not destination.is_dir():
                raise VaultError(f"Adopt target is not a directory: {destination}")
            if not (destination / ".git").is_dir():
                raise VaultError(f"Adopt target is not a git repository: {destination}")
            dirty = [line for line in git(destination, "status", "--porcelain", check=False).splitlines() if len(line) >= 4]
            if dirty:
                raise VaultError(f"Cannot adopt dirty repository: {destination}\nUncommitted changes:\n" + "\n".join(dirty))
            existing_remote = git(destination, "remote", "get-url", "origin", check=False)
            if existing_remote:
                # The adopted clone may use the same URL under a different transport.
                git(destination, "remote", "set-url", "origin", source_url)
            else:
                git(destination, "remote", "add", "origin", source_url)
            git(destination, "fetch", "--prune", "origin")
            git(destination, "checkout", "-B", spec.branch, f"origin/{spec.branch}")
        elif destination.exists():
            raise VaultError(f"Destination exists: {destination}")
        else:
            git(vault.root, "clone", "--branch", spec.branch, "--", source_url, str(destination))
        registry["sources"][source_id] = {
            "kind": "git",
            "url": source_url,
            "path": destination.relative_to(vault.root).as_posix(),
            "branch": spec.branch,
            "track": "branch",
            "trust": "unreviewed",
            "license": "unknown",
            "reviewed_at": None,
            "classify": [{"pattern": "**/SKILL.md", "as": "unknown"}],
        }
        write_data(vault.registry_path, registry)
        vault.update_lock()
        vault.scan()
        print(f"Added unreviewed source {source_id}; cataloged but not enabled.")
        print_json(source_audit(vault, source_id))
        return 0
    if args.source_command == "add-skills":
        source_id, source_input = _source_arguments(args.inputs)
        preview = skills_cli_source_preview(vault, source_id, source_input, args.full_depth, args.skill)
        print(f"Discovered {len(preview.get('skills', []))} skills from {source_input}.")
        result = skills_cli_source_apply(vault, preview["preview_token"])
        print(f"Added self-managed skills-cli source {preview['source_id']}.")
        print_json(result)
        return 0
    if args.source_command == "review":
        registry = vault.registry
        if args.id not in registry["sources"]:
            raise VaultError(f"Unknown source: {args.id}")
        source = registry["sources"][args.id]
        previous = {"trust": source.get("trust", "unreviewed"), "license": source.get("license", "unknown")}
        if args.trust is not None:
            if args.trust not in ("unreviewed", "reviewed", "trusted"):
                raise VaultError("trust must be one of: unreviewed, reviewed, trusted")
            source["trust"] = args.trust
        if args.license is not None:
            source["license"] = args.license
        if args.trust in ("reviewed", "trusted") or source.get("trust") in ("reviewed", "trusted"):
            source["reviewed_at"] = now_iso()[:10]
        write_data(vault.registry_path, registry)
        print_json(
            {
                "source_id": args.id,
                "previous": previous,
                "trust": source.get("trust", "unreviewed"),
                "license": source.get("license", "unknown"),
                "reviewed_at": source.get("reviewed_at"),
            }
        )
        return 0
    if args.source_command == "audit":
        source_ids = args.ids or list(vault.registry["sources"])
        rows = [source_audit(vault, source_id) for source_id in source_ids]
        print_json(rows)
        return 1 if any(row["warnings"] for row in rows) else 0
    if args.source_command in ("hold", "resume", "pin", "unpin"):
        registry = vault.registry
        if args.id not in registry["sources"]:
            raise VaultError(f"Unknown source: {args.id}")
        source = registry["sources"][args.id]
        if vault.source_kind(source) != "git" and args.source_command in ("pin", "unpin"):
            raise VaultError("Pinning applies only to strict Git sources")
        if args.source_command == "hold":
            source["hold"] = True
        elif args.source_command == "resume":
            source.pop("hold", None)
        elif args.source_command == "pin":
            repo = vault.source_path(source)
            resolved = git(repo, "rev-parse", f"{args.commit}^{{commit}}", check=False)
            if not resolved:
                raise VaultError(f"Commit is not available: {args.commit}")
            source["pin"] = resolved
        else:
            source.pop("pin", None)
        write_data(vault.registry_path, registry)
        print(f"Updated source policy for {args.id}.")
        return 0
    raise VaultError("Missing source subcommand")


def cmd_scan(vault: Vault, args: argparse.Namespace) -> int:
    catalog = vault.scan()
    print(
        f"Scanned {catalog['counts']['skills']} skills: {catalog['counts']['published']} published, "
        f"{catalog['counts']['conflict_groups']} conflict groups."
    )
    print(vault.root / "catalog" / "skills.md")
    return 0


def _filtered_entries(vault: Vault, query: Optional[str] = None) -> List[Dict[str, Any]]:
    entries = vault.catalog()["skills"]
    if not query:
        return entries
    needle = query.lower()
    result = []
    for entry in entries:
        haystack = " ".join(
            str(entry.get(field) or "")
            for field in ("id", "name", "description", "title_zh", "summary_zh", "recommended_for")
        ).lower()
        if needle in haystack:
            result.append(entry)
    return result


def cmd_list(vault: Vault, args: argparse.Namespace) -> int:
    entries = _filtered_entries(vault)
    if args.classification:
        entries = [entry for entry in entries if entry["classification"] == args.classification]
    if args.source:
        entries = [entry for entry in entries if entry["source_id"] == args.source]
    if args.json:
        print_json(entries)
    else:
        for entry in entries:
            print(
                f"{entry['id']:<48} {entry['classification']:<12} "
                f"{entry['compatibility']['level']:<8} {entry.get('title_zh') or entry['description']}"
            )
    return 0


def cmd_search(vault: Vault, args: argparse.Namespace) -> int:
    entries = _filtered_entries(vault, args.query)
    if args.json:
        print_json(entries)
    else:
        for entry in entries:
            print(f"{entry['id']}: {entry.get('title_zh') or entry['description']}")
    return 0 if entries else 1


def cmd_show(vault: Vault, args: argparse.Namespace) -> int:
    matches = [entry for entry in vault.catalog()["skills"] if entry["id"] == args.skill_id]
    if not matches:
        raise VaultError(f"Skill not found: {args.skill_id}")
    if len(matches) > 1:
        raise VaultError(f"Stable ID is ambiguous: {args.skill_id}")
    print_json(matches[0])
    return 0


def _one_skill(vault: Vault, skill_id: str) -> Dict[str, Any]:
    matches = [entry for entry in vault.catalog()["skills"] if entry["id"] == skill_id]
    if len(matches) != 1:
        raise VaultError(f"Expected one skill for {skill_id}, found {len(matches)}")
    return matches[0]


def cmd_diff(vault: Vault, args: argparse.Namespace) -> int:
    left = _one_skill(vault, args.left)
    right = _one_skill(vault, args.right)
    left_path = vault.root / left["path"] / "SKILL.md"
    right_path = vault.root / right["path"] / "SKILL.md"
    difference = difflib.unified_diff(
        left_path.read_text(encoding="utf-8", errors="replace").splitlines(),
        right_path.read_text(encoding="utf-8", errors="replace").splitlines(),
        fromfile=left["id"],
        tofile=right["id"],
        lineterm="",
    )
    output = "\n".join(difference)
    print(output or "No SKILL.md differences.")
    return 1 if output else 0


def cmd_status(vault: Vault, args: argparse.Namespace) -> int:
    catalog = vault.catalog()
    source_rows = vault.source_rows()
    install_state = load_data(vault.state_dir / "install-state.json", {"links": []})
    payload = {
        "root": str(vault.root),
        "active_profiles": vault.active_profiles(),
        "catalog": catalog["counts"],
        "sources": source_rows,
        "managed_links": len(install_state.get("links", [])),
        "last_backup": install_state.get("backup"),
        "derived_drift": vault.drift_rows(),
    }
    if args.json:
        print_json(payload)
    else:
        print(f"root: {payload['root']}")
        print(f"profiles: {', '.join(payload['active_profiles'])}")
        print(
            f"catalog: {catalog['counts']['skills']} skills, {catalog['counts']['published']} published, "
            f"{catalog['counts']['conflict_groups']} conflict groups"
        )
        print(f"managed links: {payload['managed_links']}")
        print(f"last backup: {payload['last_backup'] or 'none'}")
        for row in source_rows:
            flags = []
            if row.get("dirty"):
                flags.append("dirty")
            if row.get("kind", "git") == "git" and row.get("commit") != row.get("locked"):
                flags.append("lock-mismatch")
            print(f"source {row['id']}: {(row.get('commit') or 'missing')[:12]} {' '.join(flags) or 'ok'}")
    return 1 if any(row.get("dirty") or (row.get("kind", "git") == "git" and row.get("commit") != row.get("locked")) for row in source_rows) else 0


def cmd_update(vault: Vault, args: argparse.Namespace) -> int:
    rows = update_plan(vault, args.source)
    print_update_rows(rows)
    if args.check:
        json_path, md_path = save_update_report(vault, rows, applied=False)
        print(f"Report: {md_path}")
        return 2 if any(row["status"] == "fast-forward" for row in rows) else 0
    changed = apply_updates(vault, rows, assume_yes=args.yes)
    print("Updated and validated." if changed else "All selected sources are up to date.")
    return 0


def cmd_derive(vault: Vault, args: argparse.Namespace) -> int:
    destination = vault.derive(args.skill_id, args.name)
    print(f"Derived {args.skill_id} -> {destination}")
    return 0


def cmd_drift(vault: Vault, args: argparse.Namespace) -> int:
    rows = vault.drift_rows()
    if args.json:
        print_json(rows)
    else:
        for row in rows:
            print(f"{row['skill']}: {row['status']}")
    return 1 if any(row["status"] in ("upstream-changed", "conflict-review", "missing-source") for row in rows) else 0


def cmd_profile(vault: Vault, args: argparse.Namespace) -> int:
    if args.profile_command == "list":
        active = set(vault.active_profiles())
        for name, path in vault.profile_files().items():
            data = load_data(path)
            print(f"{'*' if name in active else ' '} {name:<14} {data.get('description', '')}")
        return 0
    if args.profile_command == "activate":
        vault.activate_profiles(args.profiles)
        print(f"Active profiles: {', '.join(args.profiles)}")
        return 0
    raise VaultError("Missing profile subcommand")


def cmd_install(vault: Vault, args: argparse.Namespace) -> int:
    profiles = args.profiles or vault.active_profiles()
    result = install(
        vault,
        profiles,
        reset=args.reset,
        dry_run=args.dry_run,
        assume_yes=args.yes,
    )
    for note in result.get("notes", []):
        print(f"note: {note}")
    for operation in result["operations"]:
        print(f"{operation['platform']}: {operation['name']} -> {operation['target']}")
    if result.get("backup"):
        print(f"Backup: {result['backup']}")
    print(f"{'Would install' if args.dry_run else 'Installed'} {len(result['operations'])} links.")
    return 0


def cmd_lint(vault: Vault, args: argparse.Namespace) -> int:
    errors, warnings = lint_vault(vault)
    for warning in warnings:
        print(f"WARN: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    print(f"lint: {len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


def cmd_doctor(vault: Vault, args: argparse.Namespace) -> int:
    errors, messages = doctor(vault)
    for message in messages:
        prefix = "OK" if ":" in message and not message.startswith(("Optional", "Unreviewed", "Broken")) else "WARN"
        print(f"{prefix}: {message}")
    for error in errors:
        print(f"ERROR: {error}")
    print(f"doctor: {len(errors)} errors")
    return 1 if errors else 0


def cmd_rollback(vault: Vault, args: argparse.Namespace) -> int:
    commit = rollback_source(vault, args.source_id, args.to, args.yes)
    print(f"{args.source_id} rolled back to {commit}")
    return 0


def cmd_uninstall(vault: Vault, args: argparse.Namespace) -> int:
    count = uninstall(vault, args.yes)
    print(f"Removed {count} managed links.")
    return 0


def cmd_restore(vault: Vault, args: argparse.Namespace) -> int:
    path = restore_backup(vault, args.backup_id, args.yes)
    print(f"Restored {path}")
    return 0


def cmd_used(vault: Vault, args: argparse.Namespace) -> int:
    catalog_ids = {entry["id"] for entry in vault.catalog()["skills"]}
    if args.skill_id not in catalog_ids:
        raise VaultError(f"Skill not found: {args.skill_id}")
    path = vault.state_dir / "usage.json"
    data = load_data(path, {"schema_version": 1, "skills": {}})
    record = data["skills"].setdefault(args.skill_id, {"count": 0})
    record["count"] += 1
    record["last_used_at"] = now_iso()
    if args.rating is not None:
        record["rating"] = args.rating
    if args.note:
        record["note"] = args.note
    write_data(path, data)
    print_json(record)
    return 0


def cmd_ui(vault: Vault, args: argparse.Namespace) -> int:
    server = vault.root / "web" / "server.py"
    command = [sys.executable, str(server), "--host", args.host, "--port", str(args.port)]
    return subprocess.call(command, cwd=str(vault.root))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vault", description="Manage shared Codex and Claude Code skills")
    parser.add_argument("--root", type=Path, default=default_root(), help="Skills Vault root")
    sub = parser.add_subparsers(dest="command", required=True)

    source = sub.add_parser("source")
    source_sub = source.add_subparsers(dest="source_command", required=True)
    for name in ("list", "status"):
        item = source_sub.add_parser(name)
        item.add_argument("--json", action="store_true")
    add = source_sub.add_parser("add")
    add.add_argument("inputs", nargs="+")
    add.add_argument("--branch", default="main")
    add.add_argument("--adopt", action="store_true", help="Adopt an existing clean git checkout at sources/<id> instead of cloning fresh")
    add_skills = source_sub.add_parser("add-skills")
    add_skills.add_argument("inputs", nargs="+")
    add_skills.add_argument("--full-depth", action="store_true")
    add_skills.add_argument("--skill", nargs="+", help="Only install the named skills")
    audit = source_sub.add_parser("audit")
    audit.add_argument("ids", nargs="*")
    review = source_sub.add_parser("review")
    review.add_argument("id")
    review.add_argument("--trust", choices=["unreviewed", "reviewed", "trusted"])
    review.add_argument("--license")
    for name in ("hold", "resume", "unpin"):
        item = source_sub.add_parser(name)
        item.add_argument("id")
    pin = source_sub.add_parser("pin")
    pin.add_argument("id")
    pin.add_argument("commit")

    sub.add_parser("scan")
    list_parser = sub.add_parser("list")
    list_parser.add_argument("--classification")
    list_parser.add_argument("--source")
    list_parser.add_argument("--json", action="store_true")
    search = sub.add_parser("search")
    search.add_argument("query")
    search.add_argument("--json", action="store_true")
    show = sub.add_parser("show")
    show.add_argument("skill_id")
    diff = sub.add_parser("diff")
    diff.add_argument("left")
    diff.add_argument("right")
    status = sub.add_parser("status")
    status.add_argument("--json", action="store_true")

    update = sub.add_parser("update")
    update.add_argument("--check", action="store_true")
    update.add_argument("--source", action="append")
    update.add_argument("--yes", action="store_true")
    rollback = sub.add_parser("rollback")
    rollback.add_argument("source_id")
    rollback.add_argument("--to")
    rollback.add_argument("--yes", action="store_true")

    derive = sub.add_parser("derive")
    derive.add_argument("skill_id")
    derive.add_argument("--name", required=True)
    drift = sub.add_parser("drift")
    drift.add_argument("--json", action="store_true")

    profile = sub.add_parser("profile")
    profile_sub = profile.add_subparsers(dest="profile_command", required=True)
    profile_sub.add_parser("list")
    activate = profile_sub.add_parser("activate")
    activate.add_argument("profiles", nargs="+")

    install_parser = sub.add_parser("install")
    install_parser.add_argument("--profiles", nargs="+")
    install_parser.add_argument("--reset", action="store_true")
    install_parser.add_argument("--dry-run", action="store_true")
    install_parser.add_argument("--yes", action="store_true")
    uninstall_parser = sub.add_parser("uninstall")
    uninstall_parser.add_argument("--yes", action="store_true")
    restore = sub.add_parser("restore")
    restore.add_argument("backup_id")
    restore.add_argument("--yes", action="store_true")

    sub.add_parser("lint")
    sub.add_parser("doctor")
    used = sub.add_parser("used")
    used.add_argument("skill_id")
    used.add_argument("--rating", type=int, choices=range(1, 6))
    used.add_argument("--note")
    ui = sub.add_parser("ui", help="start the local Skills Vault web UI")
    ui.add_argument("--host", default="127.0.0.1")
    ui.add_argument("--port", type=int, default=8765)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    vault = Vault(args.root)
    handlers = {
        "source": cmd_source,
        "scan": cmd_scan,
        "list": cmd_list,
        "search": cmd_search,
        "show": cmd_show,
        "diff": cmd_diff,
        "status": cmd_status,
        "update": cmd_update,
        "rollback": cmd_rollback,
        "derive": cmd_derive,
        "drift": cmd_drift,
        "profile": cmd_profile,
        "install": cmd_install,
        "uninstall": cmd_uninstall,
        "restore": cmd_restore,
        "lint": cmd_lint,
        "doctor": cmd_doctor,
        "used": cmd_used,
        "ui": cmd_ui,
    }
    try:
        return handlers[args.command](vault, args)
    except VaultError as exc:
        print(f"vault: error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("vault: interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
