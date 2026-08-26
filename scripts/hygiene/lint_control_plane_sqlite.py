#!/usr/bin/env python3
"""Ratchet: direct ``sqlite3.connect`` opens of control-plane stores (#7365).

Scans ``scripts/`` and ``agents_extensions/shared/session_streams/`` for
``sqlite3.connect`` calls that target the four control-plane sqlite files.
New opens outside ``scripts/control_plane/`` fail; existing call sites are
allowlisted by ``(path, snippet, max_occurrences)`` so later slices can shrink
the list.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

_SCAN_ROOTS: tuple[str, ...] = (
    "scripts",
    "agents_extensions/shared/session_streams",
)
_CONTROL_PLANE_PACKAGE = "scripts/control_plane"
_SKIP_PATH_PREFIXES: tuple[str, ...] = ("tests/",)

# Exact ``(path, stripped snippet, max_occurrences)`` for remaining direct opens.
_ALLOWLIST: tuple[tuple[str, str, int], ...] = (
    (
        "agents_extensions/shared/session_streams/db.py",
        "connection = sqlite3.connect(",
        2,
    ),
    (
        "scripts/agent_runtime/acpx_discuss.py",
        'connection = sqlite3.connect(f"{db_path.as_uri()}?mode=ro", uri=True)',
        1,
    ),
    (
        "scripts/api/fleet_router.py",
        "connection = sqlite3.connect(",
        1,
    ),
    (
        "scripts/api/fleet_workers_collect.py",
        "conn = sqlite3.connect(str(path))",
        1,
    ),
    (
        "scripts/api/runtime_router.py",
        'connection = sqlite3.connect(f"{db_path.resolve().as_uri()}?mode=ro", uri=True)',
        1,
    ),
    (
        "scripts/entire_context/reconcile.py",
        'with sqlite3.connect(f"{db_path.as_uri()}?mode=ro", uri=True) as connection:',
        1,
    ),
    (
        "scripts/entire_context/resolvers.py",
        'with sqlite3.connect(f"{db_path.as_uri()}?mode=ro", uri=True) as connection:',
        1,
    ),
    (
        "scripts/fleet_comms/artifacts.py",
        "self._conn = sqlite3.connect(",
        1,
    ),
    (
        "scripts/fleet_comms/cli.py",
        'conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)',
        1,
    ),
    (
        "scripts/fleet_comms/cold_start_board.py",
        'conn = sqlite3.connect(f"file:{plane_db.resolve().as_posix()}?mode=ro", uri=True)',
        1,
    ),
    (
        "scripts/fleet_comms/message_plane.py",
        'conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)',
        1,
    ),
    (
        "scripts/fleet_comms/routing_reservations.py",
        'connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)',
        1,
    ),
    (
        "scripts/orchestration/slot_routing.py",
        'conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)',
        1,
    ),
)

_WRITE_OWNERSHIP = re.compile(r"write[-_]ownership")
_SESSION_STREAMS = re.compile(
    r"session[-_]streams|SessionStreamDatabase|session_streams_db_path|stream_leases"
)
_FLEET_COMMS = re.compile(
    r"comms\.sqlite3|default_plane_root|_plane_db_path|comms_plane_store|plane_db"
)
_LEGACY = re.compile(
    r"legacy_broker|legacy_db|MESSAGE_DB|import_legacy|_probe_inbox_legacy|source_path"
)


@dataclass(frozen=True)
class Finding:
    rel_path: str
    line_no: int
    snippet: str
    store: str


def _rel(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def _allowlist_lookup() -> dict[tuple[str, str], int]:
    return {(path, snippet): max_count for path, snippet, max_count in _ALLOWLIST}


def iter_scan_paths(repo_root: Path | None = None) -> list[Path]:
    root = (repo_root or REPO_ROOT).resolve()
    found: list[Path] = []
    for scan_root in _SCAN_ROOTS:
        base = root / scan_root
        if not base.is_dir():
            continue
        found.extend(base.rglob("*.py"))
    unique = sorted({path.resolve() for path in found if path.is_file()})
    return [
        path
        for path in unique
        if not _rel(path, root).startswith(_CONTROL_PLANE_PACKAGE)
        and not any(_rel(path, root).startswith(prefix) for prefix in _SKIP_PATH_PREFIXES)
    ]


def _stores_for_context(context: str) -> set[str]:
    stores: set[str] = set()
    if _WRITE_OWNERSHIP.search(context):
        stores.add("write_ownership")
    if _SESSION_STREAMS.search(context):
        stores.add("session_streams")
    fleet_hit = bool(_FLEET_COMMS.search(context))
    legacy_hit = bool(_LEGACY.search(context))
    if (
        fleet_hit
        and not (legacy_hit and "comms_plane" not in context and "plane_db" not in context)
        and (
            not legacy_hit
            or re.search(r"comms_plane|plane_db|default_plane_root|_plane_db", context)
        )
    ):
        stores.add("fleet_comms")
    if re.search(r"task_index|task-index", context):
        stores.add("task_index")
    return stores


def _function_context(node: ast.AST, lines: list[str]) -> str:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        start = node.lineno - 1
        end = getattr(node, "end_lineno", node.lineno) or node.lineno
        return "\n".join(lines[start:end])
    return ""


def _call_snippet(lines: list[str], line_index: int) -> str:
    parts: list[str] = []
    for offset in range(0, 4):
        idx = line_index + offset
        if idx >= len(lines):
            break
        parts.append(lines[idx])
        if ")" in lines[idx]:
            break
    return " ".join(part.strip() for part in parts).strip()


def find_control_plane_connects(repo_root: Path | None = None) -> list[Finding]:
    """Return direct control-plane ``sqlite3.connect`` findings outside the seam."""
    root = (repo_root or REPO_ROOT).resolve()
    findings: list[Finding] = []
    for path in iter_scan_paths(root):
        rel = _rel(path, root)
        try:
            source = path.read_text(encoding="utf-8")
            lines = source.splitlines()
            tree = ast.parse(source, filename=str(path))
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not (
                isinstance(func, ast.Attribute)
                and func.attr == "connect"
                and isinstance(func.value, ast.Name)
                and func.value.id == "sqlite3"
            ):
                continue
            line_index = node.lineno - 1
            snippet = lines[line_index].strip() if line_index < len(lines) else ""
            if not snippet:
                snippet = _call_snippet(lines, line_index)
            enclosing = ""
            for candidate in ast.walk(tree):
                if isinstance(candidate, (ast.FunctionDef, ast.AsyncFunctionDef)) and (
                    candidate.lineno <= node.lineno
                    and (getattr(candidate, "end_lineno", candidate.lineno) or candidate.lineno)
                    >= node.lineno
                ):
                    enclosing = _function_context(candidate, lines)
            context = f"{enclosing}\n{snippet}"
            stores = _stores_for_context(context)
            if not stores:
                continue
            for store in sorted(stores):
                findings.append(Finding(rel, node.lineno, snippet, store))
    return findings


def find_unallowlisted_connects(repo_root: Path | None = None) -> list[tuple[str, str]]:
    """Return ``(path:line, detail)`` for hits not covered by the allowlist."""
    allowlist = _allowlist_lookup()
    usage: Counter[tuple[str, str]] = Counter()
    violations: list[tuple[str, str]] = []
    for finding in find_control_plane_connects(repo_root):
        key = (finding.rel_path, finding.snippet)
        max_allowed = allowlist.get(key)
        if max_allowed is not None:
            usage[key] += 1
            if usage[key] <= max_allowed:
                continue
            violations.append(
                (
                    f"{finding.rel_path}:{finding.line_no}",
                    f"allowlist exceeded for {finding.store}: {finding.snippet}",
                )
            )
            continue
        violations.append(
            (
                f"{finding.rel_path}:{finding.line_no}",
                f"new direct {finding.store} open: {finding.snippet}",
            )
        )
    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    violations = find_unallowlisted_connects()
    if not violations:
        print("OK: no unallowlisted control-plane sqlite3.connect opens")
        return 0
    print(
        "Unallowlisted control-plane sqlite3.connect (route through scripts/control_plane/):",
        file=sys.stderr,
    )
    for key, detail in violations:
        print(f"  {key}: {detail}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
