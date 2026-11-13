"""The product contribution the Monitor API composes, and the one loader that builds it.

The Monitor app is machinery. Its product half (curriculum routers, product
pages, orient sections, lifecycle hooks and the projections fleet views need)
lives in a product package that machinery never imports by name. A product
data file under the configured product root names the entry module; the
entry's ``build_api(context)`` returns a :class:`ProductContribution`
(Monitor split, C-4687)::

    product = load_product(context)
    app = create_app(context, product=product)

``load_product`` reads ``scripts/curriculum/monitor_paths.v1.json`` under
``config.PRODUCT_ROOT``, takes its ``product_api`` module name and imports it
through :func:`scripts.ops.product_entry.load_configured_module`, which
checks the name and that the module comes from that product root.

Two providers are process-wide because their machinery callers run outside a
request (occupancy and fleet-worker collectors): :func:`install_providers`
records the Atlas provider and the fleet batch projection of the most recent
product an app was built with. A process that builds no app (launchers and
observers resolving their host id) still gets the Atlas registry adapter that
product data names, ``scripts/lexicon/monitor_jobs.v1.json``, without the
host-load cache that only the product routes keep.
"""

from __future__ import annotations

import functools
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Protocol

from fastapi import APIRouter

from scripts.ops.product_entry import ConfiguredModuleError, load_configured_module

from . import config

if TYPE_CHECKING:
    from .monitor_context import MonitorContext
    from .route_contracts import PageContract, RouteContract

PRODUCT_DATA = Path("scripts") / "curriculum" / "monitor_paths.v1.json"
ATLAS_REGISTRY_DATA = Path("scripts") / "lexicon" / "monitor_jobs.v1.json"
PRODUCT_DATA_SCHEMA = "learn-ukrainian.monitor-paths"
_PRODUCT_DATA_MAX_BYTES = 64 * 1024


class ProductEntryError(RuntimeError):
    """The configured product entry is missing, malformed or returned the wrong shape."""


@dataclass(frozen=True)
class RouterMount:
    """One product router and the prefix and tags it is included with."""

    router: APIRouter
    prefix: str = ""
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class OrientSection:
    """One product section of ``GET /api/orient``.

    ``after`` names the section it follows in the response, so the composed
    order is the same as before the split. ``merge_meta`` copies the section
    value into its ``meta`` entry, as the governance section does.
    """

    collector: Callable[..., Any]
    fallback: Any
    is_async: bool
    ttl_s: float
    source: str
    after: str
    lean: bool = False
    merge_meta: bool = False


class AtlasProvider(Protocol):
    """Atlas job registry and host-load cache, as fleet occupancy and worker views read them."""

    def canonical_host(self, host: str | None) -> str: ...
    def is_self_host(self, host: str) -> bool: ...
    def list_registry(self) -> list[dict[str, Any]]: ...
    def collect_host_load(self, *, run_root: Path) -> dict[str, Any]: ...
    def host_load_entry(self, canonical: str, *, fresh: bool) -> dict[str, Any]: ...
    async def host_load_entry_async(self, canonical: str, *, fresh: bool) -> dict[str, Any]: ...


ContextHook = Callable[["MonitorContext"], Any]
FleetBatches = Callable[["MonitorContext | None"], dict[str, Any]]


@dataclass(frozen=True)
class ProductContribution:
    """Everything the product adds to one Monitor app.

    ``routers`` are included ahead of the machinery routers. ``static_files``
    maps each declared page or asset URL path (``"index.html"``,
    ``"data/status.json"``) to its file; nothing else under the product root is
    served. ``route_contracts`` and ``page_contracts`` join the machinery
    registry at ``/api/contracts/routes``. ``preload`` and
    ``preload_optional`` join the machinery startup preload. ``warmup`` hooks
    run in the machinery state-scan warmup thread after the routing-budget
    warm. Product resources created through ``ctx.runtime`` close with the
    context. ``orient_sections`` is called per request, so a collector
    replaced on its module is the one that runs. ``health`` adds fields to the
    orient health section.
    """

    routers: tuple[RouterMount, ...] = ()
    static_files: Mapping[str, Path] = field(default_factory=lambda: MappingProxyType({}))
    route_contracts: tuple[RouteContract, ...] = ()
    page_contracts: tuple[PageContract, ...] = ()
    preload: tuple[str, ...] = ()
    preload_optional: tuple[str, ...] = ()
    warmup: tuple[ContextHook, ...] = ()
    orient_sections: Callable[[], Mapping[str, OrientSection]] = field(default=lambda: MappingProxyType({}))
    health: Callable[[MonitorContext], Mapping[str, Any]] | None = None
    atlas: AtlasProvider | None = None
    fleet_batches: FleetBatches | None = None


EMPTY = ProductContribution()


def _unique_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    document: dict[str, Any] = {}
    for key, value in pairs:
        if key in document:
            raise ValueError(f"duplicate key {key!r}")
        document[key] = value
    return document


