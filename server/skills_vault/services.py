"""Structured application services shared by the CLI and local web UI."""
from __future__ import annotations

import datetime as dt
import difflib
import hashlib
import ipaddress
import json
import re
import secrets
import shutil
import tempfile
import urllib.parse
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from .core import (
    Vault,
    VaultError,
    git,
    load_data,
    now_iso,
    parse_frontmatter,
    run,
    tree_fingerprint,
    write_data,
)
from .ops import apply_updates, create_backup, install, install_plan, restore_backup, update_plan
from .skills_cli import discover as discover_skills_cli_source
from .skills_cli import install as install_skills_cli_source


MANAGED_PROFILES = ("ui-shared", "ui-codex", "ui-claude")


class ServiceError(VaultError):
    def __init__(self, code: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.details = details or {}


def transaction_id(prefix: str = "tx") -> str:
    stamp = dt.datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")
    return f"{prefix}_{stamp}_{secrets.token_hex(4)}"


def _record_transaction(vault: Vault, tx_id: str, payload: Dict[str, Any]) -> None:
    write_data(vault.state_dir / "transactions" / f"{tx_id}.json", {"transaction_id": tx_id, "created_at": now_iso(), **payload})


def _state_fingerprint(vault: Vault) -> str:
    files = [
        vault.registry_path,
        vault.lock_path,
        vault.annotations_path,
        vault.deleted_skills_path,
        vault.source_policies_path,
        vault.state_dir / "active-profiles.json",
        vault.state_dir / "install-state.json",
        *vault.profile_files().values(),
    ]
    digest = hashlib.sha256()
    for path in files:
        digest.update(str(path).encode())
        digest.update(path.read_bytes() if path.exists() else b"missing")
    digest.update(vault.catalog().get("fingerprint", "").encode())
    return digest.hexdigest()


def _guide_path(vault: Vault, skill_id: str) -> Path:
    return vault.root / "docs" / "skill-guides" / f"{skill_id.replace('/', '--')}.md"


def skill_guide_template(skill: Dict[str, Any]) -> str:
    """Return the canonical eight-section guide format for a personal Skill."""
    name = str(skill.get("name") or "Skill")
    description = str(skill.get("summary_zh") or skill.get("description") or "填写这个 Skill 要解决的问题。")
    return "\n".join(
        [
            f"# {name} 使用说明",
            "",
            "## 1. 定位",
            "",
            description,
            "",
            "## 2. 何时使用",
            "",
            "- 描述触发这个 Skill 的任务、场景或关键词。",
            "",
            "## 3. 不适用",
            "",
            "- 写明应改用其他方法或 Skill 的情况。",
            "",
            "## 4. 前置条件",
            "",
            "- 列出必须准备的文件、权限、工具或上下文。",
            "",
            "## 5. 标准流程",
            "",
            "1. 写出从输入到完成的关键步骤。",
            "2. 说明每一步需要检查的结果。",
            "",
            "## 6. 输出与验收",
            "",
            "- 说明成功后应该交付什么，以及如何确认结果正确。",
            "",
            "## 7. 风险与边界",
            "",
            "- 写明可能修改的数据、需要确认的动作和禁止自动执行的内容。",
            "",
            "## 8. 维护记录",
            "",
            "- 记录重要的使用约定、已知限制或后续改进方向。",
            "",
        ]
    )


def save_skill_guide(vault: Vault, skill_id: str, markdown: str) -> Dict[str, Any]:
    entries = [item for item in vault.catalog().get("skills", []) if item.get("id") == skill_id]
    if not entries:
        raise ServiceError("not_found", "Skill not found")
    if entries[0].get("source_id") != "my":
        raise ServiceError("guide_not_personal", "说明文档只能在个人或派生 Skill 上编辑")
    content = str(markdown).strip()
    if len(content) < 16:
        raise ServiceError("invalid_guide", "说明文档至少需要 16 个字符")
    if len(content) > 100_000:
        raise ServiceError("guide_too_large", "说明文档不能超过 100,000 个字符")
    path = _guide_path(vault, skill_id)
    created = not path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with open(fd, "w", encoding="utf-8", closefd=True) as handle:
            handle.write(content + "\n")
        Path(tmp_name).replace(path)
    finally:
        Path(tmp_name).unlink(missing_ok=True)
    tx = transaction_id("guide")
    _record_transaction(
        vault,
        tx,
        {
            "operation": "skill.guide.save",
            "status": "complete",
            "skill_id": skill_id,
            "path": str(path.relative_to(vault.root)),
            "created": created,
        },
    )
    return {
        "transaction_id": tx,
        "status": "saved",
        "skill_id": skill_id,
        "path": str(path.relative_to(vault.root)),
        "created": created,
    }


def _validate_external_source(source_id: str, source_url: str) -> tuple[str, str]:
    normalized_id = str(source_id).strip().lower()
    normalized_url = str(source_url).strip()
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", normalized_id):
        raise ServiceError("invalid_source_id", "来源 ID 只能使用小写字母、数字和连字符")
    parsed = urllib.parse.urlparse(normalized_url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ServiceError("invalid_source_url", "外部来源必须使用完整的 http:// 或 https:// URL")
    if parsed.username or parsed.password:
        raise ServiceError("invalid_source_url", "来源 URL 不能包含用户名或密码")
    hostname = parsed.hostname.lower()
    if hostname == "localhost":
        raise ServiceError("invalid_source_url", "来源 URL 不能指向本机")
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        address = None
    if address and (address.is_private or address.is_loopback or address.is_link_local or address.is_reserved):
        raise ServiceError("invalid_source_url", "来源 URL 不能指向本机或私有网络地址")
    return normalized_id, normalized_url


def _validate_git_source(source_id: str, source_url: str) -> tuple[str, str]:
    """Validate a git source URL, accepting https and scp-style ssh URLs."""
    normalized_id = str(source_id).strip().lower()
    normalized_url = str(source_url).strip()
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", normalized_id):
        raise ServiceError("invalid_source_id", "来源 ID 只能使用小写字母、数字和连字符")
    scp = re.fullmatch(r"([^@\s]+)@([^:\s]+):(.+)", normalized_url)
    if scp:
        hostname = scp.group(2).lower()
        if hostname == "localhost":
            raise ServiceError("invalid_source_url", "来源 URL 不能指向本机")
        return normalized_id, normalized_url
    parsed = urllib.parse.urlparse(normalized_url)
    if parsed.scheme not in ("http", "https", "git", "ssh") or not parsed.hostname:
        raise ServiceError("invalid_source_url", "Git 来源必须使用 https://、git://、ssh:// 或 git@host:path 形式")
    if parsed.username or parsed.password:
        raise ServiceError("invalid_source_url", "来源 URL 不能包含用户名或密码")
    hostname = parsed.hostname.lower()
    if hostname == "localhost":
        raise ServiceError("invalid_source_url", "来源 URL 不能指向本机")
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        address = None
    if address and (address.is_private or address.is_loopback or address.is_link_local or address.is_reserved):
        raise ServiceError("invalid_source_url", "来源 URL 不能指向本机或私有网络地址")
    return normalized_id, normalized_url


def skills_cli_source_preview(
    vault: Vault,
    source_id: str,
    source_url: str,
    full_depth: bool = False,
    skills: Optional[List[str]] = None,
) -> Dict[str, Any]:
    source_id, source_url = _validate_external_source(source_id, source_url)
    if source_id in vault.registry.get("sources", {}):
        raise ServiceError("already_exists", f"来源已存在：{source_id}")
    destination = vault.root / "sources" / "skills-cli" / source_id
    if destination.exists():
        raise ServiceError("already_exists", f"来源目录已存在：{destination}")
    try:
        discovery = discover_skills_cli_source(source_url, bool(full_depth))
    except VaultError as exc:
        raise ServiceError("source_discovery_failed", str(exc)) from exc
    available_skills = list(discovery.get("skills", []))
    requested_skills = list(
        dict.fromkeys(str(name).strip() for name in (skills or []) if str(name).strip())
    )
    unknown_skills = [name for name in requested_skills if name not in available_skills]
    if unknown_skills:
        raise ServiceError(
            "unknown_skill",
            f"来源中不存在这些 Skills：{', '.join(unknown_skills)}",
            {"available_skills": available_skills},
        )
    selected_skills = requested_skills or available_skills
    tx = transaction_id("source_add")
    plan = {
        "transaction_id": tx,
        "source_id": source_id,
        "source_url": source_url,
        "kind": "skills-cli",
        "update_policy": "self-managed",
        "full_depth": bool(full_depth),
        "destination": str(destination),
        "available_skills": available_skills,
        "skills": selected_skills,
        "notes": [
            "Skill 文件安装到 Vault 专用目录，不直接写入用户级 Agent 目录。",
            "后续更新交给 npx skills update；Vault 记录观测摘要，但不强制锁定其版本。",
            "来源初始状态为 unreviewed，需审核后再启用。",
        ],
    }
    plan["preview_token"] = _issue_token(vault, "source.skills-cli.add", {"plan": plan})
    return plan


def skills_cli_source_apply(vault: Vault, token: str) -> Dict[str, Any]:
    payload = _consume_token(vault, token, "source.skills-cli.add")
    plan = payload.get("plan") or {}
    source_id, source_url = _validate_external_source(plan.get("source_id", ""), plan.get("source_url", ""))
    registry = vault.registry
    if source_id in registry.get("sources", {}):
        raise ServiceError("already_exists", f"来源已存在：{source_id}")
    destination = vault.root / "sources" / "skills-cli" / source_id
    if destination.exists():
        raise ServiceError("already_exists", f"来源目录已存在：{destination}")
    old_registry = json.loads(json.dumps(registry))
    old_lock = load_data(vault.lock_path)
    tx = plan.get("transaction_id") or transaction_id("source_add")
    try:
        install_result = install_skills_cli_source(
            source_url,
            destination,
            bool(plan.get("full_depth")),
            plan.get("skills") or None,
        )
        registry.setdefault("sources", {})[source_id] = {
            "kind": "skills-cli",
            "url": source_url,
            "path": destination.relative_to(vault.root).as_posix(),
            "skill_root": ".agents/skills",
            "update_policy": "self-managed",
            "full_depth": bool(plan.get("full_depth")),
            "selected_skills": list(plan.get("skills") or []),
            "trust": "unreviewed",
            "license": "per-skill",
            "reviewed_at": None,
            "classify": [
                {"pattern": "*/SKILL.md", "as": "published"},
                {"pattern": "**/SKILL.md", "as": "unknown"},
            ],
        }
        write_data(vault.registry_path, registry)
        vault.update_lock()
        catalog = vault.scan()
    except Exception as exc:
        write_data(vault.registry_path, old_registry)
        write_data(vault.lock_path, old_lock)
        if destination.exists():
            shutil.rmtree(destination)
        try:
            vault.scan()
        except Exception:
            pass
        _record_transaction(vault, tx, {"operation": "source.skills-cli.add", "status": "rolled-back", "source_id": source_id, "error": str(exc)})
        raise ServiceError("source_install_failed", f"外部来源安装失败，已回滚：{exc}", {"transaction_id": tx}) from exc

    installed_ids = [
        entry["id"] for entry in catalog.get("skills", []) if entry.get("source_id") == source_id
    ]
    _record_transaction(
        vault,
        tx,
        {
            "operation": "source.skills-cli.add",
            "status": "complete",
            "source_id": source_id,
            "source_url": source_url,
            "skills": installed_ids,
            "update_policy": "self-managed",
        },
    )
    return {
        "transaction_id": tx,
        "status": "complete",
        "source_id": source_id,
        "skills": installed_ids,
        "installed": install_result.get("skills", []),
        "update_policy": "self-managed",
    }


def _clone_and_list_skills(source_url: str) -> Dict[str, Any]:
    """Clone a git source into a temp directory and report its advertised skills."""
    with tempfile.TemporaryDirectory(prefix="skills-vault-git-") as directory:
        repo = Path(directory) / "src"
        run(["git", "clone", "--quiet", "--depth", "1", "--", source_url, str(repo)], timeout=180)
        skills: List[Dict[str, Any]] = []
        for skill_md in sorted(repo.rglob("SKILL.md")):
            if ".git" in skill_md.parts:
                continue
            metadata, _ = parse_frontmatter(skill_md.read_text(encoding="utf-8", errors="replace"))
            name = str(metadata.get("name") or skill_md.parent.name)
            description = str(metadata.get("description") or "")
            relative = skill_md.relative_to(repo).as_posix()
            skills.append({"name": name, "path": relative, "description": description[:200]})
        commit = git(repo, "rev-parse", "HEAD", check=False) or ""
        branch = git(repo, "rev-parse", "--abbrev-ref", "HEAD", check=False) or "main"
        return {"skills": skills, "commit": commit, "branch": branch}


def git_source_preview(
    vault: Vault,
    source_id: str,
    source_url: str,
    branch: str = "main",
) -> Dict[str, Any]:
    source_id, source_url = _validate_git_source(source_id, source_url)
    if source_id in vault.registry.get("sources", {}):
        raise ServiceError("already_exists", f"来源已存在：{source_id}")
    destination = vault.root / "sources" / source_id
    if destination.exists():
        raise ServiceError("already_exists", f"来源目录已存在：{destination}")
    try:
        discovery = _clone_and_list_skills(source_url)
    except VaultError as exc:
        raise ServiceError("source_discovery_failed", f"Git 来源克隆或解析失败：{exc}") from exc
    tx = transaction_id("source_add")
    plan = {
        "transaction_id": tx,
        "source_id": source_id,
        "source_url": source_url,
        "kind": "git",
        "branch": branch,
        "update_policy": "strict",
        "destination": str(destination),
        "commit": discovery["commit"],
        "remote_branch": discovery["branch"],
        "skills": discovery["skills"],
        "notes": [
            "以严格 Git 来源登记，克隆到 Vault 专用目录。",
            "后续更新通过 Git 版本锁定（fetch + 审阅 commit 差异）完成。",
            "来源初始状态为 unreviewed，需审核后再启用。",
        ],
    }
    plan["preview_token"] = _issue_token(vault, "source.git.add", {"plan": plan})
    return plan


def git_source_apply(vault: Vault, token: str) -> Dict[str, Any]:
    payload = _consume_token(vault, token, "source.git.add")
    plan = payload.get("plan") or {}
    source_id, source_url = _validate_git_source(plan.get("source_id", ""), plan.get("source_url", ""))
    branch = str(plan.get("branch") or "main")
    registry = vault.registry
    if source_id in registry.get("sources", {}):
        raise ServiceError("already_exists", f"来源已存在：{source_id}")
    destination = vault.root / "sources" / source_id
    if destination.exists():
        raise ServiceError("already_exists", f"来源目录已存在：{destination}")
    old_registry = json.loads(json.dumps(registry))
    old_lock = load_data(vault.lock_path)
    tx = plan.get("transaction_id") or transaction_id("source_add")
    try:
        run(
            ["git", "clone", "--branch", branch, "--", source_url, str(destination)],
            timeout=300,
        )
        registry.setdefault("sources", {})[source_id] = {
            "kind": "git",
            "url": source_url,
            "path": destination.relative_to(vault.root).as_posix(),
            "branch": branch,
            "track": "branch",
            "update_policy": "strict",
            "trust": "unreviewed",
            "license": "unknown",
            "reviewed_at": None,
            "classify": [
                {"pattern": "**/SKILL.md", "as": "unknown"},
            ],
        }
        write_data(vault.registry_path, registry)
        vault.update_lock()
        catalog = vault.scan()
    except Exception as exc:
        write_data(vault.registry_path, old_registry)
        write_data(vault.lock_path, old_lock)
        if destination.exists():
            shutil.rmtree(destination)
        try:
            vault.scan()
        except Exception:
            pass
        _record_transaction(vault, tx, {"operation": "source.git.add", "status": "rolled-back", "source_id": source_id, "error": str(exc)})
        raise ServiceError("source_install_failed", f"Git 来源安装失败，已回滚：{exc}", {"transaction_id": tx}) from exc

    installed_ids = [
        entry["id"] for entry in catalog.get("skills", []) if entry.get("source_id") == source_id
    ]
    _record_transaction(
        vault,
        tx,
        {
            "operation": "source.git.add",
            "status": "complete",
            "source_id": source_id,
            "source_url": source_url,
            "skills": installed_ids,
            "update_policy": "strict",
        },
    )
    return {
        "transaction_id": tx,
        "status": "complete",
        "source_id": source_id,
        "skills": installed_ids,
        "installed": [entry.get("id") for entry in catalog.get("skills", []) if entry.get("source_id") == source_id],
        "update_policy": "strict",
    }


def source_review(vault: Vault, source_id: str, trust: Optional[str] = None, license: Optional[str] = None) -> Dict[str, Any]:
    source_id = str(source_id).strip()
    registry = vault.registry
    if source_id not in registry.get("sources", {}):
        raise ServiceError("not_found", f"来源不存在：{source_id}", {"source_id": source_id})
    source = registry["sources"][source_id]
    previous = {"trust": source.get("trust", "unreviewed"), "license": source.get("license", "unknown")}
    if trust is not None:
        if trust not in ("unreviewed", "reviewed", "trusted"):
            raise ServiceError("invalid_trust", f"trust 必须是 unreviewed、reviewed 或 trusted，收到：{trust}")
        source["trust"] = trust
    if license is not None:
        source["license"] = str(license).strip() or "unknown"
    if source.get("trust") in ("reviewed", "trusted"):
        source["reviewed_at"] = now_iso()[:10]
    write_data(vault.registry_path, registry)
    return {
        "source_id": source_id,
        "previous": previous,
        "trust": source.get("trust", "unreviewed"),
        "license": source.get("license", "unknown"),
        "reviewed_at": source.get("reviewed_at"),
    }


def source_policy_preview(vault: Vault, source_id: str, enabled: bool) -> Dict[str, Any]:
    source_id = str(source_id).strip()
    if source_id == "my":
        raise ServiceError("personal_source", "我的 Skills 不是第三方仓库，请在 Skills 管理中逐项关闭")
    if source_id not in vault.registry.get("sources", {}):
        raise ServiceError("not_found", f"来源不存在：{source_id}", {"source_id": source_id})

    current_enabled = source_id not in vault.disabled_source_ids()
    catalog = vault.catalog()
    source_skills = [entry for entry in catalog.get("skills", []) if entry.get("source_id") == source_id]
    source_ids = {entry["id"] for entry in source_skills}
    active_profiles = vault.active_profiles()
    platform_rows: Dict[str, Dict[str, Any]] = {}
    for platform in ("codex", "claude"):
        details = vault.resolve_profile_details(active_profiles, platform)
        direct = [entry_id for entry_id in details["direct"] if entry_id in source_ids]
        effective = [entry["id"] for entry in details["entries"] if entry["id"] in source_ids]
        platform_rows[platform] = {"selected": direct, "effective": effective}

    install_state = load_data(vault.state_dir / "install-state.json", {"links": []})
    installed_links = [
        row for row in install_state.get("links", []) if row.get("skill_id") in source_ids
    ]
    tx = transaction_id("source")
    plan = {
        "transaction_id": tx,
        "source_id": source_id,
        "action": "enable" if enabled else "disable",
        "current_enabled": current_enabled,
        "target_enabled": bool(enabled),
        "changed": current_enabled != bool(enabled),
        "skill_count": len(source_skills),
        "platforms": platform_rows,
        "installed_links": installed_links,
        "active_profiles": active_profiles,
        "notes": [
            "不会删除第三方仓库、Skill 文件、说明文档或 Profile 中的原始选择。",
            "关闭后，来源策略会在 Profile 解析之前统一过滤该仓库的 Skills。",
            "应用时会先备份，再同步 Codex 与 Claude Code 的受管链接。",
        ],
    }
    plan["preview_token"] = _issue_token(vault, "source.policy", {"plan": plan})
    return plan


def source_policy_apply(vault: Vault, token: str) -> Dict[str, Any]:
    payload = _consume_token(vault, token, "source.policy")
    plan = payload.get("plan") or {}
    source_id = plan.get("source_id")
    if source_id not in vault.registry.get("sources", {}):
        raise ServiceError("not_found", f"来源不存在：{source_id}", {"source_id": source_id})
    tx = plan.get("transaction_id") or transaction_id("source")
    target_enabled = bool(plan.get("target_enabled"))
    if not plan.get("changed"):
        _record_transaction(vault, tx, {"operation": "source.policy", "status": "unchanged", "source_id": source_id, "enabled": target_enabled})
        return {"transaction_id": tx, "status": "unchanged", "source_id": source_id, "enabled": target_enabled}

    old_policy = vault.source_policies()
    backup = create_backup(vault)
    policy = json.loads(json.dumps(old_policy))
    policy.setdefault("sources", {})[source_id] = {
        "enabled": target_enabled,
        "updated_at": now_iso(),
        "transaction_id": tx,
    }
    policy["updated_at"] = now_iso()
    write_data(vault.source_policies_path, policy)
    try:
        install_result = install(
            vault,
            vault.active_profiles(),
            assume_yes=True,
            backup_path=backup,
        )
    except Exception as exc:
        write_data(vault.source_policies_path, old_policy)
        _record_transaction(vault, tx, {"operation": "source.policy", "status": "rolled-back", "source_id": source_id, "enabled": target_enabled, "backup": backup.name, "error": str(exc)})
        raise ServiceError("source_policy_failed", f"来源状态修改失败，已恢复备份：{exc}", {"transaction_id": tx, "backup_id": backup.name}) from exc

    _record_transaction(vault, tx, {"operation": "source.policy", "status": "complete", "source_id": source_id, "enabled": target_enabled, "backup": backup.name})
    return {
        "transaction_id": tx,
        "status": "complete",
        "source_id": source_id,
        "enabled": target_enabled,
        "backup_id": backup.name,
        "install": install_result,
    }


def _source_delete_path(vault: Vault, source: Dict[str, Any]) -> Path:
    source_path = vault.source_path(source)
    sources_root = (vault.root / "sources").resolve()
    try:
        relative = source_path.relative_to(sources_root)
    except ValueError as exc:
        raise ServiceError(
            "unsafe_source_path",
            f"拒绝删除 sources/ 管理范围之外的路径：{source_path}",
        ) from exc
    if not relative.parts:
        raise ServiceError("unsafe_source_path", "拒绝删除整个 sources 目录")
    return source_path


def source_delete_preview(vault: Vault, source_id: str) -> Dict[str, Any]:
    source_id = str(source_id).strip()
    if source_id == "my":
        raise ServiceError("personal_source", "我的 Skills 不是可删除的第三方来源")
    source = vault.registry.get("sources", {}).get(source_id)
    if not source:
        raise ServiceError("not_found", f"来源不存在：{source_id}", {"source_id": source_id})
    source_path = _source_delete_path(vault, source)
    catalog = vault.catalog()
    source_skills = [
        entry for entry in catalog.get("skills", []) if entry.get("source_id") == source_id
    ]
    tombstones = load_data(vault.deleted_skills_path, {"schema_version": 1, "skills": {}})
    tombstone_ids = sorted(
        skill_id
        for skill_id, row in (tombstones.get("skills") or {}).items()
        if row.get("source_id") == source_id
    )
    skill_ids = sorted({entry["id"] for entry in source_skills} | set(tombstone_ids))
    selected = set(skill_ids)
    profile_changes = []
    for name, path in vault.profile_files().items():
        profile = load_data(path)
        removed_skills = [item for item in profile.get("include", []) if item in selected]
        removes_source = source_id in profile.get("include_source", [])
        if removed_skills or removes_source:
            profile_changes.append(
                {
                    "profile": name,
                    "skills": removed_skills,
                    "include_source": removes_source,
                }
            )
    install_state = load_data(vault.state_dir / "install-state.json", {"links": []})
    links = [item for item in install_state.get("links", []) if item.get("skill_id") in selected]
    annotations = vault.annotations.get("skills", {})
    annotation_ids = [skill_id for skill_id in skill_ids if skill_id in annotations]
    guides = [skill_id for skill_id in skill_ids if _guide_path(vault, skill_id).is_file()]
    source_row = next((row for row in vault.source_rows() if row["id"] == source_id), {})
    tx = transaction_id("source_delete")
    plan = {
        "transaction_id": tx,
        "source_id": source_id,
        "kind": vault.source_kind(source),
        "source_path": str(source_path),
        "source_exists": source_path.exists(),
        "dirty": bool(source_row.get("dirty")),
        "skill_ids": skill_ids,
        "profiles": profile_changes,
        "links": links,
        "counts": {
            "skills": len(source_skills),
            "tombstones": len(tombstone_ids),
            "profiles": len(profile_changes),
            "links": len(links),
            "annotations": len(annotation_ids),
            "guides": len(guides),
        },
        "notes": [
            "来源注册、版本锁、停用策略和该来源的删除记录会一并清理。",
            "来源目录会移入 .vault/trash 的事务归档，不会直接永久擦除。",
            "相关 Profile 选择、注解引用和受管安装链接会同步移除。",
        ],
    }
    plan["preview_token"] = _issue_token(vault, "source.delete", {"plan": plan})
    return plan


def source_delete_apply(vault: Vault, token: str) -> Dict[str, Any]:
    payload = _consume_token(vault, token, "source.delete")
    plan = payload.get("plan") or {}
    source_id = str(plan.get("source_id") or "")
    source = vault.registry.get("sources", {}).get(source_id)
    if not source:
        raise ServiceError("not_found", f"来源不存在：{source_id}", {"source_id": source_id})
    source_path = _source_delete_path(vault, source)
    skill_ids = set(plan.get("skill_ids") or [])
    tx = plan.get("transaction_id") or transaction_id("source_delete")
    archive = vault.state_dir / "trash" / tx
    if archive.exists():
        raise ServiceError("transaction_exists", f"来源删除事务已存在：{tx}")
    archive.mkdir(parents=True)
    try:
        link_backup = create_backup(vault)
    except Exception as exc:
        archive.rmdir()
        raise ServiceError("backup_failed", f"删除来源前备份失败：{exc}") from exc

    snapshot_paths = [
        vault.registry_path,
        vault.lock_path,
        vault.annotations_path,
        vault.deleted_skills_path,
        vault.source_policies_path,
        vault.state_dir / "install-state.json",
        *vault.profile_files().values(),
    ]
    snapshot_existence: Dict[str, bool] = {}
    for path in snapshot_paths:
        try:
            relative = path.relative_to(vault.root)
        except ValueError:
            continue
        snapshot_existence[relative.as_posix()] = path.exists()
        _snapshot_file(path, archive / "state" / relative)
    write_data(archive / "state-existence.json", snapshot_existence)

    moved: List[Dict[str, str]] = []
    try:
        if source_path.exists():
            if not source_path.is_dir():
                raise ServiceError("unsafe_source_path", f"来源路径不是目录：{source_path}")
            destination = archive / "source"
            shutil.move(str(source_path), str(destination))
            moved.append({"from": str(source_path), "to": str(destination)})

        for skill_id in sorted(skill_ids):
            guide = _guide_path(vault, skill_id)
            if guide.is_file():
                destination = archive / "guides" / guide.name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(guide), str(destination))
                moved.append({"from": str(guide), "to": str(destination)})

        registry = vault.registry
        registry.setdefault("sources", {}).pop(source_id, None)
        write_data(vault.registry_path, registry)

        lock = load_data(vault.lock_path, {"schema_version": 1, "sources": {}})
        lock.setdefault("sources", {}).pop(source_id, None)
        write_data(vault.lock_path, lock)

        policies = vault.source_policies()
        policies.setdefault("sources", {}).pop(source_id, None)
        policies["updated_at"] = now_iso()
        write_data(vault.source_policies_path, policies)

        tombstones = load_data(vault.deleted_skills_path, {"schema_version": 1, "skills": {}})
        tombstone_rows = tombstones.setdefault("skills", {})
        for skill_id, row in list(tombstone_rows.items()):
            if skill_id in skill_ids or row.get("source_id") == source_id:
                tombstone_rows.pop(skill_id, None)
        write_data(vault.deleted_skills_path, tombstones)

        annotations = vault.annotations
        annotation_rows = annotations.setdefault("skills", {})
        for skill_id in skill_ids:
            annotation_rows.pop(skill_id, None)
        for values in annotation_rows.values():
            for key in ("requires", "recommends", "routes_to"):
                if isinstance(values.get(key), list):
                    values[key] = [item for item in values[key] if item not in skill_ids]
        write_data(vault.annotations_path, annotations)

        for _, path in vault.profile_files().items():
            profile = load_data(path)
            if isinstance(profile.get("include"), list):
                profile["include"] = [item for item in profile["include"] if item not in skill_ids]
            if isinstance(profile.get("include_source"), list):
                profile["include_source"] = [
                    item for item in profile["include_source"] if item != source_id
                ]
            write_data(path, profile)

        install_state_path = vault.state_dir / "install-state.json"
        install_state = load_data(install_state_path, {"schema_version": 1, "links": []})
        retained_links = []
        allowed_link_parents = {
            (Path.home() / ".agents" / "skills").resolve(),
            (Path.home() / ".claude" / "skills").resolve(),
        }
        for item in install_state.get("links", []):
            if item.get("skill_id") not in skill_ids:
                retained_links.append(item)
                continue
            link_path = Path(item.get("path", ""))
            if link_path.is_symlink():
                if link_path.parent.resolve() not in allowed_link_parents:
                    raise ServiceError(
                        "unsafe_link_path",
                        f"拒绝移除管理范围之外的链接：{link_path}",
                    )
                link_path.unlink()
        install_state["links"] = retained_links
        install_state["updated_at"] = now_iso()
        install_state["last_source_delete_transaction"] = tx
        write_data(install_state_path, install_state)
        resulting_catalog = vault.scan()
    except Exception as exc:
        for item in reversed(moved):
            original, destination = Path(item["from"]), Path(item["to"])
            if destination.exists() and not original.exists():
                original.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(destination), str(original))
        state_archive = archive / "state"
        for snapshot in state_archive.rglob("*") if state_archive.exists() else []:
            if snapshot.is_file():
                relative = snapshot.relative_to(state_archive)
                target = vault.root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(snapshot, target)
        for relative, existed in snapshot_existence.items():
            target = vault.root / relative
            if not existed and target.exists() and target.is_file():
                target.unlink()
        try:
            restore_backup(vault, link_backup.name, assume_yes=True)
            vault.scan()
        except Exception:
            pass
        _record_transaction(
            vault,
            tx,
            {
                "operation": "source.delete",
                "status": "rolled-back",
                "source_id": source_id,
                "archive": str(archive),
                "backup": link_backup.name,
                "error": str(exc),
            },
        )
        raise ServiceError(
            "source_delete_failed",
            f"来源删除失败，已尝试恢复：{exc}",
            {"transaction_id": tx, "archive": str(archive)},
        ) from exc

    manifest = {
        "schema_version": 1,
        "transaction_id": tx,
        "deleted_at": now_iso(),
        "source_id": source_id,
        "skill_ids": sorted(skill_ids),
        "moved": moved,
        "link_backup": link_backup.name,
        "plan": plan,
    }
    write_data(archive / "manifest.json", manifest)
    _record_transaction(
        vault,
        tx,
        {
            "operation": "source.delete",
            "status": "complete",
            "source_id": source_id,
            "skill_ids": sorted(skill_ids),
            "archive": str(archive),
            "backup": link_backup.name,
        },
    )
    return {
        "transaction_id": tx,
        "status": "complete",
        "source_id": source_id,
        "removed_skills": sorted(skill_ids),
        "archive": str(archive),
        "backup_id": link_backup.name,
        "remaining_sources": len(vault.registry.get("sources", {})),
        "remaining_skills": resulting_catalog.get("counts", {}).get("skills", 0),
    }


