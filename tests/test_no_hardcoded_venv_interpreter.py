"""Fail when a test executes a hard-coded ``.venv/bin/python`` interpreter.

Issue #8788: tests that run Python in a subprocess must use the interpreter
running pytest (``tests.helpers.python.project_python``, which is
``sys.executable``), never a checkout-relative ``.venv/bin/python`` — a dispatch
worktree has no ``.venv`` by design, so such a spawn fails with
``FileNotFoundError``.

This guard scans every ``tests/**/*.py`` for a *spawn argv* built from a
``.venv/bin/python`` literal or a ``... / ".venv" / "bin" / "python"`` join (or
``.joinpath`` / ``os.path.join`` equivalent). Text-only uses — asserting that a
launcher/hook prints ``.venv/bin/python``, a ``tmp_path`` fixture stub, or a
docstring — are not flagged. Any file that still builds such a spawn argv must
be listed in ``ALLOWLIST`` with a reason.

Detector limits (documented on purpose): it only catches the literal / join form
*in the argv position of a spawn call*. A module-level ``PYTHON = ROOT /
".venv" / "bin" / "python"`` that is later handed to ``subprocess`` is not
followed (no dataflow analysis); those must use ``project_python()`` instead.
"""

from __future__ import annotations

import ast
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

_SCAN_SKIP = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    # Sparse-checkout trees are not always present; skip them like other scans.
    "curriculum",
    "data",
    "wiki",
}

_INTERPRETER_TAILS = (
    (".venv", "bin", "python"),
    (".venv", "bin", "python3"),
)

_SUBPROCESS_FUNCS = {"run", "Popen", "call", "check_call", "check_output", "check_input"}
_OS_EXEC_FUNCS = {"execv", "execve", "execl", "execle", "execlp", "execlpe", "execvp", "execvpe"}
_OS_SPAWN_FUNCS = {
    "system",
    "popen",
    "posix_spawn",
    "posix_spawnp",
    "spawnl",
    "spawnle",
    "spawnlp",
    "spawnlpe",
    "spawnv",
    "spawnve",
    "spawnvp",
    "spawnvpe",
}

# Paths owned by other in-flight workers, or the guard itself; never scanned.
_EXCLUDED = {
    "tests/test_no_hardcoded_venv_interpreter.py",
    "tests/test_delegate.py",
    "tests/test_branch_sweep.py",
    "tests/test_jevgrep_update.py",
}

# path -> reason the spawn argv still names ``.venv/bin/python``.
ALLOWLIST: dict[str, str] = {}


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


def _is_interpreter_string(value: str) -> bool:
    if value in (".venv/bin/python", ".venv/bin/python3") or value.endswith(
        ("/.venv/bin/python", "/.venv/bin/python3")
    ):
        return True
    # ``os.system``/``os.popen`` take a single command string (e.g.
    # ``".venv/bin/python -m pytest"``), not a bare argv element.
    return value.startswith((".venv/bin/python ", ".venv/bin/python3 "))


def _trailing_string_args(call: ast.Call) -> list[str]:
    args: list[str] = []
    for arg in reversed(call.args):
        if not isinstance(arg, ast.Constant) or not isinstance(arg.value, str):
            break
        args.append(arg.value)
    args.reverse()
    return args


def _os_path_join_names(tree: ast.AST) -> tuple[set[str], set[str], set[str]]:
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


_WRAPPER_FUNCS = {"str", "Path", "fspath", "os.fspath", "os.path.fspath"}


def _is_wrapper_call(node: ast.Call) -> bool:
    func = node.func
    if isinstance(func, ast.Name) and func.id in {"str", "Path", "fspath"}:
        return True
    if isinstance(func, ast.Attribute) and func.attr == "fspath":
        value = func.value
        if isinstance(value, ast.Name):
            return value.id == "os"
        if isinstance(value, ast.Attribute) and value.attr == "path":
            return isinstance(value.value, ast.Name) and value.value.id == "os"
    return False


