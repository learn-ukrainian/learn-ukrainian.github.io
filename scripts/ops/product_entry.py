"""Load a product module that product data names: the one configured entry point (#12504).

Machinery does not import product code by a literal name. A product data file
names the module, and the machinery code that read the file passes the name to
:func:`load_configured_module`. This is the only configured-entry-point import
site under ``scripts/`` (decision LOADER-1104). The SQLite boundary scan
(``scripts.hygiene.lint_source_db_writable_connects``) pins its one non-constant
``import_module`` call as the ``configured_entry_point`` kind. That scan, the
dependency scanner (``scripts.ci.components``) and the package boundary ratchet
(``scripts.lint.boundary_ratchet``) recognize calls to this function, plain,
aliased or qualified.

Contract of :func:`load_configured_module`:

* ``name`` is an absolute, lowercase, dotted ``scripts.*`` module name.
* A name with ``sqlite3`` or ``_sqlite3`` as a part is refused first, as
  ``scripts.lib.readonly_sqlite.import_named_module`` refuses it.
* ``product_root`` is the product checkout the module must come from. It
  defaults to :func:`scripts.common.repo_root.product_root`, resolved at each
  call (C-4746); a refusal there refuses the load, with no fallback to another
  checkout. A given root must be an absolute path to a directory that has a
  ``scripts/`` directory; it is checked before anything is imported.
* The product's ``scripts`` package is found in that root, not on ``sys.path``
  (C-4764): once the machinery runs from its own repository, the product
  checkout is not on the import path. A module is accepted when its file and
  every package search path resolve (symlinks followed) under the root's
  ``scripts/`` directory; a namespace package is accepted only as a package
  above the module, never as the module itself.
* First, every part of the name that is already cached is checked, each on its
  own, and then every uncached part that can be found without running product
  code. A refusal there runs no product code and changes no cache entry: a
  cached module from another checkout is refused and left cached, never evicted
  or rebound.
* Then the parts are imported one at a time, as an ordinary import imports
  them: a cached module is used as it is, and only the uncached parts at the
  end of the name run, from the one below the deepest cached part (or from the
  top-level package). Missing ancestors of a cached part are never run again.
  Each part is found before it runs: the top-level package by the file finder
  in the root, every other part by the import system in its parent's search
  path, which is checked
  again after the parent's own code has run. The found spec is checked, then
  the part is imported and checked once more. So no module outside the root
  runs because of this call, whatever a package's code did to its search path.
* A scoped, thread-aware :class:`importlib.abc.MetaPathFinder` guards the named
  module and its ancestors. Every resolution, including a retry after another
  thread's failed import, returns a root-checked spec or raises before execution.
  Guarded names never fall through to ambient resolution. Nested calls restore
  the outer scope; other threads and unrelated names retain ordinary resolution.
* Every part, including the top-level package, is imported with
  :func:`importlib.import_module`, which takes the per-module
  import lock, reuses ``sys.modules``, binds the module on its parent package,
  and removes a module whose import raised, ``BaseException`` included. No lock
  of this module's own is held while product code runs or an import lock is
  awaited, so a product module may call this function again from any thread.
* Standard-library, installed and machinery imports made by the product code
  are not confined: this is an origin check for the named product modules, not
  a sandbox for product code.
* Missing cached ancestors and a foreign checkout first on ``sys.path`` at entry
  are supported, including when an ordinary import already initializing the
  target later fails. Hostile mutation of ``sys.modules`` or ``sys.path`` by
  other code during this call is outside the contract. Ordinary import cache
  insertion and failed-import cleanup remain inside the contract.

A refusal raises :class:`ConfiguredModuleError`, an ``ImportError``. An import
that fails raises what the import raised; a part of the name that does not
exist raises ``ModuleNotFoundError`` naming it, after the parts before it are
imported, as an ordinary import does. Callers keep their own data-file
validation, error contracts and callable checks.

Example:
  .venv/bin/python -c "from scripts.ops.product_entry import load_configured_module as l; print(l('scripts.lib.readonly_sqlite'))"
"""

from __future__ import annotations

import importlib
import importlib.abc
import importlib.machinery
import re
import sys
import threading
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from importlib.machinery import ModuleSpec
from pathlib import Path
from types import ModuleType

from scripts.common import repo_root

_SQLITE_MODULES = frozenset({"sqlite3", "_sqlite3"})
_NAME_RE = re.compile(r"scripts(?:\.[a-z_][a-z0-9_]*)+")
_TOP = "scripts"
_FINDER_LOCK = threading.Lock()
# The file finder's loaders, in the order the import system's path hook uses them.
_LOADER_DETAILS = (
    (importlib.machinery.ExtensionFileLoader, importlib.machinery.EXTENSION_SUFFIXES),
    (importlib.machinery.SourceFileLoader, importlib.machinery.SOURCE_SUFFIXES),
    (importlib.machinery.SourcelessFileLoader, importlib.machinery.BYTECODE_SUFFIXES),
)


