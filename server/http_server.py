#!/usr/bin/env python3
"""Local-first API and static server for Skills Vault."""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import urllib.parse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List

APP_ROOT = Path(__file__).resolve().parents[1]
SERVER_ROOT = Path(__file__).resolve().parent
WEB_ROOT = APP_ROOT / "app" / "dist"
VAULT_ROOT = (APP_ROOT.parent / "skills-vault").resolve()
sys.path.insert(0, str(SERVER_ROOT))

from skills_vault.core import Vault, VaultError, load_data  # noqa: E402
from skills_vault.services import (ServiceError, activate_profiles, compare_skills, copy_profile,
                                   create_original, delete_skills_apply, delete_skills_preview,
                                   derive_skill, git_source_apply, git_source_preview,
                                   install_apply, install_preview, list_backups,
                                   managed_selection_payload,
                                   personal_catalog_state,
                                   profiles_payload, restore_apply, restore_preview, save_annotation,
                                   scan_catalog,
                                   save_managed_selection, save_profile, source_policy_apply,
                                   source_policy_preview, source_delete_apply, source_delete_preview,
                                   source_review,
                                   skills_cli_source_apply,
                                   skills_cli_source_preview, update_apply, update_preview)  # noqa: E402


class Handler(BaseHTTPRequestHandler):
    server_version = "SkillsVaultUI/2.0"

    @property
    def vault(self) -> Vault:
        return Vault(VAULT_ROOT)

    def send_json(self, payload: Any, status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; img-src 'self' data:; font-src 'self'")
        self.end_headers()
        self.wfile.write(body)

    def validate_local_request(self, write: bool = False) -> None:
        host_header = self.headers.get("Host", "").lower()
        if host_header.startswith("["):
            host = host_header.split("]", 1)[0].lstrip("[")
        else:
            host = host_header.rsplit(":", 1)[0] if host_header.count(":") == 1 else host_header
        if host not in {"127.0.0.1", "localhost", "::1"}:
            raise ServiceError("invalid_host", "Skills Vault only accepts local requests")
        if write:
            origin = self.headers.get("Origin")
            if origin:
                parsed = urllib.parse.urlparse(origin)
                if parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
                    raise ServiceError("invalid_origin", "Write request origin is not local")

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        try:
            self.validate_local_request()
            if parsed.path == "/api/health":
                self.send_json({
                    "status": "ok",
                    "version": "2.0.0",
                    "vault_root": str(VAULT_ROOT),
                    "frontend_built": (WEB_ROOT / "index.html").is_file(),
                })
                return
            if parsed.path == "/api/status":
                self.send_json(self.status_payload())
                return
            if parsed.path == "/api/catalog/state":
                self.send_json(personal_catalog_state(self.vault))
                return
            if parsed.path == "/api/skills":
                self.send_json(self.skills_payload(parsed.query))
                return
            if parsed.path.startswith("/api/skills/") and parsed.path.endswith("/guide"):
                skill_id = urllib.parse.unquote(parsed.path.removeprefix("/api/skills/").removesuffix("/guide").rstrip("/"))
                self.send_json(self.skill_guide_payload(skill_id))
                return
            if parsed.path.startswith("/api/skills/"):
                skill_id = urllib.parse.unquote(parsed.path.removeprefix("/api/skills/"))
                self.send_json(self.skill_payload(skill_id))
                return
            if parsed.path == "/api/sources":
                self.send_json(self.vault.source_rows())
                return
            if parsed.path.startswith("/api/sources/"):
                source_id = urllib.parse.unquote(parsed.path.removeprefix("/api/sources/"))
                source = next((row for row in self.vault.source_rows() if row["id"] == source_id), None)
                if not source:
                    self.send_json({"error": "Source not found", "code": "not_found"}, HTTPStatus.NOT_FOUND)
                else:
                    source["audit"] = self.source_audit(source_id)
                    self.send_json(source)
                return
            if parsed.path == "/api/drift":
                self.send_json(self.vault.drift_rows())
                return
            if parsed.path == "/api/reviews":
                skills = self.vault.catalog().get("skills", [])
                self.send_json([x for x in skills if x.get("review_status") != "reviewed"])
                return
            if parsed.path == "/api/transactions":
                self.send_json(self.transactions())
                return
            if parsed.path == "/api/profiles":
                self.send_json(self.profiles_payload())
                return
            if parsed.path == "/api/selection":
                self.send_json(managed_selection_payload(self.vault))
                return
            if parsed.path == "/api/backups":
                self.send_json(list_backups(self.vault))
                return
            if parsed.path == "/api/updates":
                self.send_json({"reports": self.update_reports()})
                return
            if parsed.path == "/api/compare":
                params = urllib.parse.parse_qs(parsed.query)
                self.send_json(compare_skills(self.vault, params.get("left", [""])[0], params.get("right", [""])[0]))
                return
            if parsed.path == "/api/conflicts":
                self.send_json(self.vault.catalog().get("conflicts", {}))
                return
            if parsed.path.startswith("/skills/"):
                self.serve_static("/skill.html")
                return
            self.serve_static(parsed.path)
        except VaultError as exc:
            self.send_json({"error": str(exc), "code": getattr(exc, "code", "vault_error"), "details": getattr(exc, "details", {})}, HTTPStatus.UNPROCESSABLE_ENTITY)
        except Exception as exc:
            self.send_json({"error": str(exc), "code": "server_error"}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def read_json(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length > 2_000_000:
            raise ServiceError("payload_too_large", "Request body is too large")
        raw = self.rfile.read(length) if length else b"{}"
        try:
            value = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ServiceError("invalid_json", "Request body must be JSON") from exc
        return value if isinstance(value, dict) else {}

    def do_POST(self) -> None:  # noqa: N802
        try:
            self.validate_local_request(write=True)
            body = self.read_json()
            if self.path == "/api/catalog/scan":
                self.send_json(scan_catalog(self.vault))
                return
            if self.path == "/api/install/preview":
                self.send_json(install_preview(self.vault, body.get("profiles") or self.vault.active_profiles()))
                return
            if self.path == "/api/install/apply":
                self.send_json(install_apply(self.vault, body.get("preview_token", ""), bool(body.get("reset"))))
                return
            if self.path == "/api/skills/delete/preview":
                self.send_json(delete_skills_preview(self.vault, body.get("skill_ids") or []))
                return
            if self.path == "/api/skills/delete/apply":
                self.send_json(delete_skills_apply(self.vault, body.get("preview_token", "")))
                return
            if self.path == "/api/sources/policy/preview":
                self.send_json(source_policy_preview(self.vault, body.get("source_id", ""), bool(body.get("enabled"))))
                return
            if self.path == "/api/sources/policy/apply":
                self.send_json(source_policy_apply(self.vault, body.get("preview_token", "")))
                return
            if self.path == "/api/sources/delete/preview":
                self.send_json(source_delete_preview(self.vault, body.get("source_id", "")))
                return
            if self.path == "/api/sources/delete/apply":
                self.send_json(source_delete_apply(self.vault, body.get("preview_token", "")))
                return
            if self.path == "/api/sources/skills-cli/preview":
                self.send_json(
                    skills_cli_source_preview(
                        self.vault,
                        body.get("source_id", ""),
                        body.get("source_url", ""),
                        bool(body.get("full_depth")),
                        body.get("skills") or [],
                    )
                )
                return
            if self.path == "/api/sources/skills-cli/apply":
                self.send_json(
                    skills_cli_source_apply(self.vault, body.get("preview_token", "")),
                    HTTPStatus.CREATED,
                )
                return
            if self.path == "/api/sources/git/preview":
                self.send_json(
                    git_source_preview(
                        self.vault,
                        body.get("source_id", ""),
                        body.get("source_url", ""),
                        body.get("branch", "main"),
                    )
                )
                return
            if self.path == "/api/sources/git/apply":
                self.send_json(
                    git_source_apply(self.vault, body.get("preview_token", "")),
                    HTTPStatus.CREATED,
                )
                return
            if self.path == "/api/sources/review":
                self.send_json(
                    source_review(
                        self.vault,
                        body.get("source_id", ""),
                        body.get("trust"),
                        body.get("license"),
                    )
                )
                return
            if self.path == "/api/profiles":
                self.send_json(save_profile(self.vault, body.get("name", ""), body), HTTPStatus.CREATED)
                return
            if self.path == "/api/profiles/activate":
                self.send_json(activate_profiles(self.vault, body.get("profiles") or []))
                return
            if self.path == "/api/selection":
                self.send_json(save_managed_selection(self.vault, body.get("selections") or {}))
                return
            if self.path.startswith("/api/profiles/") and self.path.endswith("/copy"):
                source_name = urllib.parse.unquote(self.path.removeprefix("/api/profiles/").removesuffix("/copy"))
                self.send_json(copy_profile(self.vault, source_name, body.get("target_name", "")), HTTPStatus.CREATED)
                return
            if self.path == "/api/updates/check":
                self.send_json(update_preview(self.vault, body.get("source_ids")))
                return
            if self.path == "/api/updates/apply":
                self.send_json(update_apply(self.vault, body.get("preview_token", "")))
                return
            if self.path == "/api/backups/restore/preview":
                self.send_json(restore_preview(self.vault, body.get("backup_id", "")))
                return
            if self.path == "/api/backups/restore/apply":
                self.send_json(restore_apply(self.vault, body.get("preview_token", "")))
                return
            if self.path == "/api/skills/original":
                self.send_json(create_original(self.vault, body.get("name", ""), body.get("description", "")), HTTPStatus.CREATED)
                return
            if self.path == "/api/derive":
                self.send_json(
                    derive_skill(self.vault, body.get("source_skill_id", ""), body.get("new_name", "")),
                    HTTPStatus.CREATED,
                )
                return
            self.send_json({"error": "Not found", "code": "not_found"}, HTTPStatus.NOT_FOUND)
        except VaultError as exc:
            self.send_json({"error": str(exc), "code": getattr(exc, "code", "vault_error"), "details": getattr(exc, "details", {})}, HTTPStatus.UNPROCESSABLE_ENTITY)
        except Exception as exc:
            self.send_json({"error": str(exc), "code": "server_error"}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_PUT(self) -> None:  # noqa: N802
        try:
            self.validate_local_request(write=True)
            body = self.read_json()
            if self.path.startswith("/api/profiles/"):
                name = urllib.parse.unquote(self.path.removeprefix("/api/profiles/"))
                self.send_json(save_profile(self.vault, name, body))
                return
            if self.path.startswith("/api/annotations/"):
                skill_id = urllib.parse.unquote(self.path.removeprefix("/api/annotations/"))
                self.send_json(save_annotation(self.vault, skill_id, body))
                return
            self.send_json({"error": "Not found", "code": "not_found"}, HTTPStatus.NOT_FOUND)
        except VaultError as exc:
            self.send_json({"error": str(exc), "code": getattr(exc, "code", "vault_error")}, HTTPStatus.UNPROCESSABLE_ENTITY)

    def update_reports(self) -> List[Dict[str, Any]]:
        reports = []
        for path in sorted((self.vault.root / "catalog" / "updates").glob("*.json"), reverse=True):
            try:
                reports.append(load_data(path))
            except VaultError:
                continue
        return reports[:20]

    def transactions(self) -> List[Dict[str, Any]]:
        rows = []
        for path in sorted((self.vault.state_dir / "transactions").glob("*.json"), reverse=True):
            try:
                rows.append(load_data(path))
            except VaultError:
                continue
        return rows[:50]

    def source_audit(self, source_id: str) -> Dict[str, Any]:
        from skills_vault.ops import source_audit
        return source_audit(self.vault, source_id)

    def status_payload(self) -> Dict[str, Any]:
        vault = self.vault
        catalog = vault.catalog()
        state = load_data(vault.state_dir / "install-state.json", {"links": []})
        return {
            "root": str(VAULT_ROOT),
            "app_version": "2.0.0",
            "generated_at": catalog.get("generated_at"),
            "active_profiles": vault.active_profiles(),
            "catalog": catalog.get("counts", {}),
            "conflicts": catalog.get("conflicts", {}),
            "sources": vault.source_rows(),
            "managed_links": len(state.get("links", [])),
            "last_backup": state.get("backup"),
            "derived_drift": vault.drift_rows(),
            "catalog_state": personal_catalog_state(vault),
        }

    def skills_payload(self, query: str) -> Dict[str, Any]:
        catalog = self.vault.catalog()
        params = urllib.parse.parse_qs(query)
        search = params.get("q", [""])[0].strip().lower()
        source = params.get("source", [""])[0]
        classification = params.get("classification", [""])[0]
        review = params.get("review", [""])[0]
        skills = catalog.get("skills", [])
        if search:
            skills = [item for item in skills if search in " ".join(str(item.get(key) or "") for key in ("id", "name", "description", "title_zh", "summary_zh", "source_id")).lower()]
        if source:
            skills = [item for item in skills if item.get("source_id") == source]
        if classification:
            skills = [item for item in skills if item.get("classification") == classification]
        if review:
            skills = [item for item in skills if item.get("review_status") == review]
        return {"total": len(skills), "skills": skills}

    def skill_payload(self, skill_id: str) -> Dict[str, Any]:
        matches = [item for item in self.vault.catalog().get("skills", []) if item.get("id") == skill_id]
        if not matches:
            self.send_json({"error": "Skill not found", "code": "not_found"}, HTTPStatus.NOT_FOUND)
            return {}
        entry = dict(matches[0])
        enablement = {}
        for platform in ("codex", "claude"):
            try:
                details = self.vault.resolve_profile_details(self.vault.active_profiles(), platform)
                enablement[platform] = details["status"].get(skill_id, {"selected": False, "installed": False, "state": "not-selected", "reasons": []})
            except VaultError as exc:
                enablement[platform] = {"selected": False, "state": "error", "error": str(exc), "reasons": []}
        entry["enablement"] = enablement
        entry["source"] = next((row for row in self.vault.source_rows() if row["id"] == entry.get("source_id")), None)
        entry["origin_detail"] = entry.get("origin")
        return entry

    def skill_guide_payload(self, skill_id: str) -> Dict[str, Any]:
        matches = [item for item in self.vault.catalog().get("skills", []) if item.get("id") == skill_id]
        if not matches:
            raise ServiceError("not_found", "Skill not found")
        safe_name = skill_id.replace("/", "--")
        guide_path = VAULT_ROOT / "docs" / "skill-guides" / f"{safe_name}.md"
        if guide_path.exists() and guide_path.is_file():
            return {"skill_id": skill_id, "exists": True, "path": str(guide_path.relative_to(VAULT_ROOT)), "markdown": guide_path.read_text(encoding="utf-8")}
        entry = matches[0]
        fallback = "\n".join([
            f"# {entry.get('name')}",
            "",
            f"> 此 Skill 的说明文档尚未创建。请添加 `{safe_name}.md` 后再查看完整内容。",
        ])
        return {"skill_id": skill_id, "exists": False, "path": str(guide_path.relative_to(VAULT_ROOT)), "markdown": fallback}

    def profiles_payload(self) -> Dict[str, Any]:
        return profiles_payload(self.vault)

    def serve_static(self, request_path: str) -> None:
        if not (WEB_ROOT / "index.html").is_file():
            self.send_error(
                HTTPStatus.SERVICE_UNAVAILABLE,
                "Frontend build not found. Run npm run build in app/.",
            )
            return
        candidate = (WEB_ROOT / (request_path.lstrip("/") or "index.html")).resolve()
        if WEB_ROOT.resolve() not in candidate.parents:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if not candidate.exists() or not candidate.is_file():
            candidate = WEB_ROOT / "index.html"
        body = candidate.read_bytes()
        content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; img-src 'self' data:; font-src 'self'")
        self.end_headers()
        self.wfile.write(body)

    def serve_file(self, candidate: Path) -> None:
        if not candidate.exists() or not candidate.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        body = candidate.read_bytes()
        content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'self'; img-src 'self' data:")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        sys.stderr.write("[skills-vault-ui] " + (format % args) + "\n")


def main() -> int:
    global VAULT_ROOT, WEB_ROOT
    parser = argparse.ArgumentParser(description="Serve the local Skills Vault UI and API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--vault-root",
        default=os.environ.get("SKILLS_VAULT_ROOT", str(VAULT_ROOT)),
        help="Path to the Skills Vault data workspace",
    )
    parser.add_argument(
        "--static-root",
        default=str(WEB_ROOT),
        help="Path to the built React application",
    )
    args = parser.parse_args()
    VAULT_ROOT = Path(args.vault_root).expanduser().resolve()
    WEB_ROOT = Path(args.static_root).expanduser().resolve()
    required = [VAULT_ROOT / "registry.yaml", VAULT_ROOT / "profiles"]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        parser.error("Invalid Vault data workspace; missing: " + ", ".join(missing))
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Skills Vault UI: http://{args.host}:{args.port}/")
    print(f"Vault data: {VAULT_ROOT}")
    print(f"Frontend: {WEB_ROOT}")
    print("Local API enabled — write operations require preview tokens and remain local to this vault.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Skills Vault UI.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
