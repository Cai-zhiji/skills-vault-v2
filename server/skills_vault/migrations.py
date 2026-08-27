from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .core import (
    Vault,
    VaultError,
    git,
    load_data,
    now_iso,
    parse_frontmatter,
    tree_fingerprint,
    valid_skill_name,
    write_data,
)


VAULT_SCHEMA_VERSION = 1
APP_VERSION = "2.1.0"


def _safe_directory(path: str | Path) -> Path:
    if not str(path).strip():
        raise VaultError("A directory path is required")
    candidate = Path(path).expanduser().resolve()
    if candidate == Path(candidate.anchor):
        raise VaultError("A filesystem root cannot be used as a Vault")
    return candidate


def _directory_size(root: Path) -> int:
    total = 0
    for path in root.rglob("*"):
        try:
            if path.is_file() and not path.is_symlink():
                total += path.stat().st_size
        except OSError:
            continue
    return total


def inspect_candidate(path: str | Path) -> Dict[str, Any]:
    root = _safe_directory(path)
    if not root.is_dir():
        return {
            "path": str(root),
            "kind": "invalid",
            "valid": False,
            "errors": ["目录不存在或不是文件夹"],
            "skills": [],
        }

    has_vault_layout = all(
        item.exists()
        for item in (root / "registry.yaml", root / "profiles", root / "my-skills")
    )
    vault_metadata: Dict[str, Any] = {}
    if (root / "vault.json").is_file():
        try:
            vault_metadata = json.loads((root / "vault.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            vault_metadata = {}

    rows: List[Dict[str, Any]] = []
    invalid: List[Dict[str, str]] = []
    skill_md_paths = sorted(
        item for item in root.rglob("SKILL.md") if ".git" not in item.parts
    )
    skill_directories = {item.parent.resolve() for item in skill_md_paths}
    for skill_md in skill_md_paths:
        try:
            metadata, _ = parse_frontmatter(
                skill_md.read_text(encoding="utf-8", errors="replace")
            )
        except OSError as exc:
            invalid.append({"path": str(skill_md.relative_to(root)), "reason": str(exc)})
            continue
        name = str(metadata.get("name") or skill_md.parent.name).strip()
        reasons = []
        if not valid_skill_name(name):
            reasons.append("名称必须使用小写字母、数字和连字符")
        if not str(metadata.get("description") or "").strip():
            reasons.append("缺少 description")
        nested = any(parent.resolve() in skill_directories for parent in skill_md.parent.parents if parent != root)
        row = {
            "name": name,
            "path": str(skill_md.parent.relative_to(root).as_posix()),
            "skill_md": str(skill_md.relative_to(root).as_posix()),
            "description": str(metadata.get("description") or "").strip(),
            "fingerprint": tree_fingerprint(skill_md.parent),
            "nested": nested,
            "valid": not reasons,
            "errors": reasons,
        }
        rows.append(row)
        if reasons:
            invalid.append({"path": row["skill_md"], "reason": "; ".join(reasons)})

    by_name: Dict[str, List[str]] = {}
    for row in rows:
        if row["valid"]:
            by_name.setdefault(row["name"], []).append(row["path"])
    conflicts = {name: paths for name, paths in by_name.items() if len(paths) > 1}
    git_repo = (root / ".git").exists()
    remote = git(root, "remote", "get-url", "origin", check=False) if git_repo else ""
    if has_vault_layout:
        kind = "vault" if vault_metadata else "web-v2-vault"
    elif git_repo:
        kind = "git-skills-repository"
    elif rows:
        kind = "skills-folder"
    else:
        kind = "invalid"
    errors = [] if kind != "invalid" else ["目录中没有可识别的 Skills Vault 或 SKILL.md"]
    return {
        "path": str(root),
        "kind": kind,
        "valid": kind != "invalid",
        "vault_schema": vault_metadata.get("schema_version", 0) if has_vault_layout else None,
        "git": git_repo,
        "git_remote": remote or None,
        "skills": rows,
        "skill_count": sum(1 for row in rows if row["valid"]),
        "invalid": invalid,
        "conflicts": conflicts,
        "nested_count": sum(bool(row["nested"]) for row in rows),
        "estimated_bytes": _directory_size(root),
        "errors": errors,
    }


def vault_create_plan(path: str | Path) -> Dict[str, Any]:
    target = _safe_directory(path)
    if target.exists() and (not target.is_dir() or any(target.iterdir())):
        raise VaultError(f"Vault destination must not exist or must be empty: {target}")
    relative_paths = [
        "vault.json",
        "registry.yaml",
        "lock.yaml",
        "annotations/skills.yaml",
        "profiles/ui-shared.yaml",
        "profiles/ui-codex.yaml",
        "profiles/ui-claude.yaml",
        "my-skills/",
        "docs/skill-guides/",
        "sources/",
        "catalog/",
        ".vault/",
    ]
    return {
        "destination": str(target),
        "schema_version": VAULT_SCHEMA_VERSION,
        "paths": relative_paths,
        "will_create_directory": not target.exists(),
    }


def create_vault(path: str | Path) -> Vault:
    plan = vault_create_plan(path)
    root = Path(plan["destination"])
    existed = root.exists()
    try:
        root.mkdir(parents=True, exist_ok=True)
        for relative in (
            "annotations",
            "profiles",
            "my-skills",
            "docs/skill-guides",
            "sources",
            "catalog",
            ".vault",
        ):
            (root / relative).mkdir(parents=True, exist_ok=True)
        write_data(
            root / "vault.json",
            {
                "schema_version": VAULT_SCHEMA_VERSION,
                "created_with": APP_VERSION,
                "created_at": now_iso(),
            },
        )
        write_data(root / "registry.yaml", {"schema_version": 1, "sources": {}})
        write_data(root / "lock.yaml", {"schema_version": 1, "sources": {}})
        write_data(root / "annotations" / "skills.yaml", {"schema_version": 1, "skills": {}})
        write_data(
            root / "profiles" / "ui-shared.yaml",
            {"schema_version": 1, "platforms": ["codex", "claude"], "include": []},
        )
        write_data(
            root / "profiles" / "ui-codex.yaml",
            {"schema_version": 1, "platform": "codex", "include": []},
        )
        write_data(
            root / "profiles" / "ui-claude.yaml",
            {"schema_version": 1, "platform": "claude", "include": []},
        )
        write_data(
            root / "profiles" / "ui-lux.yaml",
            {"schema_version": 1, "platform": "lux", "include": []},
        )
        write_data(
            root / ".vault" / "active-profiles.json",
            {"schema_version": 1, "profiles": ["ui-shared", "ui-codex", "ui-claude", "ui-lux"]},
        )
        vault = Vault(root)
        vault.scan()
        return vault
    except Exception:
        if root.exists():
            for child in root.iterdir():
                if child.is_dir() and not child.is_symlink():
                    shutil.rmtree(child)
                else:
                    child.unlink()
            if not existed:
                root.rmdir()
        raise


def import_plan(
    vault: Vault,
    source_path: str | Path,
    mode: str,
    source_id: Optional[str] = None,
    skill_names: Optional[Iterable[str]] = None,
) -> Dict[str, Any]:
    candidate = inspect_candidate(source_path)
    if not candidate["valid"] or candidate["kind"] in ("vault", "web-v2-vault"):
        raise VaultError("Import expects a Git Skills repository or a folder containing SKILL.md files")
    if mode not in ("personal", "source"):
        raise VaultError("Import mode must be personal or source")
    source_root = Path(candidate["path"])
    if source_root == vault.root or source_root in vault.root.parents or vault.root in source_root.parents:
        raise VaultError("Import source and destination Vault must not overlap")
    valid_rows = [row for row in candidate["skills"] if row["valid"] and row["name"] not in candidate["conflicts"]]
    requested = set(skill_names or [row["name"] for row in valid_rows])
    by_name = {row["name"]: row for row in valid_rows}
    missing = sorted(requested - set(by_name))
    if missing:
        raise VaultError(f"Requested Skills are unavailable or conflicted: {', '.join(missing)}")
    selected = [by_name[name] for name in sorted(requested)]
    conflicts: List[str] = []
    if mode == "personal":
        conflicts = [row["name"] for row in selected if (vault.root / "my-skills" / row["name"]).exists()]
        actions = [
            {
                "name": row["name"],
                "source": str(Path(candidate["path"]) / row["path"]),
                "destination": str(vault.root / "my-skills" / row["name"]),
                "fingerprint": row["fingerprint"],
            }
            for row in selected
        ]
    else:
        normalized_id = str(source_id or "").strip().lower()
        if not valid_skill_name(normalized_id):
            raise VaultError("Source ID must use lowercase letters, digits, and hyphens")
        if normalized_id in vault.registry.get("sources", {}):
            conflicts.append(normalized_id)
        destination = vault.root / "sources" / normalized_id
        if destination.exists():
            conflicts.append(str(destination))
        actions = [{"source": candidate["path"], "destination": str(destination)}]
        source_id = normalized_id
    return {
        "mode": mode,
        "source_id": source_id,
        "candidate": candidate,
        "skills": selected,
        "actions": actions,
        "conflicts": sorted(set(conflicts)),
        "blocked": bool(conflicts),
    }


def apply_import(vault: Vault, plan: Dict[str, Any]) -> Dict[str, Any]:
    if plan.get("blocked"):
        raise VaultError("Import plan has unresolved conflicts")
    created: List[Path] = []
    old_registry = json.loads(json.dumps(vault.registry))
    old_lock = json.loads(json.dumps(load_data(vault.lock_path)))
    try:
        if plan["mode"] == "personal":
            for action in plan["actions"]:
                destination = Path(action["destination"])
                shutil.copytree(Path(action["source"]), destination, symlinks=True)
                created.append(destination)
        else:
            action = plan["actions"][0]
            source_root = Path(action["source"])
            destination = Path(action["destination"])
            shutil.copytree(source_root, destination, symlinks=True)
            created.append(destination)
            source_id = str(plan["source_id"])
            remote = plan["candidate"].get("git_remote")
            kind = "git" if plan["candidate"].get("git") and remote else "local-copy"
            source = {
                "kind": kind,
                "url": remote or f"local-import:{source_root}",
                "path": destination.relative_to(vault.root).as_posix(),
                "trust": "unreviewed",
                "license": "unknown",
                "classify": [{"pattern": "**/SKILL.md", "as": "published"}],
            }
            if kind == "git":
                source.update({"branch": git(destination, "branch", "--show-current", check=False) or "main", "track": "branch"})
            else:
                source["update_policy"] = "self-managed"
            registry = vault.registry
            registry.setdefault("sources", {})[source_id] = source
            write_data(vault.registry_path, registry)
            vault.update_lock()
        catalog = vault.scan()
    except Exception:
        for path in reversed(created):
            shutil.rmtree(path, ignore_errors=True)
        write_data(vault.registry_path, old_registry)
        write_data(vault.lock_path, old_lock)
        raise
    prefix = "my" if plan["mode"] == "personal" else str(plan["source_id"])
    imported = [f"{prefix}/{item['name']}" for item in plan["skills"]]
    return {"mode": plan["mode"], "source_id": plan.get("source_id"), "skills": imported}


def web_v2_migration_plan(source_path: str | Path, destination: str | Path) -> Dict[str, Any]:
    candidate = inspect_candidate(source_path)
    if candidate["kind"] not in ("vault", "web-v2-vault"):
        raise VaultError("Migration source is not a Skills Vault")
    create_plan = vault_create_plan(destination)
    source = Path(candidate["path"])
    target = Path(create_plan["destination"])
    if source == target or source in target.parents or target in source.parents:
        raise VaultError("Migration source and destination must not overlap")
    facts = [
        relative
        for relative in (
            "registry.yaml",
            "lock.yaml",
            "profiles",
            "annotations",
            "my-skills",
            "docs/skill-guides",
            "sources",
        )
        if (source / relative).exists()
    ]
    history = [
        relative
        for relative in (
            ".vault/transactions",
            ".vault/backups",
            ".vault/trash",
            "catalog/updates",
        )
        if (source / relative).exists()
    ]
    return {
        "source": str(source),
        "destination": create_plan["destination"],
        "destination_existed": target.exists(),
        "candidate": candidate,
        "facts": facts,
        "legacy_history": history,
        "excluded": [
            "catalog/catalog.json",
            ".vault/run",
            ".vault/logs",
            ".vault/tokens",
            ".vault/install-state.json",
        ],
    }


def apply_web_v2_migration(plan: Dict[str, Any]) -> Dict[str, Any]:
    source = Path(plan["source"]).resolve()
    destination = Path(plan["destination"]).resolve()
    create_vault(destination)
    try:
        for relative in plan.get("facts", []):
            origin = source / relative
            target = destination / relative
            if target.exists():
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink()
            target.parent.mkdir(parents=True, exist_ok=True)
            if origin.is_dir():
                shutil.copytree(origin, target, symlinks=True)
            else:
                shutil.copy2(origin, target)
        legacy_root = destination / ".vault" / "legacy" / now_iso().replace(":", "-")
        for relative in plan.get("legacy_history", []):
            origin = source / relative
            target = legacy_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if origin.is_dir():
                shutil.copytree(origin, target, symlinks=True)
            else:
                shutil.copy2(origin, target)
        write_data(
            destination / "vault.json",
            {
                "schema_version": VAULT_SCHEMA_VERSION,
                "created_with": APP_VERSION,
                "created_at": now_iso(),
                "migrated_at": now_iso(),
                "migrated_from": str(source),
            },
        )
        vault = Vault(destination)
        catalog = vault.scan()
    except Exception:
        if plan.get("destination_existed"):
            for child in destination.iterdir() if destination.exists() else []:
                if child.is_dir() and not child.is_symlink():
                    shutil.rmtree(child)
                else:
                    child.unlink()
        else:
            shutil.rmtree(destination, ignore_errors=True)
        raise
    migrated = {row["id"]: row["fingerprint"] for row in catalog.get("skills", [])}
    expected = {
        f"my/{row['name']}": row["fingerprint"]
        for row in plan["candidate"].get("skills", [])
        if row["valid"] and row["path"].startswith("my-skills/")
    }
    return {
        "destination": str(destination),
        "skill_count": len(migrated),
        "personal_fingerprints_match": all(migrated.get(key) == value for key, value in expected.items()),
        "legacy_history": str(next((destination / ".vault" / "legacy").iterdir(), "")) if (destination / ".vault" / "legacy").exists() else None,
    }