def _is_venv_interpreter(
    node: ast.expr,
    os_modules: set[str],
    path_modules: set[str],
    join_funcs: set[str],
) -> bool:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return _is_interpreter_string(node.value)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        parts = _div_chain_strings(node)
        return parts is not None and _ends_with_interpreter(parts)
    if isinstance(node, ast.Call):
        if _is_wrapper_call(node) and len(node.args) == 1:
            return _is_venv_interpreter(node.args[0], os_modules, path_modules, join_funcs)
        is_joinpath = isinstance(node.func, ast.Attribute) and node.func.attr == "joinpath"
        if is_joinpath or _is_os_path_join(node.func, os_modules, path_modules, join_funcs):
            return _ends_with_interpreter(_trailing_string_args(node))
    return False


def _spawn_module_names(tree: ast.AST) -> tuple[set[str], set[str], set[str], set[str]]:
    """Names bound to ``subprocess``, ``os``, and their imported spawn funcs."""
    subprocess_modules: set[str] = set()
    os_modules: set[str] = set()
    subprocess_funcs: set[str] = set()
    os_funcs: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "subprocess":
                    subprocess_modules.add(alias.asname or "subprocess")
                elif alias.name == "os":
                    os_modules.add(alias.asname or "os")
        elif isinstance(node, ast.ImportFrom) and node.module == "subprocess":
            for alias in node.names:
                subprocess_funcs.add(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module == "os":
            for alias in node.names:
                os_funcs.add(alias.asname or alias.name)
    return subprocess_modules, os_modules, subprocess_funcs, os_funcs


def _is_spawn_call(
    func: ast.expr,
    subprocess_modules: set[str],
    os_modules: set[str],
    subprocess_funcs: set[str],
    os_funcs: set[str],
) -> bool:
    if isinstance(func, ast.Name):
        return func.id in subprocess_funcs or func.id in os_funcs
    if not isinstance(func, ast.Attribute):
        return False
    value = func.value
    if isinstance(value, ast.Name):
        if value.id in subprocess_modules and func.attr in _SUBPROCESS_FUNCS:
            return True
        if value.id in os_modules and func.attr in (_OS_EXEC_FUNCS | _OS_SPAWN_FUNCS):
            return True
    return False


def _argv_first_element(node: ast.expr) -> ast.expr:
    if isinstance(node, (ast.List, ast.Tuple)) and node.elts:
        return node.elts[0]
    return node


def executing_venv_interpreter_lines(source: str) -> list[int]:
    """Line numbers of spawn argv built from a ``.venv/bin/python`` literal/join."""
    tree = ast.parse(source)
    os_modules, path_modules, join_funcs = _os_path_join_names(tree)
    subprocess_modules, subprocess_os_modules, subprocess_funcs, os_funcs = _spawn_module_names(tree)
    lines: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not node.args:
            continue
        if not _is_spawn_call(node.func, subprocess_modules, subprocess_os_modules, subprocess_funcs, os_funcs):
            continue
        argv = _argv_first_element(node.args[0])
        if _is_venv_interpreter(argv, os_modules, path_modules, join_funcs):
            lines.append(node.lineno)
    return lines


def _collect_hits() -> dict[str, int]:
    hits: dict[str, int] = {}
    for dirpath, dirnames, filenames in os.walk(REPO_ROOT / "tests"):
        dirnames[:] = sorted(name for name in dirnames if name not in _SCAN_SKIP and not name.startswith("."))
        for name in filenames:
            if not name.endswith(".py"):
                continue
            path = Path(dirpath) / name
            relative = path.relative_to(REPO_ROOT).as_posix()
            if relative in _EXCLUDED:
                continue
            try:
                source = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            count = len(executing_venv_interpreter_lines(source))
            if count:
                hits[relative] = count
    return hits


def test_no_executing_hardcoded_venv_interpreter() -> None:
    hits = _collect_hits()
    unexpected = sorted(set(hits) - set(ALLOWLIST))
    stale = sorted(set(ALLOWLIST) - set(hits))
    assert unexpected == [], (
        "new executing `.venv/bin/python` spawn argv — use tests.helpers.python.project_python():\n"
        + "\n".join(unexpected)
    )
    assert stale == [], "allowlist entry has no executing spawn:\n" + "\n".join(stale)