def delete_skills_preview(vault: Vault, skill_ids: Sequence[str]) -> Dict[str, Any]:
    requested = list(dict.fromkeys(str(item).strip() for item in skill_ids if str(item).strip()))
    if not requested:
        raise ServiceError("empty_selection", "至少选择一个要删除的 Skill")
    catalog = vault.catalog()
    by_id = {entry["id"]: entry for entry in catalog.get("skills", [])}
    missing = sorted(set(requested) - set(by_id))
    if missing:
        raise ServiceError("not_found", f"Skill 不存在：{', '.join(missing)}", {"skill_ids": missing})

    selected = set(requested)
    profile_changes = []
    for name, path in vault.profile_files().items():
        profile = load_data(path)
        removed = [item for item in profile.get("include", []) if item in selected]
        if removed:
            profile_changes.append({"profile": name, "removed": removed})

    annotations = vault.annotations.get("skills", {})
    reference_changes = []
    for owner_id, values in annotations.items():
        fields = {}
        for key in ("requires", "recommends", "routes_to"):
            removed = [item for item in values.get(key, []) if item in selected]
            if removed:
                fields[key] = removed
        if fields and owner_id not in selected:
            reference_changes.append({"skill_id": owner_id, "fields": fields})

    install_state = load_data(vault.state_dir / "install-state.json", {"links": []})
    links = [item for item in install_state.get("links", []) if item.get("skill_id") in selected]
    derivatives = [
        entry["id"]
        for entry in catalog.get("skills", [])
        if (entry.get("origin") or {}).get("source_skill_id") in selected and entry["id"] not in selected
    ]
    items = []
    for skill_id in requested:
        entry = by_id[skill_id]
        source_action = "archive-personal-directory" if entry.get("source_id") == "my" else "hide-upstream-skill"
        items.append(
            {
                "id": skill_id,
                "name": entry.get("name"),
                "source_id": entry.get("source_id"),
                "path": entry.get("path"),
                "source_action": source_action,
                "guide": str(_guide_path(vault, skill_id).relative_to(vault.root)) if _guide_path(vault, skill_id).exists() else None,
                "annotation": skill_id in annotations,
            }
        )
    tx = transaction_id("delete")
    plan = {
        "transaction_id": tx,
        "skill_ids": requested,
        "items": items,
        "profiles": profile_changes,
        "annotation_references": reference_changes,
        "links": links,
        "derivatives_retained": sorted(derivatives),
        "counts": {
            "skills": len(items),
            "profiles": len(profile_changes),
            "links": len(links),
            "guides": sum(bool(item["guide"]) for item in items),
            "annotations": sum(bool(item["annotation"]) for item in items),
        },
        "notes": [
            "原创和派生 Skill 目录会移入事务归档，可从归档恢复。",
            "第三方来源保留 Git 工作树文件，并写入已删除清单，避免来源仓库变为 dirty。",
            *([f"保留独立派生 Skill：{', '.join(sorted(derivatives))}"] if derivatives else []),
        ],
    }
    plan["preview_token"] = _issue_token(vault, "skill.delete", {"plan": plan})
    return plan