class ConfiguredModuleError(ImportError):
    """A configured module name, or the module it resolved to, was refused."""


def load_configured_module(name: str, *, product_root: Path | None = None) -> ModuleType:
    """Import the ``scripts.*`` module ``name`` from ``product_root``, or raise :class:`ConfiguredModuleError`."""
    if not isinstance(name, str):
        raise ConfiguredModuleError(f"configured module name is not a string: {name!r}")
    if _SQLITE_MODULES.intersection(re.split(r"[.:]", name)):
        raise ConfiguredModuleError(f"SQLite modules are not loaded through this boundary: {name}", name=name)
    if _NAME_RE.fullmatch(name) is None:
        raise ConfiguredModuleError(f"configured module name is not a lowercase scripts.* name: {name!r}", name=name)
    scripts_dir = _scripts_dir(name, product_root)
    parts = name.split(".")
    prefixes = [".".join(parts[:index]) for index in range(1, len(parts) + 1)]
    for prefix in prefixes:
        cached = sys.modules.get(prefix)
        if cached is not None:
            _check_module(name, prefix, cached, scripts_dir, is_leaf=prefix == name)
    # As an ordinary import: only the uncached parts at the end of the name run, starting below the
    # deepest cached one; a cached module is used as it is, never rebuilt from its missing ancestors.
    start = len(prefixes)
    while start > 0 and prefixes[start - 1] not in sys.modules:
        start -= 1
    _preflight(name, prefixes, start, scripts_dir)
    with _confined_imports(name, prefixes, scripts_dir):
        if start == len(prefixes):
            return _load_part(name, name, scripts_dir)
        for prefix in prefixes[start:]:
            module = _load_part(name, prefix, scripts_dir)
    return module


def _scripts_dir(name: str, product_root: Path | None) -> Path:
    if product_root is None:
        try:
            return repo_root.product_root().resolve() / "scripts"
        except repo_root.ProductRootError as exc:
            raise ConfiguredModuleError(f"no product checkout for {name}: {exc}", name=name) from None
    if not isinstance(product_root, Path) or not product_root.is_absolute():
        raise ConfiguredModuleError(f"product root is not an absolute path: {product_root!r}", name=name)
    scripts_dir = product_root.resolve() / "scripts"
    if not scripts_dir.is_dir():
        raise ConfiguredModuleError(f"product root has no scripts/ directory: {product_root}", name=name)
    return scripts_dir


def _preflight(name: str, prefixes: list[str], start: int, scripts_dir: Path) -> None:
    """Check every part from ``start`` on that can be found without running product code, before any runs.

    Found as the import system would find it: the top-level package in the root, each other part in
    the search path of the cached part before ``start`` or of the part found before it. The walk ends
    at the first part that does not exist; the import then raises ``ModuleNotFoundError`` for it, as
    an ordinary import does.
    """
    if start == 0:
        search = [str(scripts_dir.parent)]
    else:
        search = list(getattr(sys.modules.get(prefixes[start - 1]), "__path__", None) or [])
    for prefix in prefixes[start:]:
        spec = _find_spec(prefix, search)
        if spec is None:
            return
        _check_spec(name, prefix, spec, scripts_dir, is_leaf=prefix == name)
        search = list(spec.submodule_search_locations or [])


class _ProductScope:
    """The names and root guarded by one call."""

    def __init__(self, name: str, prefixes: list[str], scripts_dir: Path) -> None:
        self.name = name
        self.prefixes = frozenset(prefixes)
        self.scripts_dir = scripts_dir

    def find_spec(self, fullname: str, path: Iterable[str] | None) -> ModuleSpec:
        if fullname == _TOP:
            search = [str(self.scripts_dir.parent)]
        else:
            parent_name = fullname.rpartition(".")[0]
            parent = sys.modules.get(parent_name)
            if parent is None:
                raise ConfiguredModuleError(f"{parent_name} is not cached while {self.name} loads", name=self.name)
            _check_module(self.name, parent_name, parent, self.scripts_dir, is_leaf=False)
            search = list(path or [])
            _check_search_paths(self.name, parent_name, search, self.scripts_dir)
        spec = _find_spec(fullname, search)
        if spec is None:
            raise ModuleNotFoundError(f"No module named {fullname!r}", name=fullname)
        _check_spec(self.name, fullname, spec, self.scripts_dir, is_leaf=fullname == self.name)
        return spec


class _ThreadScopes(threading.local):
    def __init__(self) -> None:
        self.scopes: tuple[_ProductScope, ...] = ()


