"""Fail when production code hardcodes a checkout-relative project interpreter.

A dispatch worktree has no ``.venv``. Spawns must use
``scripts.common.repo_root.project_interpreter`` (the primary checkout's
interpreter). ``tests/`` is not scanned: those joins build fixture
interpreters. The allowlist is the files that intentionally name one
checkout's interpreter, with the reason and the exact hit count.
"""

from __future__ import annotations

import ast
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCAN_SKIP = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "curriculum",
    "data",
    "node_modules",
    "site",
    "starlight",
    "tests",
    "wiki",
}

# path -> (hit count, why this checkout-local join stays)
ALLOWLIST: dict[str, tuple[int, str]] = {
    "scripts/common/repo_root.py": (
        1,
        "defines project_interpreter(); the join is the primary checkout's interpreter",
    ),
    "scripts/api/launchd_supervisor.py": (
        2,
        "LaunchAgent is bound to --repo-root; validation and the uvicorn child use that checkout's interpreter, rendered even when the file is absent",
    ),
    "scripts/api/project_state_collect.py": (
        1,
        "probes the private work-service checkout's interpreter, not this repo's",
    ),
    "scripts/orchestration/install_worktree_cleanup_launchd.py": (
        1,
        "validates the interpreter of the checkout the LaunchAgent unit is installed for",
    ),
    "scripts/orchestration/install_archived_thread_cleanup_launchd.py": (
        1,
        "validates the interpreter of the checkout the LaunchAgent unit is installed for",
    ),
    "scripts/orchestration/install_mac_observer_launchd.py": (
        1,
        "validates the interpreter of the checkout the LaunchAgent unit is installed for",
    ),
    "scripts/storage/install_data_volume_dropins.py": (
        1,
        "systemd drop-in names the primary checkout's interpreter; --apply refuses a worktree",
    ),
    "scripts/orchestration/issue_stream_audit.py": (
        1,
        "release snapshot has no .venv; the worker spawns LIVE_REPO_ROOT's interpreter",
    ),
    "scripts/orchestration/claudex_supervisor.py": (
        2,
        "relaunch contract prefers this checkout's venv, then the canonical checkout, then any sys.executable",
    ),
    "scripts/audit/post_build_review.py": (
        2,
        "resolve_venv_python prefers this checkout, then the git common-dir checkout, and raises ReviewProtocolError",
    ),
    "scripts/build/v7_build.py": (
        2,
        "main checkout first, then this repo's path even when that file is missing",
    ),
}


def _div_chain_strings(node: ast.AST) -> list[str] | None:
    parts: list[str] = []
    current = node
    while isinstance(current, ast.BinOp) and isinstance(current.op, ast.Div):
        right = current.right
        if not isinstance(right, ast.Constant) or not isinstance(right.value, str):
            return None
        parts.append(right.value)
        current = current.left
    parts.reverse()
    return parts


def checkout_relative_interpreter_lines(source: str) -> list[int]:
    """Line numbers of ``... / ".venv" / "bin" / "python"`` joins."""
    tree = ast.parse(source)
    lines: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.Div):
            continue
        parts = _div_chain_strings(node)
        if parts is not None and parts[-3:] == [".venv", "bin", "python"]:
            lines.append(node.lineno)
    return lines


def production_hits(root: Path = REPO_ROOT) -> dict[str, int]:
    hits: dict[str, int] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(name for name in dirnames if name not in SCAN_SKIP and not name.startswith("."))
        for name in filenames:
            if not name.endswith(".py"):
                continue
            path = Path(dirpath) / name
            try:
                source = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            count = len(checkout_relative_interpreter_lines(source))
            if count:
                hits[path.relative_to(root).as_posix()] = count
    return hits


def test_checkout_relative_interpreter_joins_are_allowlisted() -> None:
    hits = production_hits()
    unexpected = sorted(set(hits) - set(ALLOWLIST))
    stale = sorted(set(ALLOWLIST) - set(hits))
    count_mismatch = sorted(
        f"{path}: found {hits[path]}, allowlist {ALLOWLIST[path][0]}"
        for path in set(hits) & set(ALLOWLIST)
        if hits[path] != ALLOWLIST[path][0]
    )
    assert unexpected == [], "new checkout-relative interpreter join:\n" + "\n".join(unexpected)
    assert stale == [], "allowlist entry has no join:\n" + "\n".join(stale)
    assert count_mismatch == [], "allowlist hit count drifted:\n" + "\n".join(count_mismatch)
    assert all(reason.strip() for _count, reason in ALLOWLIST.values())


def test_scanner_flags_a_spawn_and_ignores_other_joins() -> None:
    source = 'import pathlib\npython = pathlib.Path("repo") / ".venv" / "bin" / "python"\n'
    assert checkout_relative_interpreter_lines(source) == [2]
    other = 'import pathlib\npath = pathlib.Path("repo") / ".venv" / "bin"\n'
    assert checkout_relative_interpreter_lines(other) == []