def _snapshot_file(path: Path, destination: Path) -> None:
    if path.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)


def delete_skills_apply(vault: Vault, token: str) -> Dict[str, Any]:
    payload = _consume_token(vault, token, "skill.delete")
    plan = payload.get("plan") or {}
    skill_ids = list(plan.get("skill_ids") or [])
    if not skill_ids:
        raise ServiceError("invalid_plan", "删除预览中没有 Skill")
    selected = set(skill_ids)
    tx = plan.get("transaction_id") or transaction_id("delete")
    archive = vault.state_dir / "trash" / tx
    if archive.exists():
        raise ServiceError("transaction_exists", f"删除事务已存在：{tx}")
    archive.mkdir(parents=True)
    try:
        link_backup = create_backup(vault)
    except Exception as exc:
        archive.rmdir()
        raise ServiceError("backup_failed", f"删除前备份失败：{exc}") from exc
    moved: List[Dict[str, str]] = []
    snapshot_paths = [
        vault.annotations_path,
        vault.deleted_skills_path,
        vault.state_dir / "install-state.json",
        *vault.profile_files().values(),
    ]
    snapshot_existence: Dict[str, bool] = {}
    for path in snapshot_paths:
        try:
            relative = path.relative_to(vault.root)
        except ValueError:
            continue
        snapshot_existence[relative.as_posix()] = path.exists()
        _snapshot_file(path, archive / "state" / relative)
    write_data(archive / "state-existence.json", snapshot_existence)

    try:
        catalog = vault.catalog()
        by_id = {entry["id"]: entry for entry in catalog.get("skills", [])}
        for skill_id in skill_ids:
            entry = by_id[skill_id]
            source_path = (vault.root / entry["path"]).resolve()
            if entry.get("source_id") == "my":
                personal_root = (vault.root / "my-skills").resolve()
                if source_path.parent != personal_root or not source_path.is_dir():
                    raise ServiceError("unsafe_path", f"拒绝删除非标准个人 Skill 路径：{source_path}")
                destination = archive / "skills" / skill_id.replace("/", "--")
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source_path), str(destination))
                moved.append({"from": str(source_path), "to": str(destination)})
            guide = _guide_path(vault, skill_id)
            if guide.exists():
                destination = archive / "guides" / guide.name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(guide), str(destination))
                moved.append({"from": str(guide), "to": str(destination)})

        annotations = vault.annotations
        skill_annotations = annotations.setdefault("skills", {})
        for skill_id in skill_ids:
            skill_annotations.pop(skill_id, None)
        for values in skill_annotations.values():
            for key in ("requires", "recommends", "routes_to"):
                if isinstance(values.get(key), list):
                    values[key] = [item for item in values[key] if item not in selected]
        write_data(vault.annotations_path, annotations)

        for _, path in vault.profile_files().items():
            profile = load_data(path)
            if isinstance(profile.get("include"), list):
                profile["include"] = [item for item in profile["include"] if item not in selected]
                write_data(path, profile)

        install_state_path = vault.state_dir / "install-state.json"
        install_state = load_data(install_state_path, {"schema_version": 1, "links": []})
        retained_links = []
        allowed_link_parents = {
            (Path.home() / ".agents" / "skills").resolve(),
            (Path.home() / ".claude" / "skills").resolve(),
        }
        for item in install_state.get("links", []):
            if item.get("skill_id") not in selected:
                retained_links.append(item)
                continue
            link_path = Path(item.get("path", ""))
            if link_path.is_symlink():
                if link_path.parent.resolve() not in allowed_link_parents:
                    raise ServiceError("unsafe_link_path", f"拒绝移除管理范围之外的链接：{link_path}")
                link_path.unlink()
        install_state["links"] = retained_links
        install_state["updated_at"] = now_iso()
        install_state["last_delete_transaction"] = tx
        write_data(install_state_path, install_state)

        tombstones = load_data(vault.deleted_skills_path, {"schema_version": 1, "skills": {}})
        rows = tombstones.setdefault("skills", {})
        for skill_id in skill_ids:
            entry = by_id[skill_id]
            if entry.get("source_id") != "my":
                rows[skill_id] = {
                    "deleted_at": now_iso(),
                    "transaction_id": tx,
                    "source_id": entry.get("source_id"),
                    "path": entry.get("path"),
                    "fingerprint": entry.get("fingerprint"),
                }
        write_data(vault.deleted_skills_path, tombstones)
        resulting_catalog = vault.scan()
    except Exception as exc:
        for item in reversed(moved):
            source, destination = Path(item["from"]), Path(item["to"])
            if destination.exists() and not source.exists():
                source.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(destination), str(source))
        for snapshot in (archive / "state").rglob("*") if (archive / "state").exists() else []:
            if snapshot.is_file():
                relative = snapshot.relative_to(archive / "state")
                target = vault.root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(snapshot, target)
        for relative, existed in snapshot_existence.items():
            target = vault.root / relative
            if not existed and target.exists() and target.is_file():
                target.unlink()
        try:
            restore_backup(vault, link_backup.name, assume_yes=True)
            vault.scan()
        except Exception:
            pass
        _record_transaction(vault, tx, {"operation": "skill.delete", "status": "rolled-back", "skill_ids": skill_ids, "archive": str(archive), "backup": link_backup.name, "error": str(exc)})
        raise ServiceError("delete_failed", f"删除失败，已尝试恢复：{exc}", {"transaction_id": tx, "archive": str(archive)}) from exc

    manifest = {
        "schema_version": 1,
        "transaction_id": tx,
        "deleted_at": now_iso(),
        "skill_ids": skill_ids,
        "moved": moved,
        "link_backup": link_backup.name,
        "plan": plan,
    }
    write_data(archive / "manifest.json", manifest)
    _record_transaction(vault, tx, {"operation": "skill.delete", "status": "complete", "skill_ids": skill_ids, "archive": str(archive), "backup": link_backup.name})
    return {
        "transaction_id": tx,
        "status": "complete",
        "deleted": skill_ids,
        "archive": str(archive),
        "backup_id": link_backup.name,
        "remaining_skills": resulting_catalog.get("counts", {}).get("skills", 0),
    }


