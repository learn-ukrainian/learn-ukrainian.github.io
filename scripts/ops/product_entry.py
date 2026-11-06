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
  checkout is not on the import path. Before any product code runs, every
  package and module of the name, cached or not, is checked against the root:
  its file and every package search path must resolve (symlinks followed) under
  the root's ``scripts/`` directory. A cached module from another checkout is
  refused and left cached (never evicted or rebound), and so is a namespace
  package as the module itself.
* An uncached top-level package is executed from its checked spec and cached;
  the rest is imported with :func:`importlib.import_module`, which takes the
  per-module import lock, reuses ``sys.modules``, binds the module on its parent
  package, and removes a module whose import raised, ``BaseException``
  included. The loaded modules are checked again afterwards.
* Standard-library, installed and machinery imports made by the product code
  are not confined: this is an origin check for the named product modules, not
  a sandbox for product code.

A refusal raises :class:`ConfiguredModuleError`, an ``ImportError``. An import
that fails raises what the import raised; a package of the name that does not
exist raises ``ModuleNotFoundError``. Callers keep their own data-file
validation, error contracts and callable checks.

Example:
  .venv/bin/python -c "from scripts.ops.product_entry import load_configured_module as l; print(l('scripts.lib.readonly_sqlite'))"
"""

from __future__ import annotations

import importlib
import importlib.machinery
import importlib.util
import re
import sys
import threading
from collections.abc import Iterable
from importlib.machinery import ModuleSpec
from pathlib import Path
from types import ModuleType

from scripts.common import repo_root

_SQLITE_MODULES = frozenset({"sqlite3", "_sqlite3"})
_NAME_RE = re.compile(r"scripts(?:\.[a-z_][a-z0-9_]*)+")
# Serializes this loader's own top-level package loads, which the import system's
# per-module locks do not cover (the package is executed from its spec here).
_LOAD_LOCK = threading.RLock()
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
    with _LOAD_LOCK:
        _confine(name, scripts_dir)
        _recheck(name, scripts_dir)
        return _in_this_checkout(name, importlib.import_module(name), scripts_dir)


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


def _confine(name: str, scripts_dir: Path) -> None:
    """Check every package and module of ``name`` against the root before any product code runs.

    Cached entries are checked as they are. Uncached ones are found from the root (the top-level
    package) or from their parent's checked search paths, without importing them, and their specs
    are checked. Then an uncached top-level package is executed from its checked spec, so the final
    import resolves every submodule through checked search paths.
    """
    parts = name.split(".")
    top_spec: ModuleSpec | None = None
    search: list[str] | None = None
    for index in range(1, len(parts) + 1):
        prefix = ".".join(parts[:index])
        is_leaf = index == len(parts)
        cached = sys.modules.get(prefix)
        if cached is not None:
            _check_cached(name, prefix, cached, scripts_dir, is_leaf=is_leaf)
            search = list(getattr(cached, "__path__", None) or [])
            continue
        spec = _find_spec(prefix, [str(scripts_dir.parent)] if index == 1 else search or [])
        if spec is None:
            raise ModuleNotFoundError(f"No module named {prefix!r}", name=prefix)
        _check_spec(name, prefix, spec, scripts_dir, is_leaf=is_leaf)
        if index == 1:
            top_spec = spec
        search = list(spec.submodule_search_locations or [])
    if top_spec is not None:
        _load_top_level(top_spec)


def _find_spec(prefix: str, entries: list[str]) -> ModuleSpec | None:
    """The file-system spec the import system would find for ``prefix`` in ``entries``, without importing.

    As the path finder does: the first regular module or package wins; otherwise the namespace
    portions of every entry form one namespace package. Built from the public file finder, because
    the path finder needs the parent package imported before it can describe a namespace portion.
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


def _check_cached(name: str, prefix: str, module: ModuleType, scripts_dir: Path, *, is_leaf: bool) -> None:
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


def _load_top_level(spec: ModuleSpec) -> None:
    """Execute and cache the checked top-level package; a failed execution leaves nothing cached."""
    if spec.loader is None:
        raise ConfiguredModuleError(f"{spec.name} has no loader", name=spec.name)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(spec.name, None)
        raise


def _recheck(name: str, scripts_dir: Path) -> None:
    """Every cached package of ``name`` still comes from the root (the top level just loaded included)."""
    parts = name.split(".")
    for index in range(1, len(parts)):
        prefix = ".".join(parts[:index])
        cached = sys.modules.get(prefix)
        if cached is not None:
            _check_cached(name, prefix, cached, scripts_dir, is_leaf=False)


def _in_this_checkout(name: str, module: ModuleType, scripts_dir: Path) -> ModuleType:
    _recheck(name, scripts_dir)
    origin = getattr(module, "__file__", None)
    if not isinstance(origin, str) or not Path(origin).resolve().is_relative_to(scripts_dir):
        raise ConfiguredModuleError(_not_here(name, origin, scripts_dir), name=name)
    return module
