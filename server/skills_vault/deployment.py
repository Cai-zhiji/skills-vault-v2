from __future__ import annotations

import shutil
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
            "deployment_type": row.get("deployment_type", "symlink"),
            "source_fingerprint": row.get("source_fingerprint"),
            "deployed_fingerprint": row.get("deployed_fingerprint"),
        }
        for row in deployments
    ]


def deployment_fingerprint(path: Path, deployment_type: str) -> str:
    if deployment_type == "symlink":
        if not path.is_symlink():
            return "missing"
        return tree_fingerprint(path.resolve())
    return tree_fingerprint(path)


def deployment_is_current(row: Dict[str, Any]) -> bool:
    destination = Path(row["path"])
    target = Path(row["target"])
    kind = row.get("deployment_type", "symlink")
    if kind == "symlink":
        return destination.is_symlink() and destination.resolve() == target.resolve()
    if kind == "managed-copy":
        expected = row.get("deployed_fingerprint") or row.get("source_fingerprint")
        return destination.is_dir() and bool(expected) and tree_fingerprint(destination) == expected
    return False


def remove_deployment(row: Dict[str, Any], *, allow_modified_copy: bool = False) -> bool:
    destination = Path(row["path"])
    kind = row.get("deployment_type", "symlink")
    if kind == "symlink":
        if not destination.is_symlink() or destination.resolve() != Path(row["target"]).resolve():
            return False
        destination.unlink()
        return True
    if kind == "managed-copy":
        if not destination.exists():
            return False
        expected = row.get("deployed_fingerprint") or row.get("source_fingerprint")
        current = tree_fingerprint(destination)
        if not allow_modified_copy and (not expected or current != expected):
            raise VaultError(f"Managed copy has user changes and will not be removed: {destination}")
        shutil.rmtree(destination)
        return True
    raise VaultError(f"Unsupported deployment type: {kind}")


def apply_deployment(operation: Dict[str, Any], managed: Dict[str, Any] | None = None) -> Dict[str, Any]:
    destination = Path(operation["path"])
    target = Path(operation["target"])
    kind = operation.get("deployment_type", "symlink")
    if not target.is_dir():
        raise VaultError(f"Skill deployment source is missing: {target}")
    source_fingerprint = tree_fingerprint(target)

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
    if kind == "symlink":
        destination.symlink_to(target, target_is_directory=True)
        deployed_fingerprint = source_fingerprint
    elif kind == "managed-copy":
        temporary_root = Path(tempfile.mkdtemp(prefix=f".{destination.name}.", dir=str(destination.parent)))
        temporary = temporary_root / "payload"
        try:
            shutil.copytree(target, temporary, symlinks=True)
            temporary.replace(destination)
        finally:
            shutil.rmtree(temporary_root, ignore_errors=True)
        deployed_fingerprint = tree_fingerprint(destination)
    else:
        raise VaultError(f"Unsupported deployment type: {kind}")

    return {
        "path": str(destination),
        "target": str(target),
        "skill_id": operation["skill_id"],
        "platform": operation["platform"],
        "deployment_type": kind,
        "source_fingerprint": source_fingerprint,
        "deployed_fingerprint": deployed_fingerprint,
    }