def _token_path(vault: Vault, token: str) -> Path:
    return vault.state_dir / "tokens" / f"{token}.json"


def _issue_token(vault: Vault, kind: str, payload: Dict[str, Any]) -> str:
    token = secrets.token_urlsafe(24)
    record = {"kind": kind, "token": token, "issued_at": now_iso(), "fingerprint": _state_fingerprint(vault), "payload": payload}
    write_data(_token_path(vault, token), record)
    return token


def _consume_token(vault: Vault, token: str, kind: str) -> Dict[str, Any]:
    path = _token_path(vault, token)
    if not path.exists():
        raise ServiceError("invalid_token", "Preview token is invalid or expired")
    record = load_data(path)
    try:
        issued_at = dt.datetime.fromisoformat(record.get("issued_at", ""))
    except (TypeError, ValueError):
        issued_at = None
    if issued_at is None or dt.datetime.now().astimezone() - issued_at > dt.timedelta(minutes=15):
        path.unlink(missing_ok=True)
        raise ServiceError("expired_token", "Preview 已超过 15 分钟，请重新生成")
    if record.get("kind") != kind or record.get("fingerprint") != _state_fingerprint(vault):
        raise ServiceError("stale_preview", "Preview is stale; generate a new preview")
    path.unlink()
    return record.get("payload", {})


