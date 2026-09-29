"""Static, tracked-tree coverage for the full-PR test area lanes.

An area may be skipped only when a PR changes nothing its tests can reach, so
the proof follows the transitive closure of every area test: static imports
(absolute and relative), ``importlib.import_module("…")`` / ``__import__("…")``
/ ``pytest.importorskip("…")`` / ``runpy.run_module("…")`` string literals,
``pytest_plugins``, dotted ``scripts.…`` literals (``python -m``, patch
targets) and tracked ``*.py`` path literals, plus every ancestor
``conftest.py`` and parent package ``__init__.py``. Imports inside functions
count too: a test reaches whatever it can call. Tracked data files named by
an area test or by any module it reaches must be inside the roots as well:
root-relative literals (``"registry/practice/x.json"``) and static ``Path``
expressions, resolved through module constants and imported names
(``REGISTRY_ROOT / "lexicon/x.yaml"`` with ``REGISTRY_ROOT`` from
``scripts.storage.paths``). A named directory covers every tracked file under
it; the repo root and top-level trees are anchors, not reads. Computed paths
from those anchors escape every area unless their components are static. Paths that force
the full tier (``hits_shared_root_denylist``) need no root, but their imports
and data are followed.

Completeness: a test that imports an area package and whose reach fits the
roots must be listed in the area; tests whose reach does not fit stay out and
always run.
"""

from __future__ import annotations

import ast
import functools
import gc
import importlib.metadata
import posixpath
import subprocess
import sys
from collections import defaultdict
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

import pytest

from scripts.ci.classify_changes import hits_shared_root_denylist
from scripts.ci.test_areas import AUDITED_COMPUTED_REPO_PATHS, load_areas, matches_root, matches_test

pytestmark = pytest.mark.repo_wide

_REPO = Path(__file__).resolve().parents[1]
# The repo root, the scripts/ sys.path entry many modules insert, and the
# v4 runtime's src layout.
_SEARCH_BASES = ("", "scripts/", "packages/v4-runtime/src/")
# Area packages: a test importing one must join the area when its reach fits.
_AREA_MODULES = {
    "open_model_data": ("scripts.projects.open_model_data", "learn_ukrainian_v4_runtime"),
    "atlas": ("scripts.atlas", "scripts.lexicon", "scripts.practice", "scripts.practice_deck", "scripts.etymology"),
}
_LITERAL_MODULE_HEADS = ("scripts", "tests", "learn_ukrainian_v4_runtime")
_MODULE_CALLS = {"import_module", "__import__", "importorskip", "run_module"}
_OS_PATH_MODULES = {"os.path", "posixpath", "path"}
# Text a module must contain for ``caller_data`` to find a caller-controlled path.
_CALLER_MARKERS = ("sparse_trees", "needs_artifact")
# The only node kinds any pass below reads; ``_walk`` keeps just these.
_KEPT = frozenset(
    (
        ast.Module,
        ast.ClassDef,
        ast.FunctionDef,
        ast.AsyncFunctionDef,
        ast.Import,
        ast.ImportFrom,
        ast.Call,
        ast.Assign,
        ast.AnnAssign,
        ast.BinOp,
        ast.Constant,
    )
)
# Contexts and operators are childless and matter to no pass.
_INERT = (ast.expr_context, ast.operator, ast.boolop, ast.unaryop, ast.cmpop)
# Parser output uses exactly these classes: every node kind except the inert ones.
_WALKED = frozenset(
    kind
    for kind in vars(ast).values()
    if isinstance(kind, type) and issubclass(kind, ast.AST) and not issubclass(kind, _INERT)
)
# ``data`` acts only on loops, calls and ``/`` chains, so it never descends into leaves.
_VISITED = _WALKED - {ast.Name, ast.Constant}
_PATH_BUILDERS = {"Path", "PurePath", "PurePosixPath"}
# Every call name ``_anchor`` and ``_computed`` react to; any other call is no path expression.
_ANCHOR_CALLS = {
    "resolve",
    "absolute",
    "expanduser",
    "joinpath",
    "with_name",
    "dirname",
    "abspath",
    "realpath",
    "join",
    *_PATH_BUILDERS,
}
# Pure in the path, and asked about the same modules once per test per area.
_denylisted = functools.cache(hits_shared_root_denylist)


@functools.cache
def _external_modules() -> frozenset[str]:
    """Top-level names the interpreter or an installed distribution provides.

    Scanning every installed distribution takes seconds and never changes within a run.
    """
    return frozenset(sys.stdlib_module_names) | frozenset(importlib.metadata.packages_distributions())


def _tracked() -> set[str]:
    return set(
        subprocess.check_output(
            ["git", "ls-files"],
            cwd=_REPO,
            text=True,
            timeout=30,
        ).splitlines()
    )


def _package(path: str) -> list[str]:
    return list(PurePosixPath(path).parent.parts)


def _relative(path: str, level: int, module: str | None) -> str:
    parts = _package(path)
    parts = parts[: len(parts) - (level - 1)] if level > 1 else parts
    return ".".join([*parts, *([module] if module else [])])


def _call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def _str_value(node: ast.AST | None) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def _joined(node: ast.BinOp) -> str | None:
    """``ROOT / "registry" / "practice" / "deck.json"`` -> ``registry/practice/deck.json``."""
    parts: list[str] = []
    while isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        if (right := _str_value(node.right)) is None:
            return None
        parts.append(right)
        node = node.left
    if (left := _str_value(node)) is not None:
        parts.append(left)
    return "/".join(reversed(parts)) if len(parts) > 1 else None


