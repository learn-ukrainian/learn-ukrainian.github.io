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
it; the repo root and top-level trees are anchors, not reads. Paths that force
the full tier (``hits_shared_root_denylist``) need no root, but their imports
and data are followed.

Completeness: a test that imports an area package and whose reach fits the
roots must be listed in the area; tests whose reach does not fit stay out and
always run.
"""

from __future__ import annotations

import ast
import importlib.metadata
import posixpath
import subprocess
import sys
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

import pytest

from scripts.ci.classify_changes import hits_shared_root_denylist
from scripts.ci.test_areas import load_areas, matches_root, matches_test

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


def _imports(source: str, path: str) -> tuple[set[str], set[str]]:
    """Module names (exact) and loose string literals (resolved leniently) in one file."""
    names: set[str] = set()
    literals: set[str] = set()
    docstrings: set[int] = set()
    joined: set[int] = set()
    # ast.walk is breadth-first, so a docstring's owner is seen before it.
    for node in ast.walk(ast.parse(source, filename=path)):
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


class _Graph:
    """Repo-file import graph over tracked Python files."""

    def __init__(self, tracked: set[str], read: Callable[[str], str] | None = None) -> None:
        self.modules = {path for path in tracked if path.endswith(".py")}
        self.files = tracked
        self.dirs: dict[str, set[str]] = defaultdict(set)
        for path in tracked:
            for parent in list(PurePosixPath(path).parents)[:-1]:
                self.dirs[str(parent)].add(path)
        self.read = read or (lambda path: (_REPO / path).read_text(encoding="utf-8"))
        self._refs: dict[str, tuple[set[str], set[str]]] = {}
        self._edges: dict[str, frozenset[str]] = {}
        self._trees: dict[str, ast.Module] = {}
        self._consts: dict[str, dict[str, str]] = {}
        self._data: dict[str, frozenset[str]] = {}
        self.by_top: dict[str, set[str]] = defaultdict(set)
        for path in self.modules:
            pure = PurePosixPath(path)
            if pure.name == "__init__.py":
                self.by_top[pure.parent.name].add(str(pure.parent.parent))
            else:
                self.by_top[pure.stem].add(str(pure.parent))
        self.external = set(sys.stdlib_module_names) | set(importlib.metadata.packages_distributions())

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

    def resolve(self, name: str, importer: str) -> set[str]:
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
            right = _str_value(node.right)
            return None if right is None else _join(self._anchor(node.left, scope), [right])
        if not isinstance(node, ast.Call):
            return None
        name = _call_name(node)
        method = isinstance(node.func, ast.Attribute)
        if method and name in {"resolve", "absolute", "expanduser"} and not node.args:
            return self._anchor(node.func.value, scope)
        strings = [_str_value(arg) for arg in node.args]
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
        if name in {"Path", "PurePath", "PurePosixPath"} and node.args and None not in strings[1:]:
            if (first := strings[0]) is not None:
                # A relative string counts only where it names a tracked path.
                return None if first.startswith("/") else _join("", [first, *strings[1:]])
            return _join(self._anchor(node.args[0], scope), strings[1:])
        return None

    def _scope(self, path: str) -> _Scope:
        """Module-local path names (assignments) and imported names/modules."""
        scope = _Scope({"__file__": path}, {})
        nodes = list(ast.walk(self._tree(path)))
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

    def consts(self, path: str) -> dict[str, str]:
        """Names ``path`` binds to static repo paths (``REGISTRY_ROOT = ROOT / "registry"``)."""
        if path not in self._consts:
            self._consts[path] = {}  # an import cycle sees no names, not a loop
            self._consts[path] = {name: value for name, value in self._scope(path).names.items() if name != "__file__"}
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
        scope = self._scope(path)
        inner: set[int] = set()
        # ast.walk is breadth-first: an outer path expression precedes its parts.
        for node in ast.walk(self._tree(path)):
            if id(node) in inner or not isinstance(node, (ast.BinOp, ast.Call)):
                continue
            # The longest static prefix: ``DIR / f"{x}.json"`` names DIR.
            current: ast.AST = node
            while (value := self._anchor(current, scope)) is None and (
                isinstance(current, ast.BinOp) and isinstance(current.op, ast.Div)
            ):
                current = current.left
            if value is None:
                continue
            found |= self._named(value, anchors=True)
            while isinstance(current, ast.BinOp):
                inner.add(id(current.left))
                current = current.left
        self._data[path] = frozenset(found)
        return self._data[path]

    def refs(self, path: str) -> tuple[set[str], set[str]]:
        if path not in self._refs:
            self._refs[path] = _imports(self.read(path), path)
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
    def outside(module: str) -> bool:
        return not (
            hits_shared_root_denylist(module)
            or matches_root(module, area["roots"])
            or matches_test(module, area["tests"])
        )

    reached = graph.closure(test, outside if first else None)
    found = {module for module in reached if outside(module)}
    # Data named by the test or by any module it reaches (a constant such as
    # ``DEFAULT_VERDICTS = REGISTRY_ROOT / "lexicon/x.yaml"`` is a read).
    return found | {item for module in (test, *reached) for item in graph.data(module) if outside(item)}


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


@pytest.fixture(scope="module")
def graph() -> _Graph:
    return _Graph(_tracked())


def test_every_area_is_closed_and_complete(graph: _Graph) -> None:
    areas = load_areas()
    assert set(areas) == set(_AREA_MODULES)
    for name, area in areas.items():
        missing_tests, missing_roots = _violations(name, area, graph)
        assert missing_roots == [], name
        assert missing_tests == [], name


def test_incomplete_area_is_rejected(graph: _Graph) -> None:
    area = load_areas()["open_model_data"]
    omitted_test = "tests/test_open_model_corpus_admission.py"
    omitted_root = "scripts/storage/paths.py"
    assert omitted_test in graph.modules and omitted_root in graph.modules
    fewer_tests = {**area, "tests": [pattern for pattern in area["tests"] if pattern != omitted_test]}
    assert omitted_test in _violations("open_model_data", fewer_tests, graph)[0]
    fewer_roots = {**area, "roots": [root for root in area["roots"] if root != "scripts/storage/"]}
    assert any(item.endswith(" -> " + omitted_root) for item in _violations("open_model_data", fewer_roots, graph)[1])
    atlas = load_areas()["atlas"]
    no_decks = {**atlas, "roots": [root for root in atlas["roots"] if root != "registry/practice/"]}
    missing = _violations("atlas", no_decks, graph)[1]
    assert "tests/test_noun_mechanics_engine.py -> registry/practice/noun_mechanics_deck.json" in missing
    # Data read only through an imported module's constant (review-8872-atlas).
    no_lexicon = {**atlas, "roots": [root for root in atlas["roots"] if root != "registry/lexicon/"]}
    missing = _violations("atlas", no_lexicon, graph)[1]
    assert "tests/test_atlas_db.py -> registry/lexicon/synonym_pair_verdicts.yaml" in missing


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
            "def deck(name):\n"
            '    return REGISTRY_ROOT / "decks" / f"{name}.json"\n'
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