def install_preview(vault: Vault, profiles: Sequence[str]) -> Dict[str, Any]:
    try:
        plan = install_plan(vault, profiles)
    except VaultError as exc:
        raise ServiceError("install_plan_invalid", str(exc)) from exc
    plan["transaction_id"] = transaction_id("install")
    plan["fingerprint"] = _state_fingerprint(vault)
    plan["preview_token"] = _issue_token(vault, "install", {"profiles": list(profiles), "plan": plan})
    return plan


def install_apply(vault: Vault, token: str, reset: bool = False) -> Dict[str, Any]:
    payload = _consume_token(vault, token, "install")
    profiles = payload.get("profiles", [])
    tx = payload.get("plan", {}).get("transaction_id") or transaction_id("install")
    backup = create_backup(vault)
    try:
        result = install(
            vault,
            profiles,
            reset=reset,
            assume_yes=True,
            backup_path=backup,
        )
    except Exception as exc:
        _record_transaction(
            vault,
            tx,
            {
                "operation": "install",
                "status": "rolled-back",
                "profiles": profiles,
                "backup": backup.name,
                "error": str(exc),
            },
        )
        raise ServiceError(
            "install_failed",
            f"安装失败，已从备份 {backup.name} 恢复：{exc}",
            {"transaction_id": tx, "backup_id": backup.name},
        ) from exc
    _record_transaction(
        vault,
        tx,
        {
            "operation": "install",
            "status": "complete",
            "profiles": profiles,
            "backup": backup.name,
        },
    )
    return {
        "transaction_id": tx,
        "status": "complete",
        "profiles": profiles,
        "backup_id": backup.name,
        "result": result,
    }