def _join(base: str | None, parts: list[str]) -> str | None:
    """Repo-relative join (``""`` is the repo root); ``None`` if it leaves the repo."""
    if base is None:
        return None
    joined = posixpath.normpath("/".join([base, *parts]).strip("/") or ".")
    if joined == ".":
        return ""
    return None if joined.startswith("..") or joined.startswith("/") else joined


def _parent(path: str | None, levels: int = 1) -> str | None:
    for _ in range(levels):
        if not path:
            return None
        path = posixpath.dirname(path)
    return path


def _walk(tree: ast.Module) -> tuple[list[ast.AST], dict[str, int]]:
    """One breadth-first pass: the ``_KEPT`` nodes in ``ast.walk`` order, and how often each name is written.

    ``ast.walk`` over every node of every module, once per pass, was the cost of this test.
    """
    kept: list[ast.AST] = []
    writes: dict[str, int] = defaultdict(int)
    pending: list[ast.AST] = [tree]
    for node in pending:  # a list iterated while it grows is a queue
        kind = type(node)
        if kind is ast.Name:
            if type(node.ctx) is ast.Store:
                writes[node.id] += 1
            continue
        if kind is ast.Constant:
            kept.append(node)
            continue
        if kind in _KEPT:
            kept.append(node)
        elif kind is ast.arg:
            writes[node.arg] += 1
        for name in kind._fields:
            child = getattr(node, name, None)
            if type(child) is list:
                pending.extend([item for item in child if type(item) in _WALKED])
            elif type(child) in _WALKED:
                pending.append(child)
    return kept, writes


def _imports(source: str, path: str, nodes: list[ast.AST] | None = None) -> tuple[set[str], set[str]]:
    """Module names (exact) and loose string literals (resolved leniently) in one file.

    ``nodes`` is the breadth-first walk of ``source`` when the caller already has it."""
    names: set[str] = set()
    literals: set[str] = set()
    docstrings: set[int] = set()
    joined: set[int] = set()
    # ast.walk is breadth-first, so a docstring's owner is seen before it.
    for node in nodes if nodes is not None else ast.walk(ast.parse(source, filename=path)):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                docstrings.add(id(first.value))
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = _relative(path, node.level, node.module) if node.level else node.module
            if module:
                names.add(module)
                names.update(f"{module}.{alias.name}" for alias in node.names)
        elif isinstance(node, ast.Call) and _call_name(node) in _MODULE_CALLS and node.args:
            target = _str_value(node.args[0])
            if target is None:
                continue
            if target.startswith("."):
                package = next((_str_value(k.value) for k in node.keywords if k.arg == "package"), None)
                if not package:
                    continue
                level = len(target) - len(target.lstrip("."))
                target = ".".join([*package.split(".")[: len(package.split(".")) - (level - 1)], target.lstrip(".")])
            names.add(target)
            for keyword in node.keywords:
                if keyword.arg == "fromlist" and isinstance(keyword.value, (ast.List, ast.Tuple)):
                    names.update(f"{target}.{item}" for element in keyword.value.elts if (item := _str_value(element)))
        elif isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "pytest_plugins" for target in node.targets
        ):
            values = node.value.elts if isinstance(node.value, (ast.List, ast.Tuple)) else [node.value]
            names.update(value for element in values if (value := _str_value(element)))
        elif isinstance(node, ast.BinOp) and id(node) not in joined and (chain := _joined(node)):
            literals.add(chain)
            inner = node.left
            while isinstance(inner, ast.BinOp):
                joined.add(id(inner))
                inner = inner.left
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings:
            literals.update(node.value.split())
            if "import " in node.value and "\n" in node.value:
                # An inline ``python -c`` script: its imports are the child's.
                try:
                    inline, _ = _imports(node.value, path)
                except SyntaxError:
                    continue
                names |= inline
    return names, literals


@dataclass
class _Scope:
    names: dict[str, str]  # local name -> repo-relative path
    modules: dict[str, str]  # module alias -> tracked module file
    strings: dict[str, str]  # module constant or literal-loop binding


