from __future__ import annotations

import datetime as dt
import fnmatch
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from .platform_adapter import SUPPORTED_PLATFORMS, current_platform


CATALOG_SCHEMA_VERSION = 2
SKILL_NAME_RE = re.compile(r"[a-z0-9][a-z0-9-]{0,63}")
WINDOWS_RESERVED_NAMES = {
    "con", "prn", "aux", "nul",
    *(f"com{index}" for index in range(1, 10)),
    *(f"lpt{index}" for index in range(1, 10)),
}


def valid_skill_name(name: str) -> bool:
    return bool(SKILL_NAME_RE.fullmatch(name)) and name.lower() not in WINDOWS_RESERVED_NAMES


class VaultError(RuntimeError):
    pass


def now_iso() -> str:
    return dt.datetime.now().astimezone().replace(microsecond=0).isoformat()


def load_data(path: Path, default: Any = None) -> Any:
    if not path.exists():
        if default is not None:
            return default
        raise VaultError(f"Missing configuration: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise VaultError(
            f"{path} must use JSON syntax (valid YAML 1.2): {exc}"
        ) from exc


def write_data(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def run(
    args: Sequence[str],
    cwd: Optional[Path] = None,
    check: bool = True,
    capture: bool = True,
    env: Optional[Dict[str, str]] = None,
    timeout: Optional[int] = None,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            list(args),
            cwd=str(cwd) if cwd else None,
            check=check,
            text=True,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.PIPE if capture else None,
            env=env,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise VaultError(f"Required program not found: {args[0]}") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        raise VaultError(f"Command failed: {' '.join(args)}\n{detail}") from exc
    except subprocess.TimeoutExpired as exc:
        raise VaultError(f"Command timed out after {timeout}s: {' '.join(args)}") from exc


def git(repo: Path, *args: str, check: bool = True) -> str:
    from .executable_resolver import resolve_executable
    from .platform_adapter import current_platform

    resolved = resolve_executable("git", current_platform())
    if not resolved:
        raise VaultError("Required program not found: git")
    result = run([str(resolved.path), *args], cwd=repo, check=check)
    return (result.stdout or "").strip()


def git_clean(repo: Path) -> bool:
    return not git(repo, "status", "--porcelain")


def git_commit(repo: Path) -> str:
    return git(repo, "rev-parse", "HEAD")


def git_modified_at(repo: Path, relative: str) -> Optional[str]:
    value = git(repo, "log", "-1", "--format=%cI", "--", relative, check=False)
    return value or None


def tree_fingerprint(path: Path, ignore_origin: bool = False) -> str:
    digest = hashlib.sha256()
    if not path.exists():
        return "missing"
    for item in sorted(p for p in path.rglob("*") if p.is_file()):
        rel = item.relative_to(path).as_posix()
        if "/.git/" in f"/{rel}/" or rel.startswith(".git/"):
            continue
        if ignore_origin and rel == ".vault-origin.json":
            continue
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(item.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def git_tree_fingerprint(repo: Path, commit: str, relative_dir: str) -> str:
    listing = git(repo, "ls-tree", "-r", commit, "--", relative_dir, check=False)
    if not listing:
        return "missing"
    digest = hashlib.sha256()
    prefix = relative_dir.rstrip("/") + "/"
    for line in listing.splitlines():
        metadata, path = line.split("\t", 1)
        rel = path[len(prefix) :] if path.startswith(prefix) else path
        blob = metadata.split()[2]
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(blob.encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return ""
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    lowered = value.lower()
    if lowered in ("true", "false"):
        return lowered == "true"
    if value.startswith("[") and value.endswith("]"):
        try:
            return json.loads(value.replace("'", '"'))
        except json.JSONDecodeError:
            return [part.strip() for part in value[1:-1].split(",") if part.strip()]
    return value


def parse_frontmatter(text: str) -> Tuple[Dict[str, Any], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return {}, text
    result: Dict[str, Any] = {}
    i = 1
    while i < end:
        line = lines[i]
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not match:
            i += 1
            continue
        key, raw = match.groups()
        if raw in (">", "|", ">-", "|-"):
            chunks: List[str] = []
            i += 1
            while i < end and (lines[i].startswith(" ") or not lines[i].strip()):
                chunks.append(lines[i].strip())
                i += 1
            result[key] = " ".join(part for part in chunks if part)
            continue
        result[key] = parse_scalar(raw)
        i += 1
    return result, "\n".join(lines[end + 1 :])


def replace_frontmatter_name(text: str, name: str) -> str:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return f"---\nname: {name}\ndescription: Derived skill. Review before enabling.\n---\n\n{text}"
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        raise VaultError("Cannot derive a skill with unterminated frontmatter")
    for index in range(1, end):
        if re.match(r"^name:\s*", lines[index]):
            lines[index] = f"name: {name}"
            break
    else:
        lines.insert(1, f"name: {name}")
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def classify(relative_skill_md: str, rules: Sequence[Dict[str, str]]) -> str:
    for rule in rules:
        if fnmatch.fnmatchcase(relative_skill_md, rule["pattern"]):
            return rule["as"]
    return "unknown"


def risk_signals(skill_dir: Path, text: str, metadata: Dict[str, Any]) -> List[str]:
    signals: Set[str] = set()
    files = [p for p in skill_dir.rglob("*") if p.is_file() and ".git" not in p.parts]
    if any("scripts" in p.relative_to(skill_dir).parts for p in files):
        signals.add("scripts")
    if any(p.suffix.lower() in (".sh", ".bash", ".zsh", ".ps1") for p in files):
        signals.add("shell-code")
    if re.search(r"(?:curl|wget|Invoke-WebRequest|https?://)", text, re.I):
        signals.add("network")
    if re.search(r"!`[^`]+`", text):
        signals.add("claude-dynamic-shell")
    if "allowed-tools" in metadata:
        signals.add("tool-grants")
    if re.search(r"\b(?:rm\s+-rf|reset\s+--hard|force push|--force)\b", text, re.I):
        signals.add("destructive-instructions")
    if re.search(r"\b(?:MCP|hook|subagent)\b", text, re.I):
        signals.add("agent-extension")
    return sorted(signals)


def script_inventory(skill_dir: Path) -> List[str]:
    result: List[str] = []
    executable_suffixes = {".sh", ".bash", ".zsh", ".ps1", ".py", ".js", ".ts", ".mjs"}
    for path in skill_dir.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        rel = path.relative_to(skill_dir)
        if "scripts" in rel.parts or path.suffix.lower() in executable_suffixes:
            result.append(rel.as_posix())
    return sorted(result)


def compatibility(skill_dir: Path, text: str, annotation: Dict[str, Any]) -> Dict[str, Any]:
    override = annotation.get("compatibility")
    if override:
        return override
    signals: List[str] = []
    level = "both"
    if re.search(r"!`[^`]+`|\$ARGUMENTS|\$\{CLAUDE_(?:PROJECT_DIR|SESSION_ID)\}", text):
        level = "partial"
        signals.append("Claude-specific dynamic context syntax")
    if "allowed-tools:" in text or "disable-model-invocation:" in text:
        signals.append("Claude Code frontmatter extension")
    if (skill_dir / "agents" / "openai.yaml").exists():
        signals.append("Codex metadata present")
    return {"level": level, "platforms": list(SUPPORTED_PLATFORMS), "notes": signals}


class Vault:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.registry_path = self.root / "registry.yaml"
        self.lock_path = self.root / "lock.yaml"
        self.annotations_path = self.root / "annotations" / "skills.yaml"
        self.state_dir = self.root / ".vault"

    @property
    def registry(self) -> Dict[str, Any]:
        return load_data(self.registry_path)

    @property
    def annotations(self) -> Dict[str, Any]:
        return load_data(self.annotations_path, {"schema_version": 1, "skills": {}})

    @property
    def deleted_skills_path(self) -> Path:
        return self.state_dir / "deleted-skills.json"

    @property
    def source_policies_path(self) -> Path:
        return self.state_dir / "source-policies.json"

    def source_policies(self) -> Dict[str, Any]:
        return load_data(self.source_policies_path, {"schema_version": 1, "sources": {}})

    def disabled_source_ids(self) -> Set[str]:
        rows = self.source_policies().get("sources") or {}
        return {source_id for source_id, policy in rows.items() if policy.get("enabled") is False}

    def deleted_skill_ids(self) -> Set[str]:
        data = load_data(self.deleted_skills_path, {"schema_version": 1, "skills": {}})
        return set((data.get("skills") or {}).keys())

    def source_path(self, source: Dict[str, Any]) -> Path:
        return (self.root / source["path"]).resolve()

    def source_kind(self, source: Dict[str, Any]) -> str:
        return str(source.get("kind") or "git")

    def source_skill_root(self, source: Dict[str, Any]) -> Path:
        root = self.source_path(source)
        relative = source.get("skill_root")
        return (root / relative).resolve() if relative else root

    def source_revision(self, source: Dict[str, Any]) -> Optional[str]:
        root = self.source_path(source)
        if self.source_kind(source) == "git":
            return git_commit(root) if (root / ".git").exists() else None
        if self.source_kind(source) == "local-copy":
            return tree_fingerprint(root) if root.is_dir() else None
        lock_path = root / "skills-lock.json"
        if not lock_path.is_file():
            return None
        return hashlib.sha256(lock_path.read_bytes()).hexdigest()

    def source_rows(self) -> List[Dict[str, Any]]:
        rows = []
        lock = load_data(self.lock_path, {"sources": {}})
        policies = self.source_policies().get("sources") or {}
        for source_id, source in self.registry["sources"].items():
            repo = self.source_path(source)
            kind = self.source_kind(source)
            skill_root = self.source_skill_root(source)
            if kind == "git":
                exists = (repo / ".git").exists()
            elif kind == "skills-cli":
                exists = skill_root.is_dir() and (repo / "skills-lock.json").is_file()
            else:
                exists = skill_root.is_dir()
            revision = self.source_revision(source) if exists else None
            lock_row = lock.get("sources", {}).get(source_id, {})
            row = {
                "id": source_id,
                "kind": kind,
                "update_policy": source.get("update_policy", "strict" if kind == "git" else "self-managed"),
                "path": str(repo),
                "skill_root": str(skill_root),
                "url": source["url"],
                "branch": source.get("branch", "main") if kind == "git" else None,
                "trust": source.get("trust", "unreviewed"),
                "license": source.get("license", "unknown"),
                "exists": exists,
                "commit": revision,
                "locked": lock_row.get("commit") if kind == "git" else None,
                "observed_revision": lock_row.get("revision") if kind != "git" else None,
                "dirty": not git_clean(repo) if exists and kind == "git" else False if exists else None,
                "enabled": policies.get(source_id, {}).get("enabled", True),
                "policy_updated_at": policies.get(source_id, {}).get("updated_at"),
                "policy_transaction_id": policies.get(source_id, {}).get("transaction_id"),
            }
            if exists and kind == "git":
                remote_ref = f"refs/remotes/origin/{row['branch']}"
                row["remote_commit"] = git(repo, "rev-parse", remote_ref, check=False) or None
                row["remote_url"] = git(repo, "remote", "get-url", "origin", check=False) or None
                row["dirty_files"] = [line[3:] for line in git(repo, "status", "--porcelain", check=False).splitlines() if len(line) >= 4]
                row["head_modified_at"] = git(repo, "show", "-s", "--format=%cI", "HEAD", check=False) or None
            elif exists:
                row["remote_commit"] = None
                row["remote_url"] = source.get("url") if kind == "skills-cli" else None
                row["dirty_files"] = []
                observed_file = repo / "skills-lock.json" if kind == "skills-cli" else skill_root
                row["head_modified_at"] = dt.datetime.fromtimestamp(observed_file.stat().st_mtime).astimezone().replace(microsecond=0).isoformat()
            else:
                row["dirty_files"] = []
                row["head_modified_at"] = None
            row["hold"] = bool(source.get("hold", False))
            row["pin"] = source.get("pin")
            rows.append(row)
        return rows

    def _scan_source(
        self,
        source_id: str,
        source: Dict[str, Any],
        annotations: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        repo = self.source_path(source)
        kind = self.source_kind(source)
        skill_root = self.source_skill_root(source)
        if kind == "git" and not (repo / ".git").exists():
            raise VaultError(f"Source {source_id} is not cloned at {repo}")
        if kind == "skills-cli" and (not skill_root.is_dir() or not (repo / "skills-lock.json").is_file()):
            raise VaultError(f"Source {source_id} is not installed at {repo}")
        if kind == "local-copy" and not skill_root.is_dir():
            raise VaultError(f"Source {source_id} is missing at {skill_root}")
        commit = self.source_revision(source)
        entries: List[Dict[str, Any]] = []
        for skill_md in sorted(skill_root.rglob("SKILL.md")):
            if ".git" in skill_md.parts:
                continue
            relative_md = skill_md.relative_to(skill_root).as_posix()
            skill_dir = skill_md.parent
            text = skill_md.read_text(encoding="utf-8", errors="replace")
            metadata, _ = parse_frontmatter(text)
            name = str(metadata.get("name") or skill_dir.name).strip()
            if not valid_skill_name(name):
                continue
            entry_id = f"{source_id}/{name}"
            annotation = annotations.get(entry_id, {})
            modified_at = (
                git_modified_at(repo, skill_dir.relative_to(repo).as_posix())
                if kind == "git"
                else dt.datetime.fromtimestamp(skill_md.stat().st_mtime).astimezone().replace(microsecond=0).isoformat()
            )
            review_status = annotation.get("review_status", "unreviewed")
            reviewed_at = annotation.get("reviewed_at")
            if reviewed_at and modified_at and modified_at[:10] > reviewed_at[:10]:
                review_status = "stale-review"
            entries.append(
                {
                    "id": entry_id,
                    "source_id": source_id,
                    "name": name,
                    "path": str(skill_dir.relative_to(self.root).as_posix()),
                    "source_relative_path": skill_dir.relative_to(skill_root).as_posix(),
                    "source_kind": kind,
                    "description": str(metadata.get("description", "")).strip(),
                    "classification": classify(relative_md, source.get("classify", [])),
                    "source_commit": commit,
                    "upstream_modified_at": modified_at,
                    "synced_at": load_data(self.lock_path, {"generated_at": None}).get("generated_at"),
                    "reviewed_at": reviewed_at,
                    "review_status": review_status,
                    "title_zh": annotation.get("title_zh"),
                    "summary_zh": annotation.get("summary_zh"),
                    "recommended_for": annotation.get("recommended_for", []),
                    "not_recommended_for": annotation.get("not_recommended_for", []),
                    "requires": annotation.get("requires", []),
                    "recommends": annotation.get("recommends", []),
                    "routes_to": annotation.get("routes_to", []),
                    "compatibility": compatibility(skill_dir, text, annotation),
                    "scripts": script_inventory(skill_dir),
                    "risk_signals": risk_signals(skill_dir, text, metadata),
                    "fingerprint": tree_fingerprint(skill_dir),
                    "frontmatter": metadata,
                    "invocation": {
                        "mode": "explicit-only"
                        if metadata.get("disable-model-invocation") is True
                        else "implicit-or-explicit",
                        "codex": f"${name}",
                        "claude": f"/{name}",
                        "lux": f"/skill load {name}",
                    },
                }
            )
        return entries

    def _scan_personal(self, annotations: Dict[str, Any]) -> List[Dict[str, Any]]:
        base = self.root / "my-skills"
        entries: List[Dict[str, Any]] = []
        for skill_md in sorted(base.glob("*/SKILL.md")):
            skill_dir = skill_md.parent
            text = skill_md.read_text(encoding="utf-8", errors="replace")
            metadata, _ = parse_frontmatter(text)
            name = str(metadata.get("name") or skill_dir.name).strip()
            if not valid_skill_name(name):
                continue
            entry_id = f"my/{name}"
            annotation = annotations.get(entry_id, {})
            origin = load_data(skill_dir / ".vault-origin.json", {})
            modified = git_modified_at(self.root, skill_dir.relative_to(self.root).as_posix())
            entries.append(
                {
                    "id": entry_id,
                    "source_id": "my",
                    "name": name,
                    "path": skill_dir.relative_to(self.root).as_posix(),
                    "source_relative_path": None,
                    "description": str(metadata.get("description", "")).strip(),
                    "classification": "published",
                    "source_commit": git(self.root, "rev-parse", "HEAD", check=False) or None,
                    "upstream_modified_at": None,
                    "synced_at": None,
                    "local_modified_at": modified,
                    "reviewed_at": annotation.get("reviewed_at"),
                    "review_status": annotation.get("review_status", "review-needed"),
                    "title_zh": annotation.get("title_zh"),
                    "summary_zh": annotation.get("summary_zh"),
                    "recommended_for": annotation.get("recommended_for", []),
                    "not_recommended_for": annotation.get("not_recommended_for", []),
                    "requires": annotation.get("requires", []),
                    "recommends": annotation.get("recommends", []),
                    "routes_to": annotation.get("routes_to", []),
                    "compatibility": compatibility(skill_dir, text, annotation),
                    "scripts": script_inventory(skill_dir),
                    "risk_signals": risk_signals(skill_dir, text, metadata),
                    "fingerprint": tree_fingerprint(skill_dir, ignore_origin=True),
                    "frontmatter": metadata,
                    "invocation": {
                        "mode": "explicit-only"
                        if metadata.get("disable-model-invocation") is True
                        else "implicit-or-explicit",
                        "codex": f"${name}",
                        "claude": f"/{name}",
                        "lux": f"/skill load {name}",
                    },
                    "origin": origin or None,
                }
            )
        return entries

    def build_catalog(self) -> Dict[str, Any]:
        annotation_map = self.annotations.get("skills", {})
        entries: List[Dict[str, Any]] = []
        for source_id, source in self.registry["sources"].items():
            entries.extend(self._scan_source(source_id, source, annotation_map))
        entries.extend(self._scan_personal(annotation_map))
        deleted_ids = self.deleted_skill_ids()
        entries = [entry for entry in entries if entry["id"] not in deleted_ids]
        entries.sort(key=lambda item: (item["name"].lower(), item["source_id"], item["path"]))

        by_id: Dict[str, List[Dict[str, Any]]] = {}
        by_name: Dict[str, List[Dict[str, Any]]] = {}
        for entry in entries:
            by_id.setdefault(entry["id"], []).append(entry)
            by_name.setdefault(entry["name"].lower(), []).append(entry)
        duplicate_ids = {key: value for key, value in by_id.items() if len(value) > 1}
        conflicts = {key: value for key, value in by_name.items() if len(value) > 1}

        known_names = set(by_name)
        for entry in entries:
            text = (self.root / entry["path"] / "SKILL.md").read_text(
                encoding="utf-8", errors="replace"
            )
            candidates: Set[str] = set()
            for token in re.findall(r"(?:\$|/)([a-z0-9][a-z0-9-]{1,63})", text, re.I):
                if token.lower() in known_names and token.lower() != entry["name"].lower():
                    candidates.add(token.lower())
            entry["dependency_candidates"] = sorted(candidates)

        fingerprint_payload = [
            {key: value for key, value in entry.items() if key not in ("synced_at",)}
            for entry in entries
        ]
        fingerprint = hashlib.sha256(
            json.dumps(fingerprint_payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()
        return {
            "schema_version": CATALOG_SCHEMA_VERSION,
            "generated_at": now_iso(),
            "fingerprint": fingerprint,
            "counts": {
                "skills": len(entries),
                "published": sum(e["classification"] == "published" for e in entries),
                "conflict_groups": len(conflicts),
                "duplicate_ids": len(duplicate_ids),
            },
            "duplicate_ids": {
                key: [entry["path"] for entry in value] for key, value in duplicate_ids.items()
            },
            "conflicts": {
                key: [entry["id"] for entry in value] for key, value in conflicts.items()
            },
            "skills": entries,
        }

    def save_catalog(self, catalog: Dict[str, Any]) -> None:
        catalog_dir = self.root / "catalog"
        write_data(catalog_dir / "catalog.json", catalog)
        lines = [
            "# Skills catalog",
            "",
            f"> Generated {catalog['generated_at']}; {catalog['counts']['skills']} discovered, "
            f"{catalog['counts']['published']} published, {catalog['counts']['conflict_groups']} name conflict groups.",
            "",
            "| ID | 中文标题 / Description | Class | Invocation | Compatibility | Upstream modified | Review | Risks |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for entry in catalog["skills"]:
            title = entry.get("title_zh") or entry.get("summary_zh") or entry.get("description") or "—"
            title = str(title).replace("|", "\\|").replace("\n", " ")
            risks = ", ".join(entry["risk_signals"]) or "—"
            lines.append(
                f"| `{entry['id']}` | {title} | {entry['classification']} | {entry['invocation']['mode']} | "
                f"{entry['compatibility']['level']} | {entry.get('upstream_modified_at') or entry.get('local_modified_at') or '—'} | "
                f"{entry['review_status']} | {risks} |"
            )
        lines.extend(["", "Generated file; edit `annotations/skills.yaml`, not this document.", ""])
        (catalog_dir / "skills.md").write_text("\n".join(lines), encoding="utf-8")

        conflict_lines = ["# Skill name conflicts", ""]
        if not catalog["conflicts"]:
            conflict_lines.append("No cross-source name conflicts.")
        else:
            for name, ids in sorted(catalog["conflicts"].items()):
                conflict_lines.extend([f"## `{name}`", "", *[f"- `{item}`" for item in ids], ""])
        (catalog_dir / "conflicts.md").write_text("\n".join(conflict_lines) + "\n", encoding="utf-8")

    def scan(self) -> Dict[str, Any]:
        catalog = self.build_catalog()
        self.save_catalog(catalog)
        return catalog

    def catalog(self, refresh: bool = False) -> Dict[str, Any]:
        path = self.root / "catalog" / "catalog.json"
        if refresh or not path.exists():
            return self.scan()
        catalog = load_data(path)
        if catalog.get("schema_version", 0) < CATALOG_SCHEMA_VERSION:
            return self.scan()
        return catalog

    def profile_files(self) -> Dict[str, Path]:
        return {path.stem: path for path in sorted((self.root / "profiles").glob("*.yaml"))}

    def active_profiles(self) -> List[str]:
        state = load_data(self.state_dir / "active-profiles.json", {"profiles": ["base"]})
        return state.get("profiles", ["base"])

    def activate_profiles(self, names: Sequence[str]) -> None:
        available = self.profile_files()
        missing = sorted(set(names) - set(available))
        if missing:
            raise VaultError(f"Unknown profiles: {', '.join(missing)}")
        write_data(
            self.state_dir / "active-profiles.json",
            {"schema_version": 1, "profiles": list(dict.fromkeys(names)), "updated_at": now_iso()},
        )

    def resolve_profile(self, names: Sequence[str], platform: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        details = self.resolve_profile_details(names, platform)
        return details["entries"], details["notes"]

    def resolve_profile_details(self, names: Sequence[str], platform: str) -> Dict[str, Any]:
        catalog = self.catalog()
        by_id = {entry["id"]: entry for entry in catalog["skills"]}
        disabled_sources = self.disabled_source_ids()
        selected: Set[str] = set()
        direct: Set[str] = set()
        reasons: Dict[str, List[Dict[str, Any]]] = {}
        notes: List[str] = []
        files = self.profile_files()
        for name in names:
            if name not in files:
                raise VaultError(f"Unknown profile: {name}")
            profile = load_data(files[name])
            restricted = profile.get("platform")
            restricted_platforms = profile.get("platforms")
            if not restricted and not restricted_platforms:
                restricted_platforms = ["codex", "claude"]
            if restricted and restricted != platform:
                continue
            if restricted_platforms and platform not in restricted_platforms:
                continue
            direct.update(profile.get("include", []))
            selected.update(profile.get("include", []))
            for source_id in profile.get("include_source", []):
                classes = set(profile.get("classification", ["published"]))
                included = [entry["id"] for entry in catalog["skills"] if entry["source_id"] == source_id and entry["classification"] in classes]
                direct.update(included)
                selected.update(included)
        missing = sorted(selected - set(by_id))
        if missing:
            raise VaultError(f"Profiles refer to missing skills: {', '.join(missing)}")

        requested = set(selected)
        disabled_direct = {
            entry_id for entry_id in selected if by_id[entry_id].get("source_id") in disabled_sources
        }
        selected.difference_update(disabled_direct)
        for entry_id in sorted(disabled_direct):
            notes.append(f"Skipped {entry_id}: source {by_id[entry_id]['source_id']} is disabled")

        queue = list(selected)
        for entry_id in direct:
            reasons.setdefault(entry_id, []).append({"type": "profile", "profiles": list(names)})
        while queue:
            entry_id = queue.pop()
            for required in by_id[entry_id].get("requires", []):
                if required not in by_id:
                    raise VaultError(f"{entry_id} requires missing skill {required}")
                if by_id[required].get("source_id") in disabled_sources:
                    notes.append(
                        f"Blocked {entry_id}: required dependency {required} belongs to a disabled source"
                    )
                    continue
                if required not in selected:
                    selected.add(required)
                    queue.append(required)
                    notes.append(f"Added required dependency {required} for {entry_id}")
                    reasons.setdefault(required, []).append({"type": "required_dependency", "required_by": entry_id})

        blocked: Set[str] = set()
        changed = True
        while changed:
            changed = False
            for entry_id in selected - blocked:
                required = by_id[entry_id].get("requires", [])
                if any(
                    dependency in blocked
                    or by_id.get(dependency, {}).get("source_id") in disabled_sources
                    for dependency in required
                ):
                    blocked.add(entry_id)
                    changed = True
        selected.difference_update(blocked)

        entries = []
        for entry_id in sorted(selected):
            entry = by_id[entry_id]
            if platform not in entry["compatibility"].get("platforms", []):
                notes.append(f"Skipped {entry_id}: incompatible with {platform}")
                continue
            if entry["classification"] != "published":
                notes.append(f"Included non-published entry explicitly: {entry_id} ({entry['classification']})")
            entries.append(entry)

        by_name: Dict[str, List[str]] = {}
        for entry in entries:
            by_name.setdefault(entry["name"].lower(), []).append(entry["id"])
        conflicts = {name: ids for name, ids in by_name.items() if len(ids) > 1}
        if conflicts:
            detail = "; ".join(f"{name}: {', '.join(ids)}" for name, ids in conflicts.items())
            raise VaultError(f"Profile has unresolved name conflicts for {platform}: {detail}")
        install_state = load_data(self.state_dir / "install-state.json", {"links": []})
        installed = install_state.get("deployments", install_state.get("links", []))

        def installed_platform(item: Dict[str, Any]) -> Optional[str]:
            if item.get("platform") in SUPPORTED_PLATFORMS:
                return item["platform"]
            parts = tuple(part.lower() for part in Path(str(item.get("path", ""))).parts)
            if any(parts[index : index + 2] == (".agents", "skills") for index in range(max(0, len(parts) - 1))):
                return "codex"
            if any(parts[index : index + 2] == (".claude", "skills") for index in range(max(0, len(parts) - 1))):
                return "claude"
            if any(
                parts[index : index + 2] in {(".lux_neo", "skills"), (".lux", "skills")}
                for index in range(max(0, len(parts) - 1))
            ):
                return "lux"
            return None

        platform_adapter = current_platform()
        if not platform_adapter.installation_matches(install_state.get("installation")):
            installed = []
        installed = [
            item
            for item in installed
            if platform_adapter.manages_active_skill_path(installed_platform(item), item.get("path"))
        ]

        allowed_sources = (
            (self.root / "my-skills").resolve(),
            (self.root / "sources").resolve(),
        )

        def deployment_current(item: Dict[str, Any]) -> bool:
            destination = Path(str(item.get("path", "")))
            target = Path(str(item.get("target", "")))
            try:
                resolved_target = target.resolve(strict=False)
            except OSError:
                return False
            if not any(
                resolved_target == root or root in resolved_target.parents
                for root in allowed_sources
            ):
                return False
            kind = item.get("deployment_type", "symlink")
            if kind in {"symlink", "symlink-file"}:
                return destination.is_symlink() and destination.resolve() == target.resolve()
            if kind not in {"managed-copy", "managed-copy-file"}:
                return False
            expected = item.get("deployed_fingerprint") or item.get("source_fingerprint")
            source_expected = item.get("source_fingerprint")
            if not expected or not source_expected:
                return False
            source_current = (
                hashlib.sha256(target.read_bytes()).hexdigest()
                if target.is_file()
                else tree_fingerprint(target)
            )
            if source_current != source_expected:
                return False
            if kind == "managed-copy-file":
                return destination.is_file() and hashlib.sha256(destination.read_bytes()).hexdigest() == expected
            return destination.is_dir() and tree_fingerprint(destination) == expected

        platform_deployments: Dict[str, List[Dict[str, Any]]] = {}
        for item in installed:
            if installed_platform(item) == platform and item.get("skill_id"):
                platform_deployments.setdefault(item["skill_id"], []).append(item)

        installed_ids: Set[str] = set()
        drifted_ids: Set[str] = set()
        for entry in entries:
            rows = platform_deployments.get(entry["id"], [])
            if platform != "lux":
                if rows and all(deployment_current(row) for row in rows):
                    installed_ids.add(entry["id"])
                elif rows:
                    drifted_ids.add(entry["id"])
                continue
            source = self.root / entry["path"]
            required = {"resources", "skill"}
            if (source / "SKILL.json").is_file() or (source / f"{entry['name']}.json").is_file():
                required.add("watcher")
            components: Dict[str, Dict[str, Any]] = {}
            for row in rows:
                component = row.get("component")
                if not component:
                    suffix = Path(str(row.get("path", ""))).suffix.lower()
                    component = "skill" if suffix == ".md" else "watcher" if suffix == ".json" else "resources"
                components[component] = row
            if required.issubset(components) and all(
                deployment_current(components[component]) for component in required
            ):
                installed_ids.add(entry["id"])
            elif rows:
                drifted_ids.add(entry["id"])

        by_name: Dict[str, List[str]] = {}
        for entry in entries:
            by_name.setdefault(entry["name"].lower(), []).append(entry["id"])
        conflicts = {name: ids for name, ids in by_name.items() if len(ids) > 1}
        status = {}
        for entry_id in sorted(requested | selected | blocked):
            entry = by_id[entry_id]
            compatible = platform in entry["compatibility"].get("platforms", [])
            source_disabled = entry.get("source_id") in disabled_sources
            status[entry_id] = {
                "selected": True,
                "compatible": compatible,
                "installed": entry_id in installed_ids,
                "reasons": reasons.get(entry_id, []),
                "state": "source-disabled" if source_disabled else "blocked-dependency" if entry_id in blocked else "installed" if compatible and entry_id in installed_ids else "drifted" if entry_id in drifted_ids else "saved-not-installed" if compatible else "incompatible",
            }
        return {"entries": entries, "notes": notes, "status": status, "direct": sorted(direct), "conflicts": conflicts}

    def update_lock(self) -> Dict[str, Any]:
        previous = load_data(self.lock_path, {"schema_version": 1, "sources": {}})
        result = {"schema_version": 1, "generated_at": now_iso(), "sources": {}}
        for source_id, source in self.registry["sources"].items():
            repo = self.source_path(source)
            if self.source_kind(source) == "git":
                result["sources"][source_id] = {
                    "kind": "git",
                    "commit": git_commit(repo),
                    "branch": source.get("branch", "main"),
                    "previous_commit": previous.get("sources", {}).get(source_id, {}).get("commit"),
                }
            elif self.source_kind(source) == "skills-cli":
                result["sources"][source_id] = {
                    "kind": "skills-cli",
                    "revision": self.source_revision(source),
                    "previous_revision": previous.get("sources", {}).get(source_id, {}).get("revision"),
                    "update_policy": "self-managed",
                }
            else:
                result["sources"][source_id] = {
                    "kind": "local-copy",
                    "revision": self.source_revision(source),
                    "previous_revision": previous.get("sources", {}).get(source_id, {}).get("revision"),
                    "update_policy": "self-managed",
                }
        write_data(self.lock_path, result)
        return result

    def derive(self, source_skill_id: str, new_name: str) -> Path:
        if not valid_skill_name(new_name):
            raise VaultError("Derived skill name must use lowercase letters, digits, and hyphens")
        catalog = self.catalog(refresh=True)
        matches = [entry for entry in catalog["skills"] if entry["id"] == source_skill_id]
        if len(matches) != 1:
            raise VaultError(f"Expected one source skill for {source_skill_id}, found {len(matches)}")
        entry = matches[0]
        if entry["source_id"] == "my":
            raise VaultError("Use an upstream skill as the derivation source")
        source = self.registry["sources"][entry["source_id"]]
        repo = self.source_path(source)
        if self.source_kind(source) == "git" and not git_clean(repo):
            raise VaultError(f"Source {entry['source_id']} is dirty; derivation requires a clean source")
        destination = self.root / "my-skills" / new_name
        if destination.exists():
            raise VaultError(f"Destination already exists: {destination}")
        source_dir = self.root / entry["path"]
        shutil.copytree(source_dir, destination)
        skill_md = destination / "SKILL.md"
        skill_md.write_text(
            replace_frontmatter_name(skill_md.read_text(encoding="utf-8"), new_name),
            encoding="utf-8",
        )
        origin = {
            "schema_version": 1,
            "kind": "derived",
            "source_id": entry["source_id"],
            "source_skill_id": source_skill_id,
            "source_relative_path": entry["source_relative_path"],
            "base_commit": entry["source_commit"],
            "base_fingerprint": entry["fingerprint"],
            "derived_at": now_iso(),
        }
        write_data(destination / ".vault-origin.json", origin)
        self.scan()
        return destination

    def drift_rows(self) -> List[Dict[str, Any]]:
        rows = []
        for origin_file in sorted((self.root / "my-skills").glob("*/.vault-origin.json")):
            origin = load_data(origin_file)
            skill_dir = origin_file.parent
            source = self.registry["sources"].get(origin.get("source_id"))
            if not source:
                rows.append({"skill": skill_dir.name, "status": "missing-source"})
                continue
            repo = self.source_skill_root(source)
            relative = origin["source_relative_path"]
            current_upstream = tree_fingerprint(repo / relative)
            base = origin["base_fingerprint"]
            local = tree_fingerprint(skill_dir, ignore_origin=True)
            rows.append(
                {
                    "skill": skill_dir.name,
                    "source_skill_id": origin.get("source_skill_id"),
                    "base_commit": origin["base_commit"],
                    "current_commit": self.source_revision(source),
                    "upstream_changed": current_upstream != base,
                    "local_changed": local != base,
                    "status": "conflict-review"
                    if current_upstream != base and local != base
                    else "upstream-changed"
                    if current_upstream != base
                    else "local-only"
                    if local != base
                    else "in-sync",
                }
            )
        return rows