def managed_selection_payload(vault: Vault) -> Dict[str, Any]:
    active = vault.active_profiles()
    selections: Dict[str, str] = {}
    resolved: Dict[str, Dict[str, Any]] = {}
    for platform in ("codex", "claude"):
        details = vault.resolve_profile_details(active, platform)
        resolved[platform] = {
            "direct": details["direct"],
            "effective": [item["id"] for item in details["entries"]],
            "notes": details["notes"],
        }
        for skill_id in details["direct"]:
            previous = selections.get(skill_id)
            if previous and previous != platform:
                selections[skill_id] = "both"
            else:
                selections[skill_id] = platform
    return {
        "active_profiles": active,
        "managed": all(name in MANAGED_PROFILES for name in active),
        "selections": selections,
        "resolved": resolved,
        "conflicts": vault.catalog().get("conflicts", {}),
    }


def save_managed_selection(vault: Vault, selections: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(selections, dict):
        raise ServiceError("invalid_selection", "Skills selection must be an object")
    catalog = vault.catalog()
    by_id = {entry["id"]: entry for entry in catalog.get("skills", [])}
    allowed_modes = {"off", "both", "codex", "claude"}
    selected_by_name: Dict[str, List[str]] = {}
    normalized: Dict[str, str] = {}
    for skill_id, raw_mode in selections.items():
        mode = str(raw_mode)
        if mode not in allowed_modes:
            raise ServiceError("invalid_selection", f"Invalid mode for {skill_id}: {mode}")
        if skill_id not in by_id:
            raise ServiceError("not_found", f"Skill not found: {skill_id}")
        if mode == "off":
            continue
        platforms = set(by_id[skill_id].get("compatibility", {}).get("platforms", []))
        requested = {"codex", "claude"} if mode == "both" else {mode}
        if not requested.issubset(platforms):
            raise ServiceError(
                "incompatible_platform",
                f"{skill_id} is not compatible with {mode}",
                {"skill_id": skill_id, "mode": mode, "platforms": sorted(platforms)},
            )
        normalized[skill_id] = mode
        selected_by_name.setdefault(by_id[skill_id]["name"].lower(), []).append(skill_id)
    conflicts = {name: ids for name, ids in selected_by_name.items() if len(ids) > 1}
    if conflicts:
        raise ServiceError(
            "name_conflict",
            "同名 Skill 只能启用一个实现",
            {"conflicts": conflicts},
        )

    effective = set(normalized)
    queue = list(effective)
    while queue:
        skill_id = queue.pop()
        for dependency in by_id[skill_id].get("requires", []):
            if dependency not in by_id:
                raise ServiceError("missing_dependency", f"{skill_id} requires missing skill {dependency}")
            if dependency not in effective:
                effective.add(dependency)
                queue.append(dependency)
    effective_by_name: Dict[str, List[str]] = {}
    for skill_id in effective:
        effective_by_name.setdefault(by_id[skill_id]["name"].lower(), []).append(skill_id)
    dependency_conflicts = {
        name: sorted(ids) for name, ids in effective_by_name.items() if len(ids) > 1
    }
    if dependency_conflicts:
        raise ServiceError(
            "dependency_name_conflict",
            "依赖闭包包含同名 Skill，请先选择唯一实现",
            {"conflicts": dependency_conflicts},
        )

    shared = sorted(skill_id for skill_id, mode in normalized.items() if mode == "both")
    codex = sorted(skill_id for skill_id, mode in normalized.items() if mode == "codex")
    claude = sorted(skill_id for skill_id, mode in normalized.items() if mode == "claude")
    profile_rows = {
        "ui-shared": {
            "schema_version": 1,
            "description": "UI-managed skills shared by Codex and Claude Code.",
            "include": shared,
            "classification": ["published"],
        },
        "ui-codex": {
            "schema_version": 1,
            "description": "UI-managed Codex-only skills.",
            "platform": "codex",
            "include": codex,
            "classification": ["published"],
        },
        "ui-claude": {
            "schema_version": 1,
            "description": "UI-managed Claude-only skills.",
            "platform": "claude",
            "include": claude,
            "classification": ["published"],
        },
    }
    for name, data in profile_rows.items():
        write_data(vault.root / "profiles" / f"{name}.yaml", data)
    vault.activate_profiles(MANAGED_PROFILES)
    tx = transaction_id("selection")
    _record_transaction(
        vault,
        tx,
        {
            "operation": "selection.save",
            "status": "saved-not-installed",
            "profiles": list(MANAGED_PROFILES),
            "counts": {"both": len(shared), "codex": len(codex), "claude": len(claude)},
        },
    )
    result = managed_selection_payload(vault)
    result.update({"transaction_id": tx, "status": "saved-not-installed"})
    return result


def profiles_payload(vault: Vault) -> Dict[str, Any]:
    profiles = []
    for name, path in vault.profile_files().items():
        profile = load_data(path)
        platform = profile.get("platform")
        platforms = [platform] if platform else ["codex", "claude"]
        resolved = {p: vault.resolve_profile_details([name], p) for p in platforms}
        profiles.append({"name": name, "description": profile.get("description", ""), "platform": platform,
                        "include": profile.get("include", []), "include_source": profile.get("include_source", []),
                        "classification": profile.get("classification", ["published"]),
                        "resolved": {p: {"count": len(v["entries"]), "notes": v["notes"], "status": v["status"], "conflicts": v["conflicts"]} for p, v in resolved.items()},
                        "active": name in vault.active_profiles()})
    return {"active": vault.active_profiles(), "profiles": profiles}


def save_profile(vault: Vault, name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    if not name or "/" in name or ".." in name:
        raise ServiceError("invalid_profile", "Profile name is invalid")
    payload = {"schema_version": 1, "description": str(data.get("description", "")),
               "include": list(dict.fromkeys(data.get("include", []))),
               "include_source": list(dict.fromkeys(data.get("include_source", []))),
               "classification": data.get("classification", ["published"])}
    if data.get("platform"):
        payload["platform"] = data["platform"]
    write_data(vault.root / "profiles" / f"{name}.yaml", payload)
    vault.scan()
    tx = transaction_id("profile")
    _record_transaction(vault, tx, {"operation": "profile.save", "status": "complete", "profile": name})
    return {"transaction_id": tx, "profile": name, "status": "saved", "data": payload}


def copy_profile(vault: Vault, source_name: str, target_name: str) -> Dict[str, Any]:
    source_path = vault.profile_files().get(source_name)
    if not source_path:
        raise ServiceError("not_found", f"Profile not found: {source_name}")
    if target_name in vault.profile_files():
        raise ServiceError("already_exists", f"Profile already exists: {target_name}")
    data = load_data(source_path)
    data["description"] = f"Copy of {source_name}"
    return save_profile(vault, target_name, data)


def activate_profiles(vault: Vault, names: Sequence[str]) -> Dict[str, Any]:
    try:
        vault.activate_profiles(names)
    except VaultError as exc:
        raise ServiceError("invalid_profile", str(exc)) from exc
    tx = transaction_id("profile")
    _record_transaction(vault, tx, {"operation": "profile.activate", "status": "complete", "profiles": list(names)})
    return {"transaction_id": tx, "status": "active", "profiles": list(names)}


def compare_skills(vault: Vault, left_id: str, right_id: str) -> Dict[str, Any]:
    catalog = vault.catalog()
    by_id = {entry["id"]: entry for entry in catalog.get("skills", [])}
    if left_id not in by_id or right_id not in by_id:
        raise ServiceError("not_found", "Both skills must exist")
    left, right = by_id[left_id], by_id[right_id]
    left_text = (vault.root / left["path"] / "SKILL.md").read_text(encoding="utf-8", errors="replace").splitlines()
    right_text = (vault.root / right["path"] / "SKILL.md").read_text(encoding="utf-8", errors="replace").splitlines()
    return {"left": left, "right": right, "diff": list(difflib.unified_diff(left_text, right_text, fromfile=left_id, tofile=right_id, lineterm="")),
            "same_name": left["name"].lower() == right["name"].lower()}


def personal_catalog_state(vault: Vault) -> Dict[str, Any]:
    """Compare personal Skill files with their last generated catalog entries."""
    catalog_entries = {
        entry["id"]: entry
        for entry in vault.catalog().get("skills", [])
        if entry.get("source_id") == "my"
    }
    current: Dict[str, Dict[str, str]] = {}
    for skill_md in sorted((vault.root / "my-skills").glob("*/SKILL.md")):
        metadata, _ = parse_frontmatter(
            skill_md.read_text(encoding="utf-8", errors="replace")
        )
        name = str(metadata.get("name") or skill_md.parent.name).strip()
        skill_id = f"my/{name}"
        current[skill_id] = {
            "path": skill_md.parent.relative_to(vault.root).as_posix(),
            "fingerprint": tree_fingerprint(skill_md.parent, ignore_origin=True),
        }

    added = sorted(set(current) - set(catalog_entries))
    missing = sorted(set(catalog_entries) - set(current))
    changed = sorted(
        skill_id
        for skill_id in set(current) & set(catalog_entries)
        if current[skill_id]["fingerprint"]
        != catalog_entries[skill_id].get("fingerprint")
    )
    return {
        "fresh": not (added or changed or missing),
        "added": added,
        "changed": changed,
        "missing": missing,
        "personal_skills": len(current),
    }


def scan_catalog(vault: Vault) -> Dict[str, Any]:
    """Rebuild the catalog and report stable ID/fingerprint-level differences."""
    before_catalog = vault.catalog()
    before = {
        entry["id"]: entry.get("fingerprint")
        for entry in before_catalog.get("skills", [])
    }
    after_catalog = vault.scan()
    after = {
        entry["id"]: entry.get("fingerprint")
        for entry in after_catalog.get("skills", [])
    }
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    changed = sorted(
        skill_id
        for skill_id in set(before) & set(after)
        if before[skill_id] != after[skill_id]
    )
    tx = transaction_id("scan")
    _record_transaction(
        vault,
        tx,
        {
            "operation": "catalog.scan",
            "status": "complete",
            "added": added,
            "changed": changed,
            "removed": removed,
        },
    )
    return {
        "transaction_id": tx,
        "status": "complete",
        "added": added,
        "changed": changed,
        "removed": removed,
        "conflicts": after_catalog.get("conflicts", {}),
        "counts": after_catalog.get("counts", {}),
        "catalog_state": personal_catalog_state(vault),
    }


def update_preview(vault: Vault, source_ids: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    try:
        rows = update_plan(vault, source_ids)
    except VaultError as exc:
        raise ServiceError("update_check_failed", str(exc)) from exc
    normalized_rows: List[Dict[str, Any]] = []
    for original in rows:
        row = dict(original)
        if row.get("status") == "fast-forward" and row.get("dirty"):
            row["status"] = "blocked-dirty"
        normalized_rows.append(row)
    actionable = [
        row
        for row in normalized_rows
        if row.get("status") in {"fast-forward", "self-managed"}
    ]
    blocked = [
        row
        for row in normalized_rows
        if row.get("status")
        in {"blocked-dirty", "diverged", "missing", "missing-remote-ref"}
    ]
    payload = {"sources": actionable, "observed_sources": normalized_rows}
    payload["preview_token"] = _issue_token(vault, "update", payload)
    payload["transaction_id"] = transaction_id("update")
    return {
        "sources": normalized_rows,
        "actionable_source_ids": [row.get("source_id") for row in actionable],
        "blocked_source_ids": [row.get("source_id") for row in blocked],
        "preview_token": payload["preview_token"],
        "transaction_id": payload["transaction_id"],
    }


def update_apply(vault: Vault, token: str) -> Dict[str, Any]:
    payload = _consume_token(vault, token, "update")
    rows = payload.get("sources", [])
    changed = apply_updates(vault, rows, assume_yes=True)
    tx = transaction_id("update")
    _record_transaction(vault, tx, {"operation": "update", "status": "complete" if changed else "no-op", "sources": [r.get("source_id") for r in rows]})
    return {"transaction_id": tx, "status": "complete" if changed else "no-op", "sources": rows}


def list_backups(vault: Vault) -> List[Dict[str, Any]]:
    backups = []
    for path in sorted((vault.state_dir / "backups").glob("*"), reverse=True):
        if path.is_dir():
            backups.append({"id": path.name, "path": str(path), "created_at": path.name})
    return backups


def restore_preview(vault: Vault, backup_id: str) -> Dict[str, Any]:
    if not (vault.state_dir / "backups" / backup_id).is_dir():
        raise ServiceError("not_found", "Backup not found")
    payload = {"backup_id": backup_id}
    return {"backup_id": backup_id, "preview_token": _issue_token(vault, "restore", payload), "transaction_id": transaction_id("restore")}


def restore_apply(vault: Vault, token: str) -> Dict[str, Any]:
    payload = _consume_token(vault, token, "restore")
    path = restore_backup(vault, payload["backup_id"], assume_yes=True)
    tx = transaction_id("restore")
    _record_transaction(vault, tx, {"operation": "restore", "status": "complete", "path": str(path)})
    return {"transaction_id": tx, "status": "complete", "path": str(path)}


def save_annotation(vault: Vault, skill_id: str, values: Dict[str, Any]) -> Dict[str, Any]:
    annotations = vault.annotations
    annotations.setdefault("skills", {}).setdefault(skill_id, {}).update(values)
    annotations["skills"][skill_id]["reviewed_at"] = now_iso()
    write_data(vault.annotations_path, annotations)
    vault.scan()
    tx = transaction_id("review")
    _record_transaction(vault, tx, {"operation": "review.save", "status": "complete", "skill_id": skill_id})
    return {"transaction_id": tx, "skill_id": skill_id, "status": "saved"}


def create_original(vault: Vault, name: str, description: str = "") -> Dict[str, Any]:
    destination = vault.root / "my-skills" / name
    if destination.exists():
        raise ServiceError("already_exists", f"Skill already exists: {name}")
    if not name or not name.replace("-", "").isalnum() or name.lower() != name:
        raise ServiceError("invalid_name", "Skill name must be lowercase letters, digits, and hyphens")
    destination.mkdir(parents=True)
    content = f"---\nname: {name}\ndescription: {description or 'Personal skill; review before enabling.'}\n---\n\n# {name}\n\nDescribe the workflow here.\n"
    (destination / "SKILL.md").write_text(content, encoding="utf-8")
    vault.scan()
    tx = transaction_id("skill")
    _record_transaction(vault, tx, {"operation": "skill.create", "status": "complete", "skill_id": f"my/{name}"})
    return {"transaction_id": tx, "skill_id": f"my/{name}", "path": str(destination)}


def derive_skill(vault: Vault, source_skill_id: str, new_name: str) -> Dict[str, Any]:
    destination = vault.derive(source_skill_id, new_name)
    tx = transaction_id("derive")
    _record_transaction(
        vault,
        tx,
        {
            "operation": "skill.derive",
            "status": "complete",
            "source_skill_id": source_skill_id,
            "skill_id": f"my/{new_name}",
            "path": str(destination),
        },
    )
    return {"transaction_id": tx, "status": "created", "skill_id": f"my/{new_name}", "path": str(destination)}