def product_module_name(product_root: Path) -> str:
    """The ``product_api`` module named by the product data file under ``product_root``."""
    path = product_root / PRODUCT_DATA
    if path.is_symlink() or not path.is_file():
        raise ProductEntryError(f"{PRODUCT_DATA}: not a regular file under the product root")
    raw = path.read_bytes()
    if len(raw) > _PRODUCT_DATA_MAX_BYTES:
        raise ProductEntryError(f"{PRODUCT_DATA}: larger than {_PRODUCT_DATA_MAX_BYTES} bytes")
    try:
        document = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_keys)
    except (UnicodeDecodeError, ValueError, RecursionError) as exc:
        raise ProductEntryError(f"{PRODUCT_DATA}: unreadable: {exc}") from exc
    if not isinstance(document, dict) or document.get("schema") != PRODUCT_DATA_SCHEMA:
        raise ProductEntryError(f"{PRODUCT_DATA}: expected schema {PRODUCT_DATA_SCHEMA}")
    version = document.get("schema_version")
    if type(version) is not int or version != 1:
        raise ProductEntryError(f"{PRODUCT_DATA}: expected schema_version 1")
    name = document.get("product_api")
    if not isinstance(name, str):
        raise ProductEntryError(f"{PRODUCT_DATA}: product_api must name a module")
    return name


def load_product(context: MonitorContext, *, product_root: Path | None = None) -> ProductContribution:
    """Import the configured product entry and return its contribution for ``context``."""
    root = config.PRODUCT_ROOT if product_root is None else product_root
    name = product_module_name(root)
    try:
        entry = load_configured_module(name, product_root=root)
    except ConfiguredModuleError as exc:
        raise ProductEntryError(f"product entry refused: {exc}") from exc
    build_api = getattr(entry, "build_api", None)
    if not callable(build_api):
        raise ProductEntryError(f"{name} has no callable build_api(context)")
    product = build_api(context)
    if not isinstance(product, ProductContribution):
        raise ProductEntryError(f"{name}.build_api returned {type(product).__name__}, not ProductContribution")
    return product


def product_file(product: ProductContribution | None, name: str) -> Path | None:
    """The declared product file for URL path ``name``, or ``None``.

    An extension-less name also matches its ``.html`` page, as the static
    catch-all always allowed. Only declared names match, so a traversal string
    never reaches the filesystem; the declared file must still be a regular
    file inside the product root once symlinks are resolved.
    """
    if product is None:
        return None
    path = product.static_files.get(name)
    if path is None and name and not Path(name).suffix:
        path = product.static_files.get(f"{name}.html")
    if path is None:
        return None
    resolved = path.resolve()
    if not resolved.is_file() or not resolved.is_relative_to(config.PRODUCT_ROOT.resolve()):
        return None
    return resolved


_atlas: AtlasProvider | None = None
_fleet_batches: FleetBatches | None = None
_product: ProductContribution = EMPTY


def install_providers(product: ProductContribution) -> None:
    """Record the process-wide providers of ``product`` for collectors outside a request."""
    global _atlas, _fleet_batches, _product
    _atlas = product.atlas
    _fleet_batches = product.fleet_batches
    _product = product


def installed_product() -> ProductContribution:
    """The product contribution an app was most recently built with, or :data:`EMPTY`."""
    return _product


class _RegistryOnlyAtlas:
    """The Atlas registry adapter alone, for a process that built no Monitor app."""

    def __init__(self, jobs: Any) -> None:
        self._jobs = jobs

    def canonical_host(self, host: str | None) -> str:
        return str(self._jobs._canonical_host(host))

    def is_self_host(self, host: str) -> bool:
        return bool(self._jobs.is_self_host(host))

    def list_registry(self) -> list[dict[str, Any]]:
        return list(self._jobs.list_registry())

    def collect_host_load(self, *, run_root: Path) -> dict[str, Any]:
        return dict(self._jobs.collect_host_load(run_root=run_root))

    def host_load_entry(self, canonical: str, *, fresh: bool) -> dict[str, Any]:
        raise LookupError("the Atlas host-load cache belongs to the product routes")

    async def host_load_entry_async(self, canonical: str, *, fresh: bool) -> dict[str, Any]:
        raise LookupError("the Atlas host-load cache belongs to the product routes")


@functools.cache
def _registry_only_atlas() -> AtlasProvider | None:
    path = config.PRODUCT_ROOT / ATLAS_REGISTRY_DATA
    try:
        name = json.loads(path.read_text(encoding="utf-8"))["module"]
        jobs = load_configured_module(name, product_root=config.PRODUCT_ROOT)
    except (OSError, ValueError, KeyError, TypeError, ImportError):
        return None
    return _RegistryOnlyAtlas(jobs)


def atlas_provider() -> AtlasProvider | None:
    """The Atlas provider an app installed, else the registry-only adapter, else ``None``."""
    if _atlas is not None:
        return _atlas
    return _registry_only_atlas()


def fleet_batches() -> FleetBatches | None:
    """The installed fleet batch projection, or ``None`` when no product supplies one."""
    return _fleet_batches
