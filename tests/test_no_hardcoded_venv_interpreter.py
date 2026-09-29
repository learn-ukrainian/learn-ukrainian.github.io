"""Fail when a test executes a hard-coded ``.venv/bin/python`` interpreter.

Issue #8788: tests that run Python in a subprocess must use the interpreter
running pytest (``tests.helpers.python.project_python``, which is
``sys.executable``), never a checkout-relative ``.venv/bin/python`` — a dispatch
worktree has no ``.venv`` by design, so such a spawn fails with
``FileNotFoundError``.

The guard scans every ``tests/**/*.py`` (no directory is skipped except caches
and hidden directories) and flags:

* a *spawn* — ``subprocess.*``, ``os.exec*`` / ``os.spawn*`` / ``os.system`` /
  ``os.popen``, ``asyncio.create_subprocess_*`` — whose argv (or command
  string) is a ``.venv/bin/python`` expression, either inline or reached through
  a name bound to one (``PY = ROOT / ".venv" / "bin" / "python"``,
  ``f"{ROOT}/.venv/bin/python"``, a shell-command variable
  (``cmd = ".venv/bin/python -c 1"; os.system(cmd)``), ``os.path.join(...)``, ``.joinpath(...)``,
  ``Path(..., ".venv", "bin", "python")``, a helper function or fixture that
  returns one, ``cmd = [PY, ...]``), including through ``str()`` /
  ``os.fspath()``;
* the same rooted expression handed to a helper instead of a spawn: as a
  keyword value (``executable=PY``), as the first element of an argv-shaped
  list (``_run([str(PY), ...])``), or as a dict value (``{"X_PYTHON": PY}``);
* an existence gate on such an expression (``.exists()`` / ``.is_file()`` /
  ``os.path.exists`` / ``os.path.isfile`` / ``os.access``), which is how a
  worktree run silently skips instead of failing.

Text-only uses — asserting that a launcher prints ``.venv/bin/python``, the
bare ``".venv/bin/python"`` string in expected-command data, a docstring, a
fixture file body — are not flagged (a bare literal only counts as the argv of
a spawn call), and neither is a path rooted in a temporary directory
(``tmp_path / ".venv" / "bin" / "python"`` stubs).
A list, tuple or dict compared inside an ``assert`` is expected-command data and is
not flagged (a spawn or existence gate inside an ``assert`` still is).
Any file that still needs the real thing must be listed in ``ALLOWLIST`` with a
reason *and* its exact hits (``<enclosing scope>:<shape>`` with a count): the file is not
exempt, only those hits are, so a new violation in an allowlisted file fails — including a
second spawn on an already-pinned line.

Detector limits (documented on purpose): a file without the text ``venv`` is not
analysed; the analysis is one file at a time and
flow-insensitive — a name counts as ``.venv/bin/python`` if *any* assignment in
the file binds it to one, so a later rebinding to ``sys.executable`` does not
clear it; a constant imported from another module is not followed (the module
that defines it is scanned instead); only the first argv element is checked, so
``["env", PY]`` is missed; an interpreter written into a generated shell
script or passed positionally to a helper (not by keyword, not as an argv list)
is missed; ``%`` / ``.format`` string building and tuple unpacking are not
followed; and a temp-directory root is recognised by name (``*tmp*``), by
``tempfile.*`` or by assignment from one — a repo built under ``tmp_path`` and
passed around under another name needs an ``ALLOWLIST`` entry.
"""

from __future__ import annotations

import ast
import os
import re
from collections import Counter
from pathlib import Path
from typing import NamedTuple

REPO_ROOT = Path(__file__).resolve().parents[1]

_SCAN_SKIP = {".git", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".venv", "__pycache__"}

_INTERPRETER_TAILS = (
    (".venv", "bin", "python"),
    (".venv", "bin", "python3"),
)

