"""AST helpers for the scripts/ subprocess-timeout allowlist (#7176 / #7213).

The allowlist key is ``path::qualname::callee::shape``. ``shape`` is a
location-independent hash of the call AST so a different timeout-less call
cannot rotate into a vacated slot under the same qualname (review F4).
"""

from __future__ import annotations

import ast
import hashlib
import re
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import NamedTuple

from scripts.ci.test_source_cache import parse_test_source, read_test_source

BOUNDED_FUNCS = frozenset({"run", "check_output", "call", "check_call"})
SHAPE_HASH_HEX_LEN = 16
ALLOWLIST_KEY_PARTS = 4
_SUBPROCESS_IMPORT_RE = re.compile(r"(?m)^\s*(?:import subprocess|from subprocess import)\b")
_SHAPE_RE = re.compile(rf"^[0-9a-f]{{{SHAPE_HASH_HEX_LEN}}}$")

UNALLOWLISTED_PREAMBLE = (
    "Timeout-less subprocess calls under scripts/ not in allowlist (issue #7176).\n"
    "Pass an explicit timeout= (typically 30 for git fixtures/helpers, 60–120 for "
    "heavier scripts) to bound the subprocess call. Popen callers must bound "
    ".wait() / .communicate() instead.\n"
    "Each reported line starts with the paste-ready allowlist key "
    "path::qualname::callee::shape.\n"
)

STALE_PREAMBLE = (
    "Stale entries in scripts/ci/subprocess_timeout_allowlist.txt (issue #7176).\n"
    "The allowlist is shrink-only. When a subprocess call is given a timeout=, "
    "removed, or renamed (file moved or enclosing function/qualname changed), "
    "its entry must be removed or replaced with the new paste-ready key "
    "path::qualname::callee::shape:\n"
)

SORT_ADVICE = (
    "subprocess timeout allowlist must be sorted in C-locale byte order "
    "(LC_ALL=C). Re-sort with: LC_ALL=C sort -o "
    "scripts/ci/subprocess_timeout_allowlist.txt "
    "scripts/ci/subprocess_timeout_allowlist.txt"
)


class TimeoutLessCall(NamedTuple):
    lineno: int
    name: str
    qualname: str
    shape_hash: str

    def allowlist_key(self, rel_path: str) -> str:
        return format_allowlist_key(rel_path, self.qualname, self.name, self.shape_hash)


class _SubprocessCallVisitor(ast.NodeVisitor):
    def __init__(self, aliases: dict[str, str | None]) -> None:
        self._aliases = aliases
        self._scope_stack: list[str] = []
        self.hits: list[TimeoutLessCall] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._scope_stack.append(node.name)
        self.generic_visit(node)
        self._scope_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._scope_stack.append(node.name)
        self.generic_visit(node)
        self._scope_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._scope_stack.append(node.name)
        self.generic_visit(node)
        self._scope_stack.pop()

    def visit_Call(self, node: ast.Call) -> None:
        name: str | None = None
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            base = node.func.value.id
            if base in self._aliases and self._aliases[base] is None and node.func.attr in BOUNDED_FUNCS:
                name = f"subprocess.{node.func.attr}"
        elif isinstance(node.func, ast.Name) and node.func.id in self._aliases:
            attr = self._aliases[node.func.id]
            if attr in BOUNDED_FUNCS:
                name = f"subprocess.{attr}"
        if name is not None:
            kwargs = {kw.arg for kw in node.keywords if kw.arg}
            if "timeout" not in kwargs:
                qualname = ".".join(self._scope_stack) if self._scope_stack else "<module>"
                self.hits.append(
                    TimeoutLessCall(node.lineno, name, qualname, call_shape_hash(node))
                )
        self.generic_visit(node)


def call_shape_hash(node: ast.Call) -> str:
    """Location-independent fingerprint of one Call AST.

    ``include_attributes=False`` drops lineno/col so a move inside the same
    function does not rotate identity. Changing callee or arguments does.
    """
    payload = ast.dump(node, include_attributes=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:SHAPE_HASH_HEX_LEN]


def format_allowlist_key(rel_path: str, qualname: str, callee: str, shape_hash: str) -> str:
    return f"{rel_path}::{qualname}::{callee}::{shape_hash}"


