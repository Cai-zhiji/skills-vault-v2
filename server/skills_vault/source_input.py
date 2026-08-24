from __future__ import annotations

import hashlib
import re
import shlex
import urllib.parse
from dataclasses import dataclass
from typing import Iterable, Optional


@dataclass(frozen=True)
class SourceSpec:
    kind: str
    source_ref: str
    source_url: str
    source_id: str
    branch: str
    full_depth: bool
    skills: list[str]
    input_kind: str


def _slug(value: str) -> str:
    value = re.sub(r"\.git$", "", value.strip().lower())
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")[:64] or "source"


def _repository_path(source_ref: str) -> str:
    scp = re.fullmatch(r"[^@\s]+@[^:\s]+:(.+)", source_ref)
    if scp:
        return scp.group(1)
    parsed = urllib.parse.urlparse(source_ref)
    if parsed.scheme and parsed.hostname:
        return parsed.path.strip("/")
    return source_ref.strip("/")


def source_id_for(source_ref: str) -> str:
    parts = [part for part in _repository_path(source_ref).split("/") if part]
    if len(parts) >= 2:
        return _slug("-".join(parts[-2:]))
    return _slug(parts[-1] if parts else source_ref)


def canonical_source_ref(source_ref: str) -> str:
    value = str(source_ref or "").strip()
    scp = re.fullmatch(r"([^@\s]+)@([^:\s]+):(.+)", value)
    if scp:
        return f"{scp.group(2).lower()}/{scp.group(3).strip('/').removesuffix('.git').lower()}"
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme and parsed.hostname:
        path = parsed.path.strip("/").removesuffix(".git").lower()
        return f"{parsed.hostname.lower()}/{path}"
    return value.strip("/").removesuffix(".git").lower()


def disambiguate_source_id(base: str, source_ref: str, existing: Iterable[str]) -> str:
    existing_ids = set(existing)
    if base not in existing_ids:
        return base
    suffix = hashlib.sha256(source_ref.strip().lower().encode("utf-8")).hexdigest()[:8]
    return f"{base[:55].rstrip('-')}-{suffix}"


def _tokens(raw_input: str) -> list[str]:
    if any(char in raw_input for char in (";", "|", ">", "<", "`", "$", "&")):
        raise ValueError("来源输入不能包含 shell 运算符")
    try:
        return shlex.split(raw_input, posix=True)
    except ValueError as exc:
        raise ValueError(f"来源输入引号不完整：{exc}") from exc


def _first_value(tokens: list[str], names: tuple[str, ...]) -> Optional[str]:
    for index, token in enumerate(tokens[:-1]):
        if token in names:
            return tokens[index + 1]
    return None


def _skill_values(tokens: list[str]) -> list[str]:
    values: list[str] = []
    index = 0
    while index < len(tokens):
        if tokens[index] in ("--skill", "--skills") and index + 1 < len(tokens):
            values.append(tokens[index + 1])
            index += 2
            continue
        index += 1
    return list(dict.fromkeys(value.strip() for value in values if value.strip()))


def parse_source_input(
    raw_input: str,
    kind: str,
    source_id: Optional[str] = None,
    branch: str = "main",
) -> SourceSpec:
    value = str(raw_input or "").strip()
    if not value:
        raise ValueError("来源地址或命令不能为空")
    tokens = _tokens(value)
    input_kind = "reference"
    source_ref = value
    full_depth = "--full-depth" in tokens
    skills: list[str] = []

    if kind == "skills-cli":
        if len(tokens) >= 4 and tokens[0] in ("npx", "npx.cmd") and tokens[1] == "skills" and tokens[2] in ("add", "install"):
            source_ref = tokens[3]
            input_kind = "skills-cli-command"
            skills = _skill_values(tokens[4:])
        elif len(tokens) >= 3 and tokens[0] == "skills" and tokens[1] in ("add", "install"):
            source_ref = tokens[2]
            input_kind = "skills-cli-command"
            skills = _skill_values(tokens[3:])
    elif kind == "git":
        if len(tokens) >= 3 and tokens[0] == "git" and tokens[1] == "clone":
            source_ref = tokens[2]
            input_kind = "git-command"
            branch = _first_value(tokens[3:], ("--branch", "-b")) or branch

    if source_id is not None and str(source_id).strip():
        normalized_id = str(source_id).strip().lower()
    else:
        normalized_id = source_id_for(source_ref)
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", normalized_id):
        raise ValueError("来源 ID 只能使用小写字母、数字和连字符")
    return SourceSpec(
        kind=kind,
        source_ref=source_ref,
        source_url=source_ref,
        source_id=normalized_id,
        branch=branch.strip() or "main",
        full_depth=full_depth,
        skills=skills,
        input_kind=input_kind,
    )