_SUBPROCESS_FUNCS = {"run", "Popen", "call", "check_call", "check_output", "getoutput", "getstatusoutput"}
_OS_SPAWN_FUNCS = {
    "execv",
    "execve",
    "execl",
    "execle",
    "execlp",
    "execlpe",
    "execvp",
    "execvpe",
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
_ASYNCIO_SPAWN_FUNCS = {"create_subprocess_exec", "create_subprocess_shell"}
_SPAWN_FUNCS_BY_MODULE = {
    "subprocess": _SUBPROCESS_FUNCS,
    "os": _OS_SPAWN_FUNCS,
    "asyncio": _ASYNCIO_SPAWN_FUNCS,
}
_EXISTENCE_METHODS = {"exists", "is_file", "is_symlink"}
_EXISTENCE_OS_PATH_FUNCS = {"exists", "isfile", "islink"}

_PATH_CONSTRUCTORS = {"Path", "PurePath", "PosixPath", "PurePosixPath"}
_PASSTHROUGH_FUNCS = {"str", "fspath", "abspath", "realpath", "normpath", "expanduser", "expandvars"}
_PASSTHROUGH_METHODS = {"resolve", "absolute", "expanduser", "as_posix", "__fspath__", "__str__"}
_PATH_MODULE_NAMES = {"posixpath", "ntpath"}

_TEMP_MARKER = "\x01"
_UNKNOWN_MARKER = "\x00"
_COMMAND_INTERPRETER = re.compile(rf"(?:^|[\s;&|(])(?:[^\s{_TEMP_MARKER}]*/)?\.venv/bin/python3?(?=\s|$)")

# Paths not scanned: the guard's own inline fixtures live in string literals, so
# it scans itself; nothing is excluded.
_EXCLUDED: frozenset[str] = frozenset()

# path -> (reason, the exact hits the file may keep, each with its exact count). A hit is
# ``<enclosing scope>:<shape>`` — line-independent, so the pin survives edits, but hits are
# counted: a second hit of the same identity (same scope, even the same line) fails too.
ALLOWLIST: dict[str, tuple[str, dict[str, int]]] = {
    "tests/helpers/python.py": (
        "require_repo_venv() is the sanctioned gate: it skips when the repo venv is absent",
        {"require_repo_venv:gate": 1},
    ),
    "tests/test_handoff_slot_registry.py": (
        "_helper_root() only picks the checkout that holds the shared interpreter; it never spawns "
        "it and falls back to sys.prefix when the checkout has no .venv",
        {"_helper_root:gate": 1},
    ),
    "tests/orchestration/test_thread_restart_e2e.py": (
        "runs the handoff CLI inside a throwaway git repo built under tmp_path, whose .venv is a "
        "symlink or shim to the primary interpreter; the repo root is not a checkout",
        {"checkout_handoff_command:argv": 1},
    ),
    "tests/test_lexicon_runner_pr1.py": (
        "asserts the production main_checkout_root()/.venv interpreter resolution; the primary "
        "checkout's venv always exists there, and no spawn uses the path",
        {"test_runner_spawns_use_primary_project_interpreter:gate": 1},
    ),
}

# (constant path suffix, rooted-in-a-temp-directory)
_Parts = tuple[tuple[str, ...], bool]
_NO_PARTS: _Parts = ((), False)


def _split(value: str) -> tuple[str, ...]:
    return tuple(piece for piece in value.split("/") if piece)


def _is_interpreter(parts: _Parts) -> bool:
    suffix, temp_rooted = parts
    return not temp_rooted and suffix[-3:] in _INTERPRETER_TAILS


class _Returns(NamedTuple):
    name: str
    value: ast.expr


class _Analyzer:
    """Per-file facts: import aliases plus every name bound to a ``.venv`` path."""

    def __init__(self, tree: ast.AST) -> None:
        self.tree = tree
        self.nodes = list(ast.walk(tree))  # one traversal, shared by every pass below
        self.subprocess_modules: set[str] = set()
        self.os_modules: set[str] = set()
        self.asyncio_modules: set[str] = set()
        self.spawn_names: set[str] = set()
        self.path_modules: set[str] = set(_PATH_MODULE_NAMES)
        self.join_funcs: set[str] = set()
        self.tempfile_names: set[str] = {"tempfile"}
        self.bound: dict[str, _Parts] = {}
        self.commands: set[str] = set()  # names bound to a shell string that runs the venv interpreter
        self._collect_imports()
        self._collect_bindings()
        self._collect_commands()

    # -- imports -----------------------------------------------------------
    def _collect_imports(self) -> None:
        for node in self.nodes:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name.split(".")[0]
                    if alias.name == "subprocess":
                        self.subprocess_modules.add(name)
                    elif alias.name == "os":
                        self.os_modules.add(name)
                    elif alias.name == "asyncio":
                        self.asyncio_modules.add(name)
                    elif alias.name == "os.path" and alias.asname:
                        self.path_modules.add(alias.asname)
                    elif alias.name == "os.path":
                        self.os_modules.add("os")
                    elif alias.name == "tempfile":
                        self.tempfile_names.add(name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname or alias.name
                    if alias.name in _SPAWN_FUNCS_BY_MODULE.get(node.module or "", ()):
                        self.spawn_names.add(name)
                    elif node.module == "os" and alias.name == "path":
                        self.path_modules.add(name)
                    elif node.module == "os.path" and alias.name == "join":
                        self.join_funcs.add(name)

    # -- path evaluation ---------------------------------------------------
    def _is_os_path_join(self, func: ast.expr) -> bool:
        if isinstance(func, ast.Name):
            return func.id in self.join_funcs
        if not isinstance(func, ast.Attribute) or func.attr != "join":
            return False
        value = func.value
        if isinstance(value, ast.Name):
            return value.id in self.path_modules
        return (
            isinstance(value, ast.Attribute)
            and value.attr == "path"
            and isinstance(value.value, ast.Name)
            and value.value.id in self.os_modules
        )

    def _is_tempfile_call(self, node: ast.Call) -> bool:
        func = node.func
        return (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id in self.tempfile_names
        )

    def _join(self, nodes: list[ast.expr]) -> _Parts:
        if not nodes:
            return _NO_PARTS
        suffix, temp_rooted = self.parts(nodes[0])
        for extra in nodes[1:]:
            if isinstance(extra, ast.Constant) and isinstance(extra.value, str):
                suffix = suffix + _split(extra.value)
            else:
                suffix = ()
        return suffix, temp_rooted

    def parts(self, node: ast.expr) -> _Parts:
        """The constant path suffix of ``node`` and whether it is temp-dir rooted."""
        if isinstance(node, ast.Constant):
            return (_split(node.value), False) if isinstance(node.value, str) else _NO_PARTS
        if isinstance(node, ast.Name):
            if node.id in self.bound:
                return self.bound[node.id]
            return ((), "tmp" in node.id.lower())
        if isinstance(node, ast.Attribute):
            if node.attr in self.bound:
                return self.bound[node.attr]
            return ((), self.parts(node.value)[1])
        if isinstance(node, ast.Starred):
            return self.parts(node.value)
        if isinstance(node, (ast.List, ast.Tuple)):
            return self.parts(node.elts[0]) if node.elts else _NO_PARTS
        if isinstance(node, ast.BinOp):
            return self._binop_parts(node)
        if isinstance(node, ast.JoinedStr):
            return self._fstring_parts(node)
        if isinstance(node, ast.Call):
            return self._call_parts(node)
        return _NO_PARTS

    def _binop_parts(self, node: ast.BinOp) -> _Parts:
        if not isinstance(node.op, (ast.Div, ast.Add)):
            return _NO_PARTS
        suffix, temp_rooted = self.parts(node.left)
        right = node.right
        if isinstance(right, ast.Constant) and isinstance(right.value, str):
            return suffix + _split(right.value), temp_rooted
        if isinstance(right, ast.Name) and right.id in self.bound and isinstance(node.op, ast.Div):
            return suffix + self.bound[right.id][0], temp_rooted
        if isinstance(node.op, ast.Add) and isinstance(right, (ast.List, ast.Tuple)):
            return suffix, temp_rooted  # argv concatenation keeps the first element
        return (), temp_rooted

    def _fstring_parts(self, node: ast.JoinedStr) -> _Parts:
        pieces: list[str] = []
        temp_rooted = False
        for index, value in enumerate(node.values):
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                pieces.append(value.value)
                continue
            inner = self.parts(value.value) if isinstance(value, ast.FormattedValue) else _NO_PARTS
            if index == 0:
                temp_rooted = inner[1]
            pieces.append("/".join(inner[0]) if inner[0] else _UNKNOWN_MARKER)
        return _split("".join(pieces)), temp_rooted

    def _call_parts(self, node: ast.Call) -> _Parts:
        func = node.func
        if isinstance(func, ast.Attribute):
            if func.attr == "joinpath":
                return self._join([func.value, *node.args])
            if func.attr in _PASSTHROUGH_METHODS and not node.args:
                return self.parts(func.value)
        if self._is_os_path_join(func) or (isinstance(func, ast.Name) and func.id in _PATH_CONSTRUCTORS):
            return self._join(list(node.args))
        name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else ""
        if name in _PASSTHROUGH_FUNCS and len(node.args) == 1:
            return self.parts(node.args[0])
        if name in {"get", "getenv"} and len(node.args) == 2:
            return self.parts(node.args[1])  # ``os.environ.get("X", ".venv/bin/python")``
        if self._is_tempfile_call(node):
            return ((), True)
        if name in self.bound:
            return self.bound[name]  # helper function / fixture returning a path
        return _NO_PARTS

    # -- bindings ----------------------------------------------------------
    def _bind(self, key: str, value: _Parts) -> bool:
        if not value[0] and not value[1]:
            return False
        old = self.bound.get(key)
        if old == value:
            return False
        if old is not None:
            better = ".venv" in value[0] and (".venv" not in old[0] or (old[1] and not value[1]))
            if not better:
                return False
        self.bound[key] = value
        return True

    @staticmethod
    def _target_key(target: ast.expr) -> str | None:
        if isinstance(target, ast.Name):
            return target.id
        if isinstance(target, ast.Attribute):
            return target.attr
        return None

    def _collect_bindings(self) -> None:
        binders: list[ast.AST] = []
        for node in self.nodes:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # A helper's ``return`` values bind the helper's own name.
                binders.extend(
                    _Returns(node.name, child.value)
                    for child in ast.walk(node)
                    if isinstance(child, ast.Return) and child.value is not None
                )
            elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.For, ast.With)):
                binders.append(node)
        for _ in range(8):
            changed = False
            for node in binders:
                if isinstance(node, _Returns):
                    changed |= self._bind(node.name, self.parts(node.value))
                    continue
                if isinstance(node, ast.Assign):
                    keys = [self._target_key(target) for target in node.targets]
                    value = node.value
                elif isinstance(node, ast.AnnAssign) and node.value is not None:
                    keys = [self._target_key(node.target)]
                    value = node.value
                elif isinstance(node, ast.For):
                    key = self._target_key(node.target)
                    if key and self._bind(key, self.parts(node.iter)):
                        changed = True
                    continue
                elif isinstance(node, ast.With):
                    for item in node.items:
                        key = self._target_key(item.optional_vars) if item.optional_vars else None
                        if key and self._bind(key, self.parts(item.context_expr)):
                            changed = True
                    continue
                else:
                    continue
                parts = self.parts(value)
                for key in keys:
                    if key is not None:
                        changed |= self._bind(key, parts)
            if not changed:
                return

    def _collect_commands(self) -> None:
        """Names bound to a shell command string naming ``.venv/bin/python``.

        Monotone over a fixed set of assignments, so it ends after at most one round per name
        (a name bound to itself or two names bound to each other add nothing new).
        """
        assignments: list[tuple[str, ast.expr]] = []
        for node in self.nodes:
            if isinstance(node, ast.Assign):
                pairs = [(self._target_key(target), node.value) for target in node.targets]
            elif isinstance(node, ast.AnnAssign) and node.value is not None:
                pairs = [(self._target_key(node.target), node.value)]
            else:
                continue
            assignments.extend((key, value) for key, value in pairs if key is not None)
        changed = True
        while changed:
            changed = False
            for key, value in assignments:
                if key not in self.commands and _COMMAND_INTERPRETER.search(self._command_text(value)):
                    self.commands.add(key)
                    changed = True

    # -- detection ---------------------------------------------------------
    def _is_spawn_call(self, func: ast.expr) -> bool:
        if isinstance(func, ast.Name):
            return func.id in self.spawn_names
        if not (isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name)):
            return False
        module, attr = func.value.id, func.attr
        return (
            (module in self.subprocess_modules and attr in _SUBPROCESS_FUNCS)
            or (module in self.os_modules and attr in _OS_SPAWN_FUNCS)
            or (module in self.asyncio_modules and attr in _ASYNCIO_SPAWN_FUNCS)
        )

    def _is_existence_gate(self, node: ast.Call) -> bool:
        func = node.func
        if isinstance(func, ast.Attribute):
            if func.attr in _EXISTENCE_METHODS and not node.args:
                return _is_interpreter(self.parts(func.value))
            if node.args and (
                (func.attr in _EXISTENCE_OS_PATH_FUNCS and self._is_path_module(func.value))
                or (func.attr == "access" and isinstance(func.value, ast.Name) and func.value.id in self.os_modules)
            ):
                return _is_interpreter(self.parts(node.args[0]))
        return False

    def _is_path_module(self, value: ast.expr) -> bool:
        if isinstance(value, ast.Name):
            return value.id in self.path_modules
        return (
            isinstance(value, ast.Attribute)
            and value.attr == "path"
            and isinstance(value.value, ast.Name)
            and value.value.id in self.os_modules
        )

    def _command_text(self, node: ast.expr) -> str:
        """A shell command string with interpreter names spelled out, else ''."""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return self._command_text(node.left) + self._command_text(node.right)
        if isinstance(node, (ast.Name, ast.Attribute)):
            return ".venv/bin/python" if self._target_key(node) in self.commands else ""
        if not isinstance(node, ast.JoinedStr):
            return ""
        pieces: list[str] = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                pieces.append(value.value)
                continue
            inner = self.parts(value.value) if isinstance(value, ast.FormattedValue) else _NO_PARTS
            if _is_interpreter(inner) or (
                isinstance(value, ast.FormattedValue)
                and isinstance(value.value, (ast.Name, ast.Attribute))
                and self._target_key(value.value) in self.commands
            ):
                pieces.append(".venv/bin/python")
            else:
                pieces.append(_TEMP_MARKER if inner[1] else _UNKNOWN_MARKER)
        return "".join(pieces)

    def _spawn_arg_is_venv(self, node: ast.expr) -> bool:
        if _is_interpreter(self.parts(node)):
            return True
        if isinstance(node, (ast.Constant, ast.JoinedStr, ast.BinOp, ast.Name, ast.Attribute)):
            return bool(_COMMAND_INTERPRETER.search(self._command_text(node)))
        return False

    def _is_rooted_interpreter(self, node: ast.expr) -> bool:
        leaf = node
        while isinstance(leaf, (ast.List, ast.Tuple, ast.Starred)):
            if isinstance(leaf, ast.Starred):
                leaf = leaf.value
            elif leaf.elts:
                leaf = leaf.elts[0]
            else:
                return False
        return not isinstance(leaf, ast.Constant) and _is_interpreter(self.parts(node))

    def _assertion_data_ids(self) -> set[int]:
        """Literals compared inside an ``assert``: expected-command data, never a spawn."""
        ignored: set[int] = set()
        for assertion in self.nodes:
            if not isinstance(assertion, ast.Assert):
                continue
            for compare in ast.walk(assertion.test):
                if not isinstance(compare, ast.Compare):
                    continue
                for side in (compare.left, *compare.comparators):
                    if isinstance(side, (ast.List, ast.Tuple, ast.Dict)):
                        ignored.update(id(child) for child in ast.walk(side))
        return ignored

    def _scoped_nodes(self) -> list[tuple[ast.AST, str]]:
        """Every node with the dotted name of its enclosing function/class (iterative)."""
        scoped: list[tuple[ast.AST, str]] = []
        stack: list[tuple[ast.AST, str]] = [(self.tree, "<module>")]
        while stack:
            node, scope = stack.pop()
            scoped.append((node, scope))
            child_scope = scope
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                child_scope = node.name if scope == "<module>" else f"{scope}.{node.name}"
            stack.extend((child, child_scope) for child in ast.iter_child_nodes(node))
        return scoped

    def hits(self) -> list[tuple[int, str]]:
        """``(line, "<enclosing scope>:<shape>")`` for every spawn, gate or handoff."""
        ignored = self._assertion_data_ids()
        found: list[tuple[int, str]] = []
        for node, scope in self._scoped_nodes():
            kind = self._hit_kind(node, ignored)
            if kind is not None:
                found.append((getattr(node, "lineno", 0), f"{scope}:{kind}"))
        return sorted(found)

    def _hit_kind(self, node: ast.AST, ignored: set[int]) -> str | None:
        if isinstance(node, ast.Call):
            if self._is_existence_gate(node):
                return "gate"
            if self._is_spawn_call(node.func):
                args = [*node.args, *(kw.value for kw in node.keywords if kw.arg in {"args", "executable"})]
                return "spawn" if any(self._spawn_arg_is_venv(arg) for arg in args) else None
            # An interpreter handed to a helper by keyword (``executable=``, ``delegate=``).
            if any(self._is_rooted_interpreter(kw.value) for kw in node.keywords if kw.arg):
                return "keyword"
            return None
        if id(node) in ignored:
            return None
        if isinstance(node, (ast.List, ast.Tuple)) and len(node.elts) > 1 and self._is_rooted_interpreter(node.elts[0]):
            # An argv-shaped literal: a rooted interpreter path followed by its arguments. A bare
            # ``".venv/bin/python"`` string is the production command text tests assert on, so
            # only a spawn call (above) makes that one a hit.
            return "argv"
        if isinstance(node, ast.Dict) and any(v is not None and self._is_rooted_interpreter(v) for v in node.values):
            # An interpreter handed over by environment (``{"X_PYTHON": str(PY)}``).
            return "env"
        return None