class _Graph:
    """Repo-file import graph over tracked Python files."""

    def __init__(self, tracked: set[str], read: Callable[[str], str] | None = None) -> None:
        self.modules = {path for path in tracked if path.endswith(".py")}
        self.files = tracked
        self.dirs: dict[str, set[str]] = defaultdict(set)
        for path in tracked:
            parent = posixpath.dirname(path)
            while parent:
                self.dirs[parent].add(path)
                parent = posixpath.dirname(parent)
        self._read = read or (lambda path: (_REPO / path).read_text(encoding="utf-8"))
        self._sources: dict[str, str] = {}
        self._resolved: dict[tuple[str, str], frozenset[str]] = {}
        self._refs: dict[str, tuple[set[str], set[str]]] = {}
        self._edges: dict[str, frozenset[str]] = {}
        self._trees: dict[str, ast.Module] = {}
        self._walks: dict[str, tuple[list[ast.AST], dict[str, int]]] = {}
        self._consts: dict[str, dict[str, str]] = {}
        self._data: dict[str, frozenset[str]] = {}
        self.audited_sites: set[tuple[tuple[str, str], str]] = set()
        self._callers: dict[str, frozenset[str]] = {}
        self._scopes: dict[str, _Scope] = {}
        self._computing: set[str] = set()  # modules whose ``consts`` is being built
        self._cycles = 0  # times ``consts`` was asked for a module still being built
        self._reach: dict[tuple[tuple[str, ...], tuple[str, ...]], dict[str, frozenset[str]]] = {}
        self.by_top: dict[str, set[str]] = defaultdict(set)
        for path in self.modules:
            pure = PurePosixPath(path)
            if pure.name == "__init__.py":
                self.by_top[pure.parent.name].add(str(pure.parent.parent))
            else:
                self.by_top[pure.stem].add(str(pure.parent))
        self.external = _external_modules()

    def _at(self, base: str, name: str) -> set[str]:
        stem = (base.rstrip("/") + "/" if base not in ("", ".") else "") + name.replace(".", "/")
        found = {candidate for candidate in (stem + ".py", stem + "/__init__.py") if candidate in self.modules}
        if found:
            parts = stem.split("/")
            found.update(
                init
                for index in range(1, len(parts))
                if (init := "/".join(parts[:index]) + "/__init__.py") in self.modules
            )
        return found

    def read(self, path: str) -> str:
        if path not in self._sources:
            self._sources[path] = self._read(path)
        return self._sources[path]

    def resolve(self, name: str, importer: str) -> set[str]:
        # Only the importer's directory matters: its parents are the search bases.
        key = (name, posixpath.dirname(importer))
        if key not in self._resolved:
            self._resolved[key] = frozenset(self._resolve(name, importer))
        return set(self._resolved[key])

    def _resolve(self, name: str, importer: str) -> set[str]:
        bases = [
            *_SEARCH_BASES,
            *(str(parent) + "/" for parent in PurePosixPath(importer).parents if str(parent) != "."),
        ]
        for base in bases:
            if found := self._at(base, name):
                return found
        top = name.split(".")[0]
        if top in self.external:
            return set()
        # A bare name reachable only through some sys.path.insert(dir): take
        # every tracked directory that could provide it.
        return {path for base in self.by_top.get(top, ()) for path in self._at(base, name)}

    def _literal(self, text: str, importer: str) -> set[str]:
        text = text.strip("'\"(),;:").removeprefix("./")
        if text in self.modules:
            return {text}
        if text.endswith(".py") or text.split(".")[0] not in _LITERAL_MODULE_HEADS:
            return set()
        parts = text.split(".")
        if not all(part.isidentifier() for part in parts):
            return set()
        # Longest importable prefix: a patch target names an attribute.
        for end in range(len(parts), 1, -1):
            if found := self.resolve(".".join(parts[:end]), importer):
                return found
        return set()

    def _tree(self, path: str) -> ast.Module:
        if path not in self._trees:
            self._trees[path] = ast.parse(self.read(path), filename=path)
        return self._trees[path]

    def _facts(self, path: str) -> tuple[list[ast.AST], dict[str, int]]:
        """``_walk`` of ``path``, done once for every pass over it."""
        if path not in self._walks:
            self._walks[path] = _walk(self._tree(path))
        return self._walks[path]

    def _module_file(self, name: str, importer: str) -> str | None:
        stem = name.replace(".", "/")
        return next(
            (
                found
                for found in sorted(self.resolve(name, importer))
                if found.removesuffix(".py").removesuffix("/__init__").endswith(stem)
            ),
            None,
        )

    @staticmethod
    def _string(node: ast.AST, scope: _Scope) -> str | None:
        if isinstance(node, ast.Name):
            return scope.strings.get(node.id)
        return _str_value(node)

    def _anchor(self, node: ast.AST, scope: _Scope) -> str | None:
        """The repo-relative path a ``Path``-building expression denotes, if static."""
        if isinstance(node, ast.Name):
            return scope.names.get(node.id)
        if isinstance(node, ast.Attribute):
            if node.attr == "parent":
                return _parent(self._anchor(node.value, scope))
            if isinstance(node.value, ast.Name) and node.value.id in scope.modules:
                return self.consts(scope.modules[node.value.id]).get(node.attr)
            return None
        if (
            isinstance(node, ast.Subscript)
            and isinstance(node.value, ast.Attribute)
            and node.value.attr == "parents"
            and isinstance(node.slice, ast.Constant)
            and isinstance(node.slice.value, int)
        ):
            return _parent(self._anchor(node.value.value, scope), node.slice.value + 1)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            right = self._string(node.right, scope)
            return None if right is None else _join(self._anchor(node.left, scope), [right])
        if not isinstance(node, ast.Call):
            return None
        name = _call_name(node)
        method = isinstance(node.func, ast.Attribute)
        if method and name in {"resolve", "absolute", "expanduser"} and not node.args:
            return self._anchor(node.func.value, scope)
        strings = [self._string(arg, scope) for arg in node.args]
        if method and name == "joinpath" and None not in strings:
            return _join(self._anchor(node.func.value, scope), strings)
        if method and name == "with_name" and len(strings) == 1 and strings[0] is not None:
            return _join(_parent(self._anchor(node.func.value, scope)), strings)
        os_path = method and ast.unparse(node.func.value) in _OS_PATH_MODULES
        if os_path and name == "dirname" and len(node.args) == 1:
            return _parent(self._anchor(node.args[0], scope))
        if os_path and name in {"abspath", "realpath"} and len(node.args) == 1:
            return self._anchor(node.args[0], scope)
        if os_path and name == "join" and node.args and None not in strings[1:]:
            return _join(self._anchor(node.args[0], scope), strings[1:])
        if name in _PATH_BUILDERS and node.args and None not in strings[1:]:
            if (first := strings[0]) is not None:
                # A relative string counts only where it names a tracked path.
                return None if first.startswith("/") else _join("", [first, *strings[1:]])
            return _join(self._anchor(node.args[0], scope), strings[1:])
        return None

    def _computed(self, node: ast.AST, scope: _Scope) -> bool:
        """A known repo anchor joined to an unresolved component."""
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            return self._anchor(node.left, scope) is not None and self._string(node.right, scope) is None
        if not isinstance(node, ast.Call):
            return False
        name = _call_name(node)
        method = isinstance(node.func, ast.Attribute)
        if method and name == "joinpath":
            base = node.func.value
            parts = node.args
        elif node.args and (
            (method and ast.unparse(node.func.value) in _OS_PATH_MODULES and name == "join") or name in _PATH_BUILDERS
        ):
            base = node.args[0]
            parts = node.args[1:]
        else:
            return False
        return self._anchor(base, scope) is not None and any(self._string(part, scope) is None for part in parts)

    def _scope(self, path: str) -> _Scope:
        """Module-local path names (assignments) and imported names/modules."""
        scope = _Scope({"__file__": path}, {}, {})
        nodes, writes = self._facts(path)
        # Only a single module-level literal binding is a static string. A
        # function local, parameter, or a name assigned twice is not a
        # dependable module constant at its use site.
        bindings: dict[str, list[ast.AST]] = defaultdict(list)
        for stmt in self._tree(path).body:
            if isinstance(stmt, (ast.Assign, ast.AnnAssign)) and stmt.value is not None:
                targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
                for target in targets:
                    if isinstance(target, ast.Name):
                        bindings[target.id].append(stmt.value)
        scope.strings = {
            name: value
            for name, assigned in bindings.items()
            if len(assigned) == writes[name] == 1 and (value := _str_value(assigned[0])) is not None
        }
        for node in nodes:
            if isinstance(node, ast.ImportFrom):
                module = _relative(path, node.level, node.module) if node.level else node.module
                if not module or not (source := self._module_file(module, path)):
                    continue
                for alias in node.names:
                    local = alias.asname or alias.name
                    if (value := self.consts(source).get(alias.name)) is not None:
                        scope.names[local] = value
                    elif sub := self._module_file(f"{module}.{alias.name}", path):
                        scope.modules[local] = sub
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.asname and (source := self._module_file(alias.name, path)):
                        scope.modules[alias.asname] = source
        # Two passes let a name defined after its first use still resolve.
        for _ in range(2):
            for node in nodes:
                if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
                    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                    if (value := self._anchor(node.value, scope)) is not None:
                        scope.names.update((target.id, value) for target in targets if isinstance(target, ast.Name))
        return scope

    def scope(self, path: str) -> _Scope:
        """``_scope`` once per module."""
        if path not in self._scopes:
            self._scopes[path] = self._scope(path)
        return self._scopes[path]

    def consts(self, path: str) -> dict[str, str]:
        """Names ``path`` binds to static repo paths (``REGISTRY_ROOT = ROOT / "registry"``)."""
        if path in self._consts:
            if path in self._computing:
                self._cycles += 1
            return self._consts[path]
        self._consts[path] = {}  # an import cycle sees no names, not a loop
        self._computing.add(path)
        cycles = self._cycles
        try:
            scope = self._scopes.get(path) or self._scope(path)
        finally:
            self._computing.discard(path)
        if self._cycles == cycles:
            # Nothing above saw a half-built module, so this is the scope any later
            # call would compute: keep it instead of walking the module again.
            self._scopes[path] = scope
        self._consts[path] = {name: value for name, value in scope.names.items() if name != "__file__"}
        return self._consts[path]

    def _named(self, text: str, *, anchors: bool = False) -> set[str]:
        """Tracked non-Python files at, or under, repo-relative ``text``."""
        if text.endswith(".py"):
            return set()
        if text in self.files:
            return {text}
        # The repo root or a top-level tree (``REGISTRY_ROOT``) is an anchor
        # other paths are built from, not a read of the whole tree.
        if anchors and "/" not in text:
            return set()
        return {item for item in self.dirs.get(text, ()) if not item.endswith(".py")}

    def _anchorless(self, path: str, scope: _Scope) -> bool:
        """No name, module or ``Path(...)`` call to build a repo path from.

        ``_anchor`` bottoms out in a name of ``scope`` (only ``__file__`` unless
        something was assigned or imported), a module alias, or a ``Path`` call.
        """
        return (
            set(scope.names) == {"__file__"}
            and not scope.modules
            and "__file__" not in self.read(path)
            and not any(
                isinstance(node, ast.Call) and _call_name(node) in _PATH_BUILDERS for node in self._facts(path)[0]
            )
        )

    def data(self, path: str) -> frozenset[str]:
        """Tracked non-Python files ``path`` names: root-relative literals and
        static ``Path`` expressions, including constants imported from other
        modules (``REGISTRY_ROOT / "lexicon/x.yaml"``)."""
        if path in self._data:
            return self._data[path]
        found: set[str] = set()
        for literal in self.refs(path)[1]:
            text = literal.strip("'\"(),;:").removeprefix("./").rstrip("/")
            if "/" in text:
                found |= self._named(text)
        scope = self.scope(path)
        audited_seen: set[tuple[tuple[str, str], str]] = set()

        def visit(node: ast.AST, active: _Scope, inner: set[int], owner: str = "") -> None:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                owner = f"{owner}.{node.name}" if owner else node.name
            if (
                isinstance(node, ast.For)
                and isinstance(node.target, ast.Name)
                and isinstance(node.iter, (ast.Tuple, ast.List))
            ):
                values = [_str_value(item) for item in node.iter.elts]
                if values and all(value is not None for value in values):
                    for value in values:
                        loop_scope = _Scope(active.names, active.modules, {**active.strings, node.target.id: value})
                        for stmt in node.body:
                            visit(stmt, loop_scope, set(), owner)
                    for stmt in node.orelse:
                        visit(stmt, active, inner, owner)
                    return
            if id(node) not in inner and (
                (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div))
                or (isinstance(node, ast.Call) and _call_name(node) in _ANCHOR_CALLS)
            ):
                if (value := self._anchor(node, active)) is not None:
                    found.update(self._named(value, anchors=True))
                    current = node
                    while isinstance(current, ast.BinOp):
                        inner.add(id(current.left))
                        current = current.left
                elif self._computed(node, active):
                    key = (path, owner)
                    expression = ast.unparse(node)
                    audit = (key, expression)
                    if expression in AUDITED_COMPUTED_REPO_PATHS.get(key, ()) and audit not in audited_seen:
                        audited_seen.add(audit)
                    else:
                        found.add(f"<computed repo path: {path}:{node.lineno} {expression}>")
            for name in type(node)._fields:  # ``ast.iter_child_nodes`` order, without its generators
                child = getattr(node, name, None)
                if type(child) is list:
                    for item in child:
                        if type(item) in _VISITED:
                            visit(item, active, inner, owner)
                elif type(child) in _VISITED:
                    visit(child, active, inner, owner)

        if self._anchorless(path, scope):
            # No expression in this module can denote a repo path, so the walk finds none.
            self._data[path] = frozenset(found)
            return self._data[path]
        visit(self._tree(path), scope, set())
        self.audited_sites.update(audited_seen)
        self._data[path] = frozenset(found)
        return self._data[path]

    def caller_data(self, path: str) -> frozenset[str]:
        """Resolve caller-controlled paths in the two audited shared helpers."""
        if path in self._callers:
            return self._callers[path]
        if not any(marker in self.read(path) for marker in _CALLER_MARKERS):
            # Every path this finds sits behind a ``tests.sparse_trees`` import or
            # ``pytest.mark.needs_artifact``; without either name there is nothing to walk.
            self._callers[path] = frozenset()
            return self._callers[path]
        nodes, _ = self._facts(path)
        scope = self.scope(path)
        sparse_names: set[str] = set()
        sparse_modules: set[str] = set()
        marker_names: set[str] = set()
        for node in nodes:
            if isinstance(node, ast.ImportFrom) and node.module == "tests.sparse_trees":
                sparse_names.update(
                    alias.asname or ("tree_absent" if alias.name == "*" else alias.name)
                    for alias in node.names
                    if alias.name in {"tree_absent", "*"}
                )
            elif isinstance(node, ast.ImportFrom) and node.module == "tests":
                sparse_modules.update(
                    alias.asname or alias.name for alias in node.names if alias.name == "sparse_trees"
                )
            elif isinstance(node, ast.Import):
                sparse_modules.update(
                    alias.asname or alias.name for alias in node.names if alias.name == "tests.sparse_trees"
                )
            elif isinstance(node, ast.Assign) and isinstance(node.value, (ast.Name, ast.Attribute)):
                source = ast.unparse(node.value)
                for target in node.targets:
                    if not isinstance(target, ast.Name):
                        continue
                    if source in sparse_names:
                        sparse_names.add(target.id)
                    if source == "pytest.mark.needs_artifact" or source in marker_names:
                        marker_names.add(target.id)
        found: set[str] = set()
        for node in nodes:
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            sparse_call = (isinstance(func, ast.Name) and func.id in sparse_names) or (
                isinstance(func, ast.Attribute)
                and func.attr == "tree_absent"
                and ast.unparse(func.value) in sparse_modules
            )
            marker_call = (isinstance(func, ast.Name) and func.id in marker_names) or (
                isinstance(func, ast.Attribute) and ast.unparse(func).endswith(".mark.needs_artifact")
            )
            if not sparse_call and not marker_call:
                continue
            index = 0 if sparse_call else 1
            value = self._string(node.args[index], scope) if len(node.args) > index else None
            target = _join("", [value]) if sparse_call and value is not None else None
            if sparse_call and target is not None:
                target += "/"  # Directory existence is covered by that area root.
            if marker_call and value is not None:
                target = _join("data", [value])
            found.add(
                target if target is not None else f"<computed caller path: {path}:{node.lineno} {ast.unparse(node)}>"
            )
        self._callers[path] = frozenset(found)
        return self._callers[path]

    def refs(self, path: str) -> tuple[set[str], set[str]]:
        if path not in self._refs:
            self._refs[path] = _imports(self.read(path), path, self._facts(path)[0])
        return self._refs[path]

    def edges(self, path: str) -> frozenset[str]:
        if path in self._edges:
            return self._edges[path]
        names, literals = self.refs(path)
        found: set[str] = set()
        for name in names:
            found |= self.resolve(name, path)
        for literal in literals:
            found |= self._literal(literal, path)
        if path.startswith("tests/"):
            found.update(
                conftest
                for parent in PurePosixPath(path).parents
                if (conftest := f"{parent}/conftest.py") in self.modules
            )
        found.discard(path)
        self._edges[path] = frozenset(found)
        return self._edges[path]

    def closure(self, path: str, stop: Callable[[str], bool] | None = None) -> set[str]:
        """Everything ``path`` reaches; returns early once ``stop`` accepts a module."""
        seen = {path}
        stack = [path]
        while stack:
            for module in self.edges(stack.pop()) - seen:
                seen.add(module)
                if stop is not None and stop(module):
                    stack.clear()
                    break
                stack.append(module)
        seen.discard(path)
        return seen


