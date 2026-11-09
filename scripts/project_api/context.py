"""Product roots and stores the curriculum half of the Monitor attaches to a MonitorContext.

The machinery :class:`~scripts.api.monitor_context.MonitorContext` owns
generic roots and fleet stores. The textbook image store, the textbook and
image roots and the sources database belong to product routes, so they are
built here, lazily, on the context's runtime holder. A resource created
through ``runtime.get_or_create_resource`` is closed with the context when
the app shuts down (Monitor split, C-4687).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from lu_machinery.api.monitor_context import DatabaseHandle, MonitorContext, resolve_context
from lu_machinery.api.resilience import connect_sqlite
from lu_machinery.storage.topology import (
    StoreBinding,
    StoreRefusal,
    resolve_active_sources_db,
    resolve_store,
    unavailable_store_path,
)

if TYPE_CHECKING:
    from .images_router import ImageStore

_ROOTS_KEY = "project_api.roots"
_SOURCES_DB_KEY = "project_api.sources_db"
_IMAGE_STORE_KEY = "project_api.image_store"


@dataclass(frozen=True)
class ProductRoots:
    """Filesystem roots of the product routes for one context."""

    images_dir: Path
    textbooks_dir: Path
    sources_db_path: Path


def _sources_store_path(project_root: Path, path: Path | None = None, *, required: bool = False) -> Path:
    """Resolve the sources store at use time; a refusal never names a local store."""
    binding = None if path is None else StoreBinding("sources", Path(path))
    result = resolve_store("sources", project_root, binding=binding)
    if isinstance(result, StoreRefusal):
        if required:
            raise FileNotFoundError(result.reason) from None
        return unavailable_store_path("sources")
    return result.path


def _default_roots(ctx: MonitorContext) -> ProductRoots:
    project_root = ctx.roots.project_root
    if ctx.root is not None:
        return ProductRoots(
            images_dir=project_root / "data" / "textbook_images",
            textbooks_dir=project_root / "data" / "textbooks",
            sources_db_path=resolve_active_sources_db(project_root, env={}).path,
        )
    from . import config  # noqa: PLC0415 — TEXTBOOKS_DIR resolves through the product wrapper on first use

    return ProductRoots(
        images_dir=project_root / "data" / "textbook_images",
        textbooks_dir=Path(config.TEXTBOOKS_DIR),
        sources_db_path=_sources_store_path(project_root),
    )


def product_roots(ctx: MonitorContext | None = None) -> ProductRoots:
    """The product roots of ``ctx``, computed once per context."""
    resolved = resolve_context(ctx)
    return cast(ProductRoots, resolved.runtime.get_or_create_derived(_ROOTS_KEY, lambda: _default_roots(resolved)))


def with_product_roots(ctx: MonitorContext, **overrides: Any) -> MonitorContext:
    """Return a fresh context with the same machinery roots and the given product roots.

    The new context gets a new runtime, so no store built against the old
    product roots carries over.
    """
    fresh = ctx.with_roots()
    roots = replace(product_roots(ctx), **overrides)
    fresh.runtime.get_or_create_derived(_ROOTS_KEY, lambda: roots)
    return fresh


def _open_sources_db(ctx: MonitorContext, database: Path, *, read_only: bool = True) -> Any:
    path = _sources_store_path(ctx.roots.project_root, ctx.resolve_db_path(database), required=True)
    return connect_sqlite(path.as_uri() + "?mode=ro", uri=True)


def sources_db(ctx: MonitorContext | None = None) -> DatabaseHandle:
    """Read-only handle to the sources database of ``ctx``."""
    resolved = resolve_context(ctx)
    return cast(
        DatabaseHandle,
        resolved.runtime.get_or_create_derived(
            _SOURCES_DB_KEY,
            lambda: DatabaseHandle(
                product_roots(resolved).sources_db_path,
                lambda database, read_only=True: _open_sources_db(resolved, database, read_only=read_only),
            ),
        ),
    )


def image_store(ctx: MonitorContext | None = None) -> ImageStore:
    """The textbook image store of ``ctx``, created once and closed with the context."""
    from .images_router import ImageStore  # noqa: PLC0415 — images_router imports this module

    resolved = resolve_context(ctx)
    roots = product_roots(resolved)

    def build() -> ImageStore:
        return ImageStore(
            images_dir=roots.images_dir,
            textbooks_dir=roots.textbooks_dir,
            annotations_file=roots.images_dir / "image_text_pairs.jsonl",
            project_root=resolved.roots.project_root,
        )

    return cast("ImageStore", resolved.runtime.get_or_create_resource(_IMAGE_STORE_KEY, build))