def executing_venv_interpreter_lines(source: str) -> list[int]:
    """Line numbers of a spawn or existence gate on a ``.venv/bin/python`` expression."""
    return [line for line, _ in _Analyzer(ast.parse(source)).hits()]


def executing_venv_interpreter_hits(source: str) -> dict[str, int]:
    """Line-independent identities (``scope:shape``) of those hits, with how many of each."""
    return dict(sorted(Counter(identity for _, identity in _Analyzer(ast.parse(source)).hits()).items()))


def _collect_hits() -> dict[str, dict[str, int]]:
    hits: dict[str, dict[str, int]] = {}
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
            if "venv" not in source:
                continue  # every detected shape spells the ``.venv`` directory as a string literal
            found = executing_venv_interpreter_hits(source)
            if found:
                hits[relative] = found
    return hits


def test_no_executing_hardcoded_venv_interpreter() -> None:
    hits = _collect_hits()
    pinned = {path: expected for path, (_, expected) in ALLOWLIST.items()}
    unexpected = sorted(f"{path}: {found}" for path, found in hits.items() if found != pinned.get(path))
    stale = sorted(path for path in pinned if path not in hits)
    assert unexpected == [], (
        "new `.venv/bin/python` spawn or existence gate — use tests.helpers.python.project_python() "
        "(an allowlisted file may keep only its pinned hits):\n" + "\n".join(unexpected)
    )
    assert stale == [], "allowlist entry has no `.venv/bin/python` spawn or gate:\n" + "\n".join(stale)