def _escapes(area: dict[str, list[str]], graph: _Graph, test: str, *, first: bool = False) -> set[str]:
    key = (tuple(area["roots"]), tuple(area["tests"]))
    # Area membership is fixed per module, and modules recur in every test's
    # closure: decide each module (and the data it names) once per area.
    escaping = graph._reach.setdefault(key, {})

    def outside(item: str) -> bool:
        return not (_denylisted(item) or matches_root(item, area["roots"]) or matches_test(item, area["tests"]))

    def leaks(module: str) -> frozenset[str]:
        # Data named by a module (a constant such as ``DEFAULT_VERDICTS =
        # REGISTRY_ROOT / "lexicon/x.yaml"`` is a read) and its caller-controlled paths.
        if module not in escaping:
            escaping[module] = frozenset(
                item for item in (*graph.data(module), *graph.caller_data(module)) if outside(item)
            )
        return escaping[module]

    reached = graph.closure(test, outside if first else None)
    found = {module for module in reached if outside(module)}
    for module in (test, *reached):
        found |= leaks(module)
    return found


def _is_test(path: str) -> bool:
    return path.startswith("tests/") and Path(path).name.startswith("test_") and path.endswith(".py")


def _violations(name: str, area: dict[str, list[str]], graph: _Graph) -> tuple[list[str], list[str]]:
    """(eligible tests left out of the area, reachable modules outside its roots)."""
    heads = _AREA_MODULES[name]
    missing_tests: list[str] = []
    missing_roots: set[str] = set()
    for test in sorted(path for path in graph.modules if _is_test(path)):
        if matches_test(test, area["tests"]):
            missing_roots.update(f"{test} -> {module}" for module in _escapes(area, graph, test))
            continue
        # Cheap text check first: any import of an area module names its package.
        if not any(head.rsplit(".", 1)[-1] in graph.read(test) for head in heads):
            continue
        names, _ = graph.refs(test)
        if any(item == head or item.startswith(head + ".") for item in names for head in heads) and not _escapes(
            area, graph, test, first=True
        ):
            missing_tests.append(test)
    return missing_tests, sorted(missing_roots)


