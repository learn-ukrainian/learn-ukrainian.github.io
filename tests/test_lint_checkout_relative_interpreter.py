"""Fail when production code hardcodes a checkout-relative project interpreter.

A dispatch worktree has no ``.venv``. Spawns must use
``scripts.common.repo_root.project_interpreter`` (the primary checkout's
interpreter). ``tests/`` is not scanned: those joins build fixture
interpreters. The allowlist is the files that intentionally name one
checkout's interpreter, with the reason and the exact hit count.

Flagged constructions are ``/`` joins, ``.joinpath(...)``, and
``os.path.join(...)`` whose pieces end in ``.venv/bin/python`` or
``.venv/bin/python3``. A single ``".venv/bin/python"`` segment counts the
same as the three-part form.
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
    "batch_state/phase3-run-cycle006-controller-v2.py": (
        1,
        "tracked frozen source whose code hash is bound by a receipt (preflight preflight_binding_drift)",
    ),
    "scripts/projects/open_model_data/phase3_rule_author_runner.py": (
        1,
        "script_sha256 of this file is sealed into prepared run manifests; resume rejects hash drift",
    ),
}

_INTERPRETER_TAILS = (
    (".venv", "bin", "python"),
    (".venv", "bin", "python3"),
)


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


def _flatten_parts(parts: list[str]) -> tuple[str, ...]:
    flat: list[str] = []
    for part in parts:
        flat.extend(piece for piece in part.split("/") if piece)
    return tuple(flat)


def _ends_with_interpreter(parts: list[str]) -> bool:
    flat = _flatten_parts(parts)
    return len(flat) >= 3 and flat[-3:] in _INTERPRETER_TAILS


def _trailing_string_args(call: ast.Call) -> list[str]:
    args: list[str] = []
    for arg in reversed(call.args):
        if not isinstance(arg, ast.Constant) or not isinstance(arg.value, str):
            break
        args.append(arg.value)
    args.reverse()
    return args


def _os_path_join_names(tree: ast.AST) -> tuple[set[str], set[str], set[str]]:
    """Names bound to ``os``, to ``os.path``, and to ``os.path.join``."""
    os_modules: set[str] = set()
    path_modules: set[str] = set()
    join_funcs: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "os":
                    os_modules.add(alias.asname or "os")
                elif alias.name == "os.path":
                    if alias.asname:
                        path_modules.add(alias.asname)
                    else:
                        os_modules.add("os")
        elif isinstance(node, ast.ImportFrom) and node.module == "os":
            for alias in node.names:
                if alias.name == "path":
                    path_modules.add(alias.asname or "path")
        elif isinstance(node, ast.ImportFrom) and node.module == "os.path":
            for alias in node.names:
                if alias.name == "join":
                    join_funcs.add(alias.asname or "join")
    return os_modules, path_modules, join_funcs


def _is_os_path_join(
    func: ast.expr,
    os_modules: set[str],
    path_modules: set[str],
    join_funcs: set[str],
) -> bool:
    if isinstance(func, ast.Name):
        return func.id in join_funcs
    if not isinstance(func, ast.Attribute) or func.attr != "join":
        return False
    value = func.value
    if isinstance(value, ast.Name):
        return value.id in path_modules
    return (
        isinstance(value, ast.Attribute)
        and value.attr == "path"
        and isinstance(value.value, ast.Name)
        and value.value.id in os_modules
    )


def checkout_relative_interpreter_lines(source: str) -> list[int]:
    """Line numbers of checkout-relative ``.venv/bin/python`` (or ``python3``) joins."""
    tree = ast.parse(source)
    os_modules, path_modules, join_funcs = _os_path_join_names(tree)
    lines: list[int] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            parts = _div_chain_strings(node)
            if parts is not None and _ends_with_interpreter(parts):
                lines.append(node.lineno)
            continue
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        is_joinpath = isinstance(func, ast.Attribute) and func.attr == "joinpath"
        if not is_joinpath and not _is_os_path_join(func, os_modules, path_modules, join_funcs):
            continue
        if _ends_with_interpreter(_trailing_string_args(node)):
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


def test_scanner_flags_collapsed_joinpath_and_os_path_join_forms() -> None:
    source = "\n".join(
        [
            "import os",
            "import os.path as osp",
            "from os import path as ospath",
            "from os.path import join",
            "root = root",
            'a = root / ".venv/bin/python"',
            'b = root / ".venv/bin/python3"',
            'c = root / ".venv" / "bin" / "python3"',
            'd = root.joinpath(".venv", "bin", "python")',
            'e = root.joinpath(".venv", "bin", "python3")',
            'f = root.joinpath(".venv/bin/python")',
            'g = os.path.join(root, ".venv", "bin", "python")',
            'h = os.path.join(root, ".venv", "bin", "python3")',
            'i = osp.join(root, ".venv/bin/python")',
            'j = ospath.join(root, ".venv", "bin", "python")',
            'k = join(root, ".venv", "bin", "python3")',
            'm = root / ".venv" / "bin"',
            'n = root.joinpath("scripts", "tool.py")',
            'p = os.path.join(root, "scripts", "tool.py")',
            'q = " ".join([".venv", "bin", "python"])',
        ]
    )
    assert checkout_relative_interpreter_lines(source) == list(range(6, 17))