_PREAMBLE = "import asyncio, os, subprocess, tempfile\nfrom pathlib import Path\nROOT = Path('.')\n"

_POSITIVE_CASES = {
    "inline-join": 'subprocess.run([str(ROOT / ".venv" / "bin" / "python"), "-c", "1"])',
    "inline-literal": 'subprocess.run([".venv/bin/python", "-c", "1"])',
    "assigned-constant": 'PY = ROOT / ".venv" / "bin" / "python"\nsubprocess.run([PY, "-c", "1"])',
    "assigned-str-wrapper": 'PY = ROOT / ".venv" / "bin" / "python"\nsubprocess.run([str(PY), "-c", "1"])',
    "assigned-fspath": 'PY = ROOT / ".venv/bin/python"\nsubprocess.check_output([os.fspath(PY), "-c", "1"])',
    "fstring": 'PY = f"{ROOT}/.venv/bin/python"\nsubprocess.Popen([PY, "-c", "1"])',
    "os-path-join": 'PY = os.path.join(str(ROOT), ".venv", "bin", "python")\nsubprocess.call([PY])',
    "joinpath": 'PY = ROOT.joinpath(".venv", "bin", "python")\nsubprocess.check_call([str(PY)])',
    "path-constructor": 'PY = Path(ROOT, ".venv", "bin", "python")\nsubprocess.run([PY])',
    "split-directory": 'VENV = ROOT / ".venv"\nPY = VENV / "bin" / "python"\nsubprocess.run([PY])',
    "helper-return": (
        'def _python():\n    return ROOT / ".venv" / "bin" / "python"\n\n'
        'def test_x():\n    subprocess.run([str(_python()), "-c", "1"])'
    ),
    "fixture-parameter": (
        'def venv_python():\n    return ROOT / ".venv" / "bin" / "python"\n\n'
        "def test_x(venv_python):\n    subprocess.run([venv_python])"
    ),
    "argv-list-variable": 'PY = ROOT / ".venv" / "bin" / "python"\ncmd = [PY, "-m", "x"]\nsubprocess.run(cmd)',
    "self-attribute": (
        "class T:\n    def setup(self):\n"
        '        self.python = ROOT / ".venv" / "bin" / "python"\n'
        "    def run(self):\n        subprocess.run([self.python])"
    ),
    "argv-list-to-helper": '_run([ROOT / ".venv" / "bin" / "python", "-c", "1"])',
    "keyword-handoff": 'PY = ROOT / ".venv" / "bin" / "python"\nRunner(executable=str(PY))',
    "env-dict": 'PY = ROOT / ".venv" / "bin" / "python"\nenv = {"X_PYTHON": str(PY)}',
    "env-default": (
        'PY = Path(os.environ.get("X", ".venv/bin/python")).resolve()\nsubprocess.run([str(PY), "-c", "1"])'
    ),
    "loop-candidate": (
        'def _find():\n    for candidate in [ROOT / ".venv" / "bin" / "python"]:\n        return candidate\n\n'
        'subprocess.run([str(_find()), "-c", "1"])'
    ),
    "os-system-string": 'os.system(".venv/bin/python -m pytest")',
    "os-system-fstring": 'PY = ROOT / ".venv" / "bin" / "python"\nos.system(f"{PY} -m pytest")',
    "shell-string": 'subprocess.run("cd x && .venv/bin/python -m pytest", shell=True)',
    "shell-command-variable": 'cmd = ".venv/bin/python -c 1"\nsubprocess.run(cmd, shell=True)',
    "os-system-command-variable": 'cmd = ".venv/bin/python -c 1"\nos.system(cmd)',
    "command-variable-fstring": 'cmd = f"{ROOT}/.venv/bin/python -c 1"\nos.system(cmd)',
    "command-variable-chain": (
        'a = ".venv/bin/python -c 1"\nb = a + " x"\nc = f"cd y && {b}"\nsubprocess.run(c, shell=True)'
    ),
    "command-attribute": (
        'class T:\n    def setup(self):\n        self.cmd = ".venv/bin/python -c 1"\n'
        "    def run(self):\n        os.system(self.cmd)"
    ),
    "spawn-inside-assert": 'assert subprocess.run([ROOT / ".venv" / "bin" / "python", "-V"]).returncode == 0',
    "os-exec": 'PY = ROOT / ".venv" / "bin" / "python"\nos.execv(PY, [PY, "-c", "1"])',
    "asyncio": 'PY = ROOT / ".venv" / "bin" / "python"\nasyncio.create_subprocess_exec(PY, "-c", "1")',
    "from-import": 'from subprocess import run\nPY = ROOT / ".venv" / "bin" / "python"\nrun([PY])',
    "skip-gate-method": 'PY = ROOT / ".venv" / "bin" / "python"\nskip = not PY.exists()',
    "skip-gate-is-file": 'assert (ROOT / ".venv" / "bin" / "python").is_file()',
    "skip-gate-os-path": 'PY = ROOT / ".venv" / "bin" / "python"\nos.path.isfile(PY)',
}