@contextmanager
def _gc_paused() -> Iterator[None]:
    """Parsing the whole reachable tree keeps millions of AST nodes alive; the
    collector re-scans them on every generation-0 pass and costs more than the
    parsing itself. Nothing here makes cycles worth collecting mid-run."""
    was_enabled = gc.isenabled()
    gc.disable()
    try:
        yield
    finally:
        if was_enabled:
            gc.enable()


@pytest.fixture(scope="module")
def graph() -> _Graph:
    return _Graph(_tracked())


def test_every_area_is_closed_and_complete(graph: _Graph) -> None:
    areas = load_areas()
    assert set(areas) == set(_AREA_MODULES)
    with _gc_paused():
        found = {name: _violations(name, area, graph) for name, area in areas.items()}
    for name, (missing_tests, missing_roots) in found.items():
        assert missing_roots == [], name
        assert missing_tests == [], name


def test_shared_modules_are_parsed_once(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every test's closure re-reaches the same modules: analysing each per test, not once, is what
    made the real-repo run exceed the CI timeout (#8872)."""
    sources = {
        "tests/test_a.py": "from scripts.area import shared\n",
        "tests/test_b.py": "from scripts.area import shared\n",
        "scripts/area/shared.py": 'from scripts.area import leaf\nfrom scripts.storage.paths import ROOT\nDATA = ROOT / "registry"\n',
        "scripts/area/leaf.py": "from scripts.storage import paths\n",
        "scripts/storage/paths.py": "ROOT = Path(__file__).resolve().parents[2]\n",
    }
    parsed: list[str] = []
    real_parse = ast.parse

    def counting_parse(source: str, filename: str = "<unknown>", *args, **kwargs):
        parsed.append(filename)
        return real_parse(source, filename, *args, **kwargs)

    monkeypatch.setattr(ast, "parse", counting_parse)
    graph = _Graph(set(sources), read=lambda path: sources[path])
    for roots in (["scripts/area/", "scripts/storage/"], ["scripts/area/"]):
        area = {"tests": ["tests/test_*.py"], "roots": roots}
        for test in ("tests/test_a.py", "tests/test_b.py"):
            _escapes(area, graph, test)
            _escapes(area, graph, test, first=True)
    assert sorted(parsed) == sorted(sources)


def test_incomplete_area_is_rejected() -> None:
    test = "tests/test_area.py"
    root = "scripts/storage/paths.py"
    tracked = {test, "scripts/projects/open_model_data/core.py", root}
    sources = {
        test: "from scripts.projects.open_model_data import core\n",
        "scripts/projects/open_model_data/core.py": "from scripts.storage import paths\n",
    }
    graph = _Graph(tracked, read=lambda path: sources.get(path, ""))
    area = {"tests": [test], "roots": ["scripts/projects/open_model_data/", "scripts/storage/"]}
    assert test in _violations("open_model_data", {**area, "tests": []}, graph)[0]
    assert (
        f"{test} -> {root}"
        in _violations("open_model_data", {**area, "roots": ["scripts/projects/open_model_data/"]}, graph)[1]
    )


def test_data_reached_through_imported_constants() -> None:
    """``test -> atlas_db.py -> REGISTRY_ROOT / "lexicon/…"``: the test names no path."""
    tracked = {
        "tests/test_area.py",
        "scripts/__init__.py",
        "scripts/area/__init__.py",
        "scripts/area/db.py",
        "scripts/storage/__init__.py",
        "scripts/storage/paths.py",
        "registry/lexicon/verdicts.yaml",
        "registry/lexicon/aliases.yaml",
        "registry/decks/a.json",
        "registry/decks/b.json",
        "registry/other.yaml",
        "scripts/area/fixtures/case.json",
        "scripts/area/sibling.json",
        "docs/joined.md",
    }
    sources = {
        "tests/test_area.py": "from scripts.area import db\n",
        "scripts/storage/paths.py": 'ROOT = Path(__file__).resolve().parents[2]\nREGISTRY_ROOT = ROOT / "registry"\n',
        "scripts/area/db.py": (
            "import os\n"
            "from scripts.storage.paths import REGISTRY_ROOT\n"
            "from scripts.storage import paths as store\n"
            'VERDICTS = REGISTRY_ROOT / "lexicon/verdicts.yaml"\n'
            'ALIASES = store.REGISTRY_ROOT.joinpath("lexicon", "aliases.yaml")\n'
            'for name in ("a.json", "b.json"):\n'
            '    DECK = REGISTRY_ROOT / "decks" / name\n'
            'FIXTURES = Path(__file__).parent / "fixtures"\n'
            'SIBLING = Path(__file__).with_name("sibling.json")\n'
            'JOINED = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "joined.md")\n'
        ),
    }
    graph = _Graph(tracked, read=lambda path: sources.get(path, ""))
    assert graph.consts("scripts/storage/paths.py") == {"ROOT": "", "REGISTRY_ROOT": "registry"}
    # REGISTRY_ROOT itself is an anchor: registry/other.yaml is not read.
    assert graph.data("scripts/area/db.py") == {
        "registry/lexicon/verdicts.yaml",
        "registry/lexicon/aliases.yaml",
        "registry/decks/a.json",
        "registry/decks/b.json",
        "scripts/area/fixtures/case.json",
        "scripts/area/sibling.json",
        "docs/joined.md",
    }
    area = {"tests": ["tests/test_area.py"], "roots": ["scripts/area/", "scripts/storage/", "docs/"]}
    assert _escapes(area, graph, "tests/test_area.py") == {
        "registry/lexicon/verdicts.yaml",
        "registry/lexicon/aliases.yaml",
        "registry/decks/a.json",
        "registry/decks/b.json",
    }
    widened = {**area, "roots": [*area["roots"], "registry/lexicon/", "registry/decks/"]}
    assert _escapes(widened, graph, "tests/test_area.py") == set()


def test_computed_repo_root_read_is_not_admitted() -> None:
    tracked = {"tests/test_area.py", "scripts/area/__init__.py", "scripts/area/read.py", "docs/elsewhere.json"}
    sources = {
        "tests/test_area.py": "from scripts.area import read\n",
        "scripts/area/read.py": "ROOT = Path(__file__).resolve().parents[2]\nname = input()\nDATA = ROOT / name\n",
    }
    graph = _Graph(tracked, read=lambda path: sources.get(path, ""))
    area = {"tests": ["tests/test_area.py"], "roots": ["scripts/area/"]}
    assert any("ROOT / name" in item for item in _escapes(area, graph, "tests/test_area.py"))


def test_audited_computed_paths_are_an_exact_set() -> None:
    expected = {
        ("tests/conftest.py", "_resolve_module"): frozenset(
            {"_REPO_ROOT / rel.with_suffix('.py')", "_REPO_ROOT / rel"}
        ),
        ("tests/conftest.py", "_analyze_test_module"): frozenset({"_REPO_ROOT / rel_path"}),
        ("tests/conftest.py", "pytest_runtest_setup"): frozenset({"DATA_ROOT / rel"}),
        ("tests/sparse_trees.py", "tree_absent"): frozenset({"REPO_ROOT / normalized"}),
    }
    assert expected == AUDITED_COMPUTED_REPO_PATHS


def test_every_audited_computed_path_matches_a_current_site(graph: _Graph) -> None:
    for path, _ in AUDITED_COMPUTED_REPO_PATHS:
        assert path in graph.modules
        graph.data(path)
    declared = {
        (key, expression) for key, expressions in AUDITED_COMPUTED_REPO_PATHS.items() for expression in expressions
    }
    assert graph.audited_sites == declared


def test_audited_function_cannot_add_another_computed_path() -> None:
    path = "tests/conftest.py"
    source = (
        "from pathlib import Path\n_REPO_ROOT = Path(__file__).parents[1]\n"
        "def _analyze_test_module(rel_path):\n"
        "    first = _REPO_ROOT / rel_path\n"
        "    second = _REPO_ROOT / rel_path\n"
        "    third = _REPO_ROOT / extra\n"
    )
    graph = _Graph({path}, read=lambda _: source)
    assert graph.data(path) == {
        f"<computed repo path: {path}:5 _REPO_ROOT / rel_path>",
        f"<computed repo path: {path}:6 _REPO_ROOT / extra>",
    }


def test_new_computed_path_in_area_test_still_disqualifies() -> None:
    test = "tests/test_area.py"
    source = (
        "from pathlib import Path\nROOT = Path(__file__).parents[1]\ndef test_read(name):\n    return ROOT / name\n"
    )
    graph = _Graph({test, "docs/elsewhere.json"}, read=lambda _: source)
    area = {"tests": [test], "roots": ["docs/inside/"]}
    assert any("ROOT / name" in item for item in _escapes(area, graph, test))


def test_shared_helper_caller_paths_are_checked() -> None:
    test = "tests/test_area.py"
    source = (
        "from tests.sparse_trees import tree_absent as absent\n"
        'absent("data/projects")\n'
        'pytest.mark.needs_artifact("group", "projects/open_model_data/item.json")\n'
        'pytest.mark.needs_artifact("group", "elsewhere/item.json")\n'
        "absent(dynamic_tree)\n"
        "import tests.sparse_trees\n"
        "tests.sparse_trees.tree_absent(dynamic_tree)\n"
        "also_absent = absent\n"
        "also_absent(dynamic_tree)\n"
        "artifact = pytest.mark.needs_artifact\n"
        "artifact('group', dynamic_rel)\n"
    )
    graph = _Graph({test}, read=lambda _: source)
    assert graph.caller_data(test) == {
        "data/projects/",
        "data/projects/open_model_data/item.json",
        "data/elsewhere/item.json",
        f"<computed caller path: {test}:5 absent(dynamic_tree)>",
        f"<computed caller path: {test}:7 tests.sparse_trees.tree_absent(dynamic_tree)>",
        f"<computed caller path: {test}:9 also_absent(dynamic_tree)>",
        f"<computed caller path: {test}:11 artifact('group', dynamic_rel)>",
    }


@pytest.mark.parametrize(
    "expression",
    [
        "ROOT / name",
        "REPO_ROOT.joinpath(name)",
        "os.path.join(ROOT, name)",
        "Path(__file__).parents[2] / name",
    ],
)
def test_computed_repo_root_forms_escape(expression: str) -> None:
    tracked = {"scripts/area/read.py", "docs/elsewhere.json"}
    source = f"import os\nfrom pathlib import Path\nROOT = Path(__file__).parents[2]\nREPO_ROOT = ROOT\nname = input()\nDATA = {expression}\n"
    graph = _Graph(tracked, read=lambda _: source)
    assert any(expression in item for item in graph.data("scripts/area/read.py"))


def test_static_string_constant_stays_in_area() -> None:
    tracked = {"scripts/area/read.py", "registry/lexicon/item.json", "docs/elsewhere.json"}
    source = (
        "from pathlib import Path\nROOT = Path(__file__).parents[2]\n"
        'NAME = "registry/lexicon/item.json"\nDATA = ROOT / NAME\n'
    )
    graph = _Graph(tracked, read=lambda _: source)
    assert graph.data("scripts/area/read.py") == {"registry/lexicon/item.json"}
    area = {"tests": [], "roots": ["scripts/area/", "registry/lexicon/"]}
    assert all(matches_root(item, area["roots"]) for item in graph.data("scripts/area/read.py"))


def test_shadowed_module_string_is_not_treated_as_constant() -> None:
    source = (
        'from pathlib import Path\nROOT = Path(__file__).parents[2]\nNAME = "registry/lexicon/item.json"\n'
        "def read(NAME):\n    return ROOT / NAME\n"
    )
    graph = _Graph({"scripts/area/read.py"}, read=lambda _: source)
    assert any("ROOT / NAME" in item for item in graph.data("scripts/area/read.py"))


def test_imports_sees_dynamic_and_relative_forms() -> None:
    source = '''
"""Docstring naming scripts.docs_only.module and scripts/docs_only.py."""
import importlib
from importlib import import_module
from . import sibling
from .pkg import thing
from .. import parent_mod
importlib.import_module("scripts.dyn.a")
import_module("scripts.dyn.b")
importlib.import_module(".rel", package="scripts.dyn")
__import__("scripts.dyn.c", fromlist=["d"])
pytest.importorskip("scripts.dyn.e")
runpy.run_module("scripts.dyn.f")
pytest_plugins = ("tests._plugin",)
CMD = ["python", "-m", "scripts.dyn.g", "--flag"]
INLINE = """
from scripts.dyn import inline_child
"""
TARGET = "scripts.dyn.h.attr"
importlib.import_module(name)
'''
    names, literals = _imports(source, "tests/sub/test_x.py")
    assert {
        "tests.sub",
        "tests.sub.sibling",
        "tests.sub.pkg",
        "tests.sub.pkg.thing",
        "tests",
        "tests.parent_mod",
        "scripts.dyn.a",
        "scripts.dyn.b",
        "scripts.dyn.rel",
        "scripts.dyn.c",
        "scripts.dyn.c.d",
        "scripts.dyn.e",
        "scripts.dyn.f",
        "tests._plugin",
        "scripts.dyn.inline_child",
    } <= names
    assert {"scripts.dyn.g", "scripts.dyn.h.attr"} <= literals
    assert not any("docs_only" in item for item in names | literals)
    assert "name" not in names


def test_graph_follows_dynamic_literals_transitively() -> None:
    tracked = {
        "tests/test_area.py",
        "scripts/__init__.py",
        "scripts/area/__init__.py",
        "scripts/area/core.py",
        "scripts/dyn/__init__.py",
        "scripts/dyn/loaded.py",
        "scripts/dyn/cli.py",
        "scripts/dyn/patched.py",
        "scripts/far/__init__.py",
        "scripts/far/deep.py",
        "scripts/unrelated.py",
    }
    sources = {
        "tests/test_area.py": (
            'import scripts.area.core\nsubprocess.run(["python", "-m", "scripts.dyn.cli"])\n'
            'mock.patch("scripts.dyn.patched.fn")\n'
        ),
        "scripts/area/core.py": 'def lazy():\n    importlib.import_module("scripts.dyn.loaded")\n',
        "scripts/dyn/loaded.py": "def f():\n    __import__('scripts.far.deep')\n",
    }
    graph = _Graph(tracked, read=lambda path: sources.get(path, ""))
    closure = graph.closure("tests/test_area.py")
    assert {
        "scripts/area/core.py",
        "scripts/dyn/loaded.py",
        "scripts/dyn/cli.py",
        "scripts/dyn/patched.py",
        "scripts/far/deep.py",
        "scripts/far/__init__.py",
    } <= closure
    assert "scripts/unrelated.py" not in closure
    area = {"tests": ["tests/test_area.py"], "roots": ["scripts/area/", "scripts/dyn/"]}
    assert _escapes(area, graph, "tests/test_area.py") == {"scripts/far/__init__.py", "scripts/far/deep.py"}
    assert _escapes({**area, "roots": [*area["roots"], "scripts/far/"]}, graph, "tests/test_area.py") == set()
