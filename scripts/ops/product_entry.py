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
  call (C-4746); a refusal there refuses the load. A given root must be an
  absolute path to a directory that has a ``scripts/`` directory; it is checked
  before anything is imported.
* The module is imported with :func:`importlib.import_module`. It takes the
  per-module import lock, reuses ``sys.modules``, binds the module on its parent
  package, and removes a module whose import raised, ``BaseException`` included.
* The module must be a file under the product root's ``scripts/`` directory. A
  module cached from another checkout and a namespace package are refused.

A refusal raises :class:`ConfiguredModuleError`, an ``ImportError``. An import
that fails raises what the import raised. Callers keep their own data-file
validation, error contracts and callable checks.

Example:
  .venv/bin/python -c "from scripts.ops.product_entry import load_configured_module as l; print(l('scripts.lib.readonly_sqlite'))"
"""

from __future__ import annotations

import importlib
import re
from pathlib import Path
from types import ModuleType

from scripts.common import repo_root

_SQLITE_MODULES = frozenset({"sqlite3", "_sqlite3"})
_NAME_RE = re.compile(r"scripts(?:\.[a-z_][a-z0-9_]*)+")


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


def _in_this_checkout(name: str, module: ModuleType, scripts_dir: Path) -> ModuleType:
    origin = getattr(module, "__file__", None)
    if not isinstance(origin, str) or not Path(origin).resolve().is_relative_to(scripts_dir):
        raise ConfiguredModuleError(f"{name} is not a file in this checkout's scripts/: {origin!r}", name=name)
    return module