_NEGATIVE_CASES = {
    "sys-executable": 'import sys\nsubprocess.run([sys.executable, "-c", "1"])',
    "tmp-path-stub": (
        "def test_x(tmp_path):\n"
        '    python = tmp_path / ".venv" / "bin" / "python"\n'
        "    python.parent.mkdir(parents=True)\n"
        "    if python.exists():\n"
        "        subprocess.run([str(python), '-c', '1'])"
    ),
    "tmp-derived-root": (
        "def test_x(tmp_path):\n"
        '    repo = tmp_path / "repo"\n'
        '    python = repo / ".venv" / "bin" / "python"\n'
        "    subprocess.run([python])"
    ),
    "tempfile-root": (
        "def test_x():\n"
        "    with tempfile.TemporaryDirectory() as d:\n"
        '        py = Path(d) / ".venv" / "bin" / "python"\n'
        "        subprocess.run([py])"
    ),
    "tmp-fstring": 'def test_x(tmp_path):\n    subprocess.run(f"{tmp_path}/.venv/bin/python -c 1", shell=True)',
    "assertion-string": 'def test_x(out):\n    assert ".venv/bin/python" in out\n    assert out == ROOT / ".venv" / "bin" / "python"',
    "text-fixture": 'def test_x(tmp_path):\n    (tmp_path / "hook.sh").write_text("exec .venv/bin/python run.py\\n")',
    "docstring": 'def test_x():\n    """Runs .venv/bin/python -m pytest."""',
    "venv-directory-only": 'subprocess.run(["ls", str(ROOT / ".venv" / "bin")])',
    "parent-of-interpreter": 'PY = ROOT / ".venv" / "bin" / "python"\nsubprocess.run([PY.parent / "pip"])',
    "assert-expected-command": 'def test_x(command):\n    assert command == [ROOT / ".venv" / "bin" / "python", "-V"]',
    "assert-expected-tuple": 'assert command in ((ROOT / ".venv" / "bin" / "python", "-V"),)',
    "assert-expected-env": 'assert env == {"X_PYTHON": str(ROOT / ".venv" / "bin" / "python")}',
    "command-variable-unrelated": 'cmd = "ls -l"\nsubprocess.run(cmd, shell=True)',
    "command-variable-cycle": "a = b\nb = a\nos.system(a)",
    "command-variable-self": "cmd = cmd\nos.system(cmd)",
    "command-variable-tmp": 'def test_x(tmp_path):\n    cmd = f"{tmp_path}/.venv/bin/python -c 1"\n    os.system(cmd)',
    "expected-argv-data": 'assert command[:2] == [".venv/bin/python", "scripts/x.py"]',
    "bare-literal-keyword": 'plan(argv=[".venv/bin/python", "scripts/x.py"])',
    "bare-literal-dict": 'config = {"cmd": ".venv/bin/python"}',
    "unrelated-spawn": 'subprocess.run(["git", "status"])',
    "non-spawn-call": 'print(str(ROOT / ".venv" / "bin" / "python"))',
    "other-name-exists": 'PY = ROOT / "bin" / "python"\nassert PY.exists()',
}


