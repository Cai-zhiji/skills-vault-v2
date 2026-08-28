from __future__ import annotations

import hashlib
import os
import shutil
import stat
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .core import VaultError, tree_fingerprint


def state_deployments(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Read schema v2 deployments while remaining compatible with v1 links."""

    rows = state.get("deployments")
    if isinstance(rows, list):
        return [dict(row) for row in rows]
    return [
        {
            **dict(row),
            "deployment_type": row.get("deployment_type", "symlink"),
            "source_fingerprint": row.get("source_fingerprint"),
            "deployed_fingerprint": row.get("deployed_fingerprint"),
        }
        for row in state.get("links", [])
    ]


def legacy_links(deployments: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Compatibility projection for existing API/UI consumers during migration."""

    return [
        {
            "path": row["path"],
            "target": row["target"],
            "skill_id": row["skill_id"],
            "platform": row["platform"],
            "name": row.get("name"),
            "component": row.get("component"),
            "deployment_type": row.get("deployment_type", "symlink"),
            "source_fingerprint": row.get("source_fingerprint"),
            "deployed_fingerprint": row.get("deployed_fingerprint"),
        }
        for row in deployments
    ]


def path_fingerprint(path: Path) -> str:
    if not path.exists():
        return "missing"
    if path.is_file():
        return hashlib.sha256(path.read_bytes()).hexdigest()
    return tree_fingerprint(path)


def deployment_fingerprint(path: Path, deployment_type: str) -> str:
    if deployment_type in {"symlink", "symlink-file"}:
        if not path.is_symlink():
            return "missing"
        return path_fingerprint(path.resolve())
    return path_fingerprint(path)


def deployment_is_current(row: Dict[str, Any]) -> bool:
    destination = Path(row["path"])
    target = Path(row["target"])
    kind = row.get("deployment_type", "symlink")
    if kind in {"symlink", "symlink-file"}:
        return destination.is_symlink() and destination.resolve() == target.resolve()
    if kind in {"managed-copy", "managed-copy-file"}:
        expected = row.get("deployed_fingerprint") or row.get("source_fingerprint")
        expected_kind = destination.is_file() if kind == "managed-copy-file" else destination.is_dir()
        return expected_kind and bool(expected) and path_fingerprint(destination) == expected
    return False


def _remove_readonly(function: Any, value: str, _: Any) -> None:
    path = Path(value)
    if not path.is_symlink():
        os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
    function(value)


def remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        try:
            path.unlink()
        except PermissionError:
            if path.is_symlink():
                raise
            os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
            path.unlink()
    elif path.is_dir():
        shutil.rmtree(path, onerror=_remove_readonly)


def remove_deployment(row: Dict[str, Any], *, allow_modified_copy: bool = False) -> bool:
    destination = Path(row["path"])
    kind = row.get("deployment_type", "symlink")
    if kind in {"symlink", "symlink-file"}:
        if not destination.is_symlink() or destination.resolve() != Path(row["target"]).resolve():
            return False
        remove_path(destination)
        return True
    if kind in {"managed-copy", "managed-copy-file"}:
        if not destination.exists():
            return False
        expected = row.get("deployed_fingerprint") or row.get("source_fingerprint")
        current = path_fingerprint(destination)
        if not allow_modified_copy and (not expected or current != expected):
            raise VaultError(f"Managed copy has user changes and will not be removed: {destination}")
        remove_path(destination)
        return True
    raise VaultError(f"Unsupported deployment type: {kind}")


def apply_deployment(operation: Dict[str, Any], managed: Dict[str, Any] | None = None) -> Dict[str, Any]:
    destination = Path(operation["path"])
    target = Path(operation["target"])
    kind = operation.get("deployment_type", "symlink")
    allowed_parent = operation.get("allowed_parent")
    if allowed_parent and destination.parent.resolve() != Path(allowed_parent).resolve():
        raise VaultError(f"Skill deployment destination escapes the managed root: {destination}")
    allowed_source_roots = [Path(root).resolve() for root in operation.get("allowed_source_roots", [])]
    resolved_target = target.resolve()
    if allowed_source_roots and not any(
        resolved_target == root or root in resolved_target.parents for root in allowed_source_roots
    ):
        raise VaultError(f"Skill deployment source escapes the Vault: {target}")
    expects_file = kind in {"symlink-file", "managed-copy-file"}
    if (expects_file and not target.is_file()) or (not expects_file and not target.is_dir()):
        raise VaultError(f"Skill deployment source is missing: {target}")
    source_fingerprint = path_fingerprint(target)

    if managed and deployment_is_current(managed):
        same_target = Path(managed["target"]).resolve() == target.resolve()
        same_kind = managed.get("deployment_type", "symlink") == kind
        if same_target and same_kind and managed.get("source_fingerprint") == source_fingerprint:
            return dict(managed)

    if destination.exists() or destination.is_symlink():
        if not managed:
            raise VaultError(
                f"Destination is not managed by this install plan: {destination}. Resolve it manually or use a reset preview."
            )
        remove_deployment(managed)

    destination.parent.mkdir(parents=True, exist_ok=True)
    if kind in {"symlink", "symlink-file"}:
        destination.symlink_to(target, target_is_directory=kind == "symlink")
        deployed_fingerprint = source_fingerprint
    elif kind == "managed-copy":
        temporary_root = Path(tempfile.mkdtemp(prefix=f".{destination.name}.", dir=str(destination.parent)))
        temporary = temporary_root / "payload"
        try:
            shutil.copytree(target, temporary, symlinks=True)
            temporary.replace(destination)
        finally:
            shutil.rmtree(temporary_root, ignore_errors=True)
        deployed_fingerprint = path_fingerprint(destination)
    elif kind == "managed-copy-file":
        with tempfile.NamedTemporaryFile(
            prefix=f".{destination.name}.", dir=destination.parent, delete=False
        ) as handle:
            temporary = Path(handle.name)
        try:
            shutil.copy2(target, temporary)
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)
        deployed_fingerprint = path_fingerprint(destination)
    else:
        raise VaultError(f"Unsupported deployment type: {kind}")

    return {
        "path": str(destination),
        "target": str(target),
        "skill_id": operation["skill_id"],
        "platform": operation["platform"],
        "name": operation.get("name"),
        "component": operation.get("component"),
        "deployment_type": kind,
        "source_fingerprint": source_fingerprint,
        "deployed_fingerprint": deployed_fingerprint,
    }