class _ProductFinder(importlib.abc.MetaPathFinder):
    """One stable registration while any thread has a scope; scopes themselves are thread-local."""

    def __init__(self) -> None:
        self.local = _ThreadScopes()
        self.users = 0

    def find_spec(self, fullname: str, path=None, target=None) -> ModuleSpec | None:
        for scope in reversed(self.local.scopes):
            if fullname in scope.prefixes:
                return scope.find_spec(fullname, path)
        return None


_PRODUCT_FINDER = _ProductFinder()


@contextmanager
def _confined_imports(name: str, prefixes: list[str], scripts_dir: Path) -> Iterator[None]:
    scope = _ProductScope(name, prefixes, scripts_dir)
    previous = _PRODUCT_FINDER.local.scopes
    with _FINDER_LOCK:
        if _PRODUCT_FINDER.users == 0:
            sys.meta_path.insert(0, _PRODUCT_FINDER)
        _PRODUCT_FINDER.users += 1
        _PRODUCT_FINDER.local.scopes = (*previous, scope)
    try:
        yield
    finally:
        with _FINDER_LOCK:
            _PRODUCT_FINDER.local.scopes = previous
            _PRODUCT_FINDER.users -= 1
            if _PRODUCT_FINDER.users == 0:
                sys.meta_path[:] = [registered for registered in sys.meta_path if registered is not _PRODUCT_FINDER]


def _load_part(name: str, prefix: str, scripts_dir: Path) -> ModuleType:
    """Import ``prefix`` from its parent's checked search path, checking it before and after it runs.

    A cached ``prefix`` is returned by the import as it is, without its parent, as an ordinary import
    returns it; it was checked before anything ran.
    """
    module = _import(prefix, scripts_dir)
    _check_module(name, prefix, module, scripts_dir, is_leaf=prefix == name)
    return module


def _import(name: str, scripts_dir: Path) -> ModuleType:
    """The ordinary import of one checked part of a configured name: this module's one import site."""
    return _in_this_checkout(name, importlib.import_module(name), scripts_dir)


def _find_spec(prefix: str, entries: list[str]) -> ModuleSpec | None:
    """The file-system spec the import system would find for ``prefix`` in ``entries``, without importing.

    As the path finder does: the first regular module or package wins; otherwise the namespace
    portions of every entry form one namespace package.
    """
    portions: list[str] = []
    for entry in entries:
        spec = importlib.machinery.FileFinder(entry, *_LOADER_DETAILS).find_spec(prefix)
        if spec is None:
            continue
        if spec.loader is not None:
            return spec
        portions.extend(spec.submodule_search_locations or [])
    if not portions:
        return None
    namespace = ModuleSpec(prefix, None, is_package=True)
    namespace.submodule_search_locations = portions
    return namespace


def _check_module(name: str, prefix: str, module: ModuleType, scripts_dir: Path, *, is_leaf: bool) -> None:
    origin = getattr(module, "__file__", None)
    if (origin is None and is_leaf) or (
        origin is not None and not (isinstance(origin, str) and _inside(origin, scripts_dir))
    ):
        raise ConfiguredModuleError(_not_here(prefix, origin, scripts_dir), name=name)
    _check_search_paths(name, prefix, getattr(module, "__path__", None) or [], scripts_dir)


def _check_spec(name: str, prefix: str, spec: ModuleSpec, scripts_dir: Path, *, is_leaf: bool) -> None:
    origin = spec.origin if spec.has_location else None
    if (origin is None and is_leaf) or (origin is not None and not _inside(origin, scripts_dir)):
        raise ConfiguredModuleError(_not_here(prefix, origin, scripts_dir), name=name)
    _check_search_paths(name, prefix, spec.submodule_search_locations or [], scripts_dir)


def _check_search_paths(name: str, prefix: str, paths: Iterable[str], scripts_dir: Path) -> None:
    for entry in paths:
        if not isinstance(entry, str) or not _inside(entry, scripts_dir):
            raise ConfiguredModuleError(
                f"{prefix} searches outside this checkout's scripts/ ({scripts_dir}): {entry!r}", name=name
            )


def _not_here(prefix: str, origin: object, scripts_dir: Path) -> str:
    return f"{prefix} is not a file in this checkout's scripts/ ({scripts_dir}): {origin!r}"


def _inside(path: str, scripts_dir: Path) -> bool:
    try:
        return Path(path).resolve().is_relative_to(scripts_dir)
    except (OSError, RuntimeError, ValueError):
        return False


def _in_this_checkout(name: str, module: ModuleType, scripts_dir: Path) -> ModuleType:
    _check_module(name, name, module, scripts_dir, is_leaf=False)
    return module