def test_detector_flags_exactly_the_positive_cases() -> None:
    flagged = {name for name, body in _POSITIVE_CASES.items() if executing_venv_interpreter_lines(_PREAMBLE + body)}
    assert flagged == set(_POSITIVE_CASES), sorted(set(_POSITIVE_CASES) - flagged)
    wrongly_flagged = {
        name for name, body in _NEGATIVE_CASES.items() if executing_venv_interpreter_lines(_PREAMBLE + body)
    }
    assert wrongly_flagged == set(), sorted(wrongly_flagged)


def test_allowlisted_file_cannot_gain_a_hit() -> None:
    """A hit in a new scope, or of a new shape in a pinned scope, changes the counted identities."""
    pinned = 'def gate():\n    return (ROOT / ".venv" / "bin" / "python").exists()\n'
    assert executing_venv_interpreter_hits(_PREAMBLE + pinned) == {"gate:gate": 1}
    second = pinned + '\ndef other():\n    subprocess.run([str(ROOT / ".venv" / "bin" / "python")])\n'
    assert executing_venv_interpreter_hits(_PREAMBLE + second) == {"gate:gate": 1, "other:spawn": 1}
    same_scope = pinned.replace("return", 'subprocess.run(".venv/bin/python -c 1", shell=True)\n    return')
    assert executing_venv_interpreter_hits(_PREAMBLE + same_scope) == {"gate:gate": 1, "gate:spawn": 1}
    moved = "\n\n\n" + pinned
    assert executing_venv_interpreter_hits(_PREAMBLE + moved) == {"gate:gate": 1}