def parse_allowlist_key(entry: str) -> tuple[str, str, str, str]:
    parts = entry.split("::")
    if len(parts) != ALLOWLIST_KEY_PARTS:
        raise ValueError(
            "invalid allowlist entry format "
            f"(expected path::qualname::callee::shape): {entry}"
        )
    path, qualname, callee, shape_hash = parts
    if not _SHAPE_RE.fullmatch(shape_hash):
        raise ValueError(
            f"invalid allowlist shape hash (expected {SHAPE_HASH_HEX_LEN} lowercase hex): {entry}"
        )
    if not callee.startswith("subprocess."):
        raise ValueError(f"invalid allowlist callee (expected subprocess.*): {entry}")
    if not path or not qualname:
        raise ValueError(f"invalid allowlist entry (empty path or qualname): {entry}")
    return path, qualname, callee, shape_hash


def load_allowlist(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]


def sort_allowlist_entries(entries: Sequence[str]) -> list[str]:
    """C-locale / UTF-8 byte order — not libc locale ``sort``."""
    return sorted(entries, key=lambda item: item.encode("utf-8"))


def format_unallowlisted_line(
    key: str, *, lineno: int, actual_count: int, allowed_count: int
) -> str:
    """Paste-ready key first so the line can be copied into the allowlist."""
    return f"{key}  # line {lineno}; found {actual_count}, allowlist permits {allowed_count}"


def format_stale_line(key: str, *, allowed_count: int, actual_count: int) -> str:
    return f"{key} (allowlist has {allowed_count}, actual violations {actual_count})"


def _collect_aliases(tree: ast.AST) -> dict[str, str | None]:
    aliases: dict[str, str | None] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "subprocess":
            for alias in node.names:
                aliases[alias.asname or alias.name] = alias.name
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "subprocess":
                    aliases[alias.asname or "subprocess"] = None
    return aliases


def timeout_less_calls_from_tree(tree: ast.AST) -> list[TimeoutLessCall]:
    visitor = _SubprocessCallVisitor(_collect_aliases(tree))
    visitor.visit(tree)
    return visitor.hits


def timeout_less_calls_from_source(src: str, *, filename: str = "<mem>") -> list[TimeoutLessCall]:
    if "subprocess" not in src or not _SUBPROCESS_IMPORT_RE.search(src):
        return []
    return timeout_less_calls_from_tree(ast.parse(src, filename=filename))


def timeout_less_calls(path: Path) -> list[TimeoutLessCall]:
    src = read_test_source(path)
    if "subprocess" not in src or not _SUBPROCESS_IMPORT_RE.search(src):
        return []
    return timeout_less_calls_from_tree(parse_test_source(path))


def scan_scripts(scripts_root: Path, repo_root: Path) -> tuple[dict[str, list[TimeoutLessCall]], list[str]]:
    """Scan ``scripts_root`` for timeout-less calls. Returns (hits_by_key, scan_errors)."""
    actual_hits: dict[str, list[TimeoutLessCall]] = defaultdict(list)
    scan_errors: list[str] = []
    for path in sorted(scripts_root.rglob("*.py")):
        try:
            hits = timeout_less_calls(path)
        except SyntaxError as exc:
            scan_errors.append(f"{path}: syntax error while scanning ({exc})")
            continue
        rel = path.relative_to(repo_root).as_posix()
        for hit in hits:
            actual_hits[hit.allowlist_key(rel)].append(hit)
    return actual_hits, scan_errors


def compare_allowlist(
    allowlist_entries: Sequence[str],
    actual_hits: Mapping[str, Sequence[TimeoutLessCall]],
) -> tuple[list[str], list[str]]:
    """Return paste-ready unallowlisted lines and stale-entry lines."""
    allowlist_counts = Counter(allowlist_entries)
    unallowlisted: list[str] = []
    for key, hits in sorted(actual_hits.items()):
        allowed_count = allowlist_counts.get(key, 0)
        if len(hits) > allowed_count:
            for hit in hits[allowed_count:]:
                unallowlisted.append(
                    format_unallowlisted_line(
                        key,
                        lineno=hit.lineno,
                        actual_count=len(hits),
                        allowed_count=allowed_count,
                    )
                )

    stale_entries: list[str] = []
    for key, allowed_count in sorted(allowlist_counts.items()):
        actual_count = len(actual_hits.get(key, []))
        if allowed_count > actual_count:
            stale_entries.append(
                format_stale_line(key, allowed_count=allowed_count, actual_count=actual_count)
            )
    return unallowlisted, stale_entries


def validate_allowlist_entry(entry: str, repo_root: Path) -> None:
    path, _qualname, _callee, _shape = parse_allowlist_key(entry)
    resolved = repo_root / path
    if not resolved.is_file():
        raise ValueError(f"allowlist entry refers to non-existent file: {path}")
