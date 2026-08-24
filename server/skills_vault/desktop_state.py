from __future__ import annotations

import hashlib
import json
import secrets
import shutil
from pathlib import Path
from typing import Any, Dict, Optional

from .core import Vault, VaultError, load_data, now_iso, write_data
from .migrations import (
    apply_import,
    apply_web_v2_migration,
    create_vault,
    import_plan,
    inspect_candidate,
    vault_create_plan,
    web_v2_migration_plan,
)


class DesktopStateError(VaultError):
    def __init__(self, code: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.details = details or {}


class DesktopState:
    """Desktop-only configuration and onboarding operations.

    This state intentionally lives outside every Vault. It only stores the last
    selected Vault, short-lived preview tokens, and desktop operation records.
    """

    def __init__(self, config_root: Path, default_vault_root: Path):
        self.root = config_root.expanduser().resolve()
        self.default_vault_root = default_vault_root.expanduser().resolve()
        self.config_path = self.root / "desktop.json"
        self.tokens_root = self.root / "tokens"
        self.transactions_root = self.root / "transactions"
        self._runtime_active: Optional[Path] = None

    def _config(self) -> Dict[str, Any]:
        return load_data(
            self.config_path,
            {"schema_version": 1, "active_vault": None, "recent_vaults": []},
        )

    @staticmethod
    def _is_vault(root: Path) -> bool:
        return root.is_dir() and (root / "registry.yaml").is_file() and (root / "profiles").is_dir()

    def active_vault_root(self) -> Optional[Path]:
        if self._runtime_active and self._is_vault(self._runtime_active):
            return self._runtime_active
        value = self._config().get("active_vault")
        if not value:
            return None
        root = Path(str(value)).expanduser().resolve()
        return root if self._is_vault(root) else None

    def select(self, root: Path, remember: bool = True) -> Path:
        target = root.expanduser().resolve()
        if not self._is_vault(target):
            raise DesktopStateError(
                "invalid_vault",
                "所选目录不是可打开的 Skills Vault",
                {"path": str(target)},
            )
        self._runtime_active = target
        if remember:
            config = self._config()
            recent = [str(target)] + [
                str(item) for item in config.get("recent_vaults", []) if str(item) != str(target)
            ]
            config.update(
                {
                    "schema_version": 1,
                    "active_vault": str(target),
                    "recent_vaults": recent[:10],
                    "updated_at": now_iso(),
                }
            )
            write_data(self.config_path, config)
        return target

    def _clear_active(self) -> Optional[Path]:
        config = self._config()
        previous = self.active_vault_root()
        config.update({"schema_version": 1, "active_vault": None, "updated_at": now_iso()})
        write_data(self.config_path, config)
        self._runtime_active = None
        return previous

    def leave(self) -> Dict[str, Any]:
        """Clear the active Vault without touching any Vault files."""
        previous = self._clear_active()
        transaction_id = f"desktop_{secrets.token_hex(6)}"
        result = {
            "transaction_id": transaction_id,
            "status": "complete",
            "action": "leave",
            "previous_vault": str(previous) if previous else None,
        }
        self._record(transaction_id, result)
        return result

    def status(self) -> Dict[str, Any]:
        config = self._config()
        configured = config.get("active_vault")
        active = self.active_vault_root()
        return {
            "mode": "ready" if active else "onboarding",
            "active_vault": str(active) if active else None,
            "configured_vault": configured,
            "configured_vault_missing": bool(configured and not active),
            "recent_vaults": config.get("recent_vaults", []),
            "default_vault": str(self.default_vault_root),
            "config_root": str(self.root),
        }

    def _fingerprint(self) -> str:
        payload = json.dumps(self._config(), ensure_ascii=False, sort_keys=True).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def _issue(self, action: str, plan: Dict[str, Any]) -> str:
        token = secrets.token_urlsafe(24)
        write_data(
            self.tokens_root / f"{token}.json",
            {
                "token": token,
                "action": action,
                "issued_at": now_iso(),
                "config_fingerprint": self._fingerprint(),
                "plan": plan,
            },
        )
        return token

    def _consume(self, token: str) -> Dict[str, Any]:
        path = self.tokens_root / f"{token}.json"
        if not path.is_file():
            raise DesktopStateError("invalid_token", "Preview 已失效，请重新预览")
        record = load_data(path)
        if record.get("config_fingerprint") != self._fingerprint():
            raise DesktopStateError("stale_preview", "桌面配置已变化，请重新预览")
        path.unlink()
        return record

    def preview(
        self,
        action: str,
        source_path: str = "",
        destination: str = "",
    ) -> Dict[str, Any]:
        if action == "leave":
            plan = {"source": str(self.active_vault_root()) if self.active_vault_root() else None}
        elif action == "create":
            plan = vault_create_plan(destination or self.default_vault_root)
        elif action == "open":
            candidate = inspect_candidate(source_path)
            if candidate.get("kind") != "vault":
                raise DesktopStateError(
                    "migration_required" if candidate.get("kind") == "web-v2-vault" else "invalid_vault",
                    "这是旧版 Web Vault，请使用“迁移旧版”" if candidate.get("kind") == "web-v2-vault" else "该目录不是可打开的 Skills Vault",
                    {"candidate": candidate},
                )
            plan = {"source": candidate["path"], "candidate": candidate}
        elif action == "import":
            target = destination or self.default_vault_root
            candidate = inspect_candidate(source_path)
            if candidate.get("kind") not in ("git-skills-repository", "skills-folder"):
                raise DesktopStateError(
                    "invalid_import_source",
                    "请选择包含 SKILL.md 的仓库或文件夹",
                    {"candidate": candidate},
                )
            plan = {
                "source": candidate["path"],
                "destination": vault_create_plan(target)["destination"],
                "candidate": candidate,
                "mode": "personal",
            }
        elif action == "migrate":
            plan = web_v2_migration_plan(source_path, destination or self.default_vault_root)
        else:
            raise DesktopStateError("invalid_action", "不支持的首次启动操作")
        token = self._issue(action, plan)
        return {"action": action, "preview_token": token, "plan": plan}

    def _record(self, transaction_id: str, payload: Dict[str, Any]) -> None:
        write_data(
            self.transactions_root / f"{transaction_id}.json",
            {"transaction_id": transaction_id, "created_at": now_iso(), **payload},
        )

    @staticmethod
    def _cleanup_new_vault(destination: Path, destination_existed: bool) -> None:
        if not destination.exists():
            return
        if destination_existed:
            for child in destination.iterdir():
                if child.is_dir() and not child.is_symlink():
                    shutil.rmtree(child)
                else:
                    child.unlink()
        else:
            shutil.rmtree(destination)

    def apply(self, token: str) -> Dict[str, Any]:
        record = self._consume(token)
        action = str(record.get("action"))
        plan = record.get("plan") or {}
        transaction_id = f"desktop_{secrets.token_hex(6)}"
        destination: Optional[Path] = None
        try:
            if action == "create":
                destination = Path(plan["destination"])
                result = create_vault(destination)
                active = result.root
            elif action == "open":
                active = Path(plan["source"])
                self.select(active, remember=False)
            elif action == "import":
                destination = Path(plan["destination"])
                existed = destination.exists()
                created = create_vault(destination)
                try:
                    import_preview = import_plan(created, plan["source"], "personal")
                    imported = apply_import(created, import_preview)
                except Exception:
                    self._cleanup_new_vault(destination, existed)
                    raise
                active = created.root
                plan["imported"] = imported.get("skills", [])
            elif action == "migrate":
                destination = Path(plan["destination"])
                migrated = apply_web_v2_migration(plan)
                active = Path(migrated["destination"])
            elif action == "leave":
                previous = self._clear_active()
                result = {
                    "transaction_id": transaction_id,
                    "status": "complete",
                    "action": action,
                    "previous_vault": str(previous) if previous else None,
                }
                self._record(transaction_id, result)
                return result
            else:
                raise DesktopStateError("invalid_action", "Preview 操作类型无效")
            active = self.select(active)
            result = {
                "transaction_id": transaction_id,
                "status": "complete",
                "action": action,
                "active_vault": str(active),
                "imported_skills": plan.get("imported", []),
            }
            self._record(transaction_id, result)
            return result
        except Exception as exc:
            self._record(
                transaction_id,
                {
                    "status": "failed",
                    "action": action,
                    "destination": str(destination) if destination else None,
                    "error": str(exc),
                },
            )
            raise