def test_allowlist_pins_count_duplicate_hits() -> None:
    """A duplicate of an already-pinned identity fails: pins are counts, not sets."""
    path = "tests/helpers/python.py"
    helper = (REPO_ROOT / path).read_text(encoding="utf-8")
    pin = ALLOWLIST[path][1]
    assert executing_venv_interpreter_hits(helper) == pin  # the real file matches its pin

    gate = "    if not venv.is_file():\n"
    assert helper.count(gate) == 1
    spawn = "subprocess.run([str(venv)])"
    variants = {
        # a second spawn on the very line of the pinned gate (different shape, same line)
        "same-line-spawn": "import subprocess\n" + helper.replace(gate, f"    if not venv.is_file() or {spawn}:\n"),
        # a second gate of the same shape on the pinned gate's own line
        "same-line-gate": helper.replace(gate, "    if not venv.is_file() or not venv.exists():\n"),
        # a second gate of the same shape elsewhere in the same scope
        "same-scope-gate": helper.replace("    return venv\n", "    venv.exists()\n    return venv\n"),
    }
    for name, source in variants.items():
        assert source != helper, name
        assert executing_venv_interpreter_hits(source) != pin, name
    assert executing_venv_interpreter_hits(variants["same-line-gate"]) == {"require_repo_venv:gate": 2}
    assert executing_venv_interpreter_hits(variants["same-scope-gate"]) == {"require_repo_venv:gate": 2}
    assert executing_venv_interpreter_hits(variants["same-line-spawn"]) == {
        "require_repo_venv:gate": 1,
        "require_repo_venv:spawn": 1,
    }
