"""Application-scoped roots and store handles for the Monitor API."""

from __future__ import annotations

import concurrent.futures
import inspect
import os
import threading
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

from fastapi import Request

from agents_extensions.shared.session_streams.db import (
    SessionStreamDatabase,
    default_database_path,
)
from agents_extensions.shared.session_streams.store import SessionStreamStore

from . import config
from .resilience import connect_sqlite

if TYPE_CHECKING:
    from .images_router import ImageStore
    from .observer_presence import ObserverPresence
    from .project_state_store import StoredReport

# Production singleton for work-router single-flight handles. Fixture contexts
# get a fresh dict; production_context() reuses this object so existing tests
# that inspect ``work_router._IN_FLIGHT_BUILDS`` keep seeing the live slot map.
_WORK_IN_FLIGHT_BUILDS: dict[Any, Any] = {}


def _as_path(value: os.PathLike[str] | str) -> Path:
    return Path(value).expanduser()


def _frozen_mapping(values: Mapping[str, Path]) -> Mapping[str, Path]:
    return MappingProxyType({key: Path(value) for key, value in values.items()})


@dataclass(frozen=True)
class MonitorRoots:
    """Filesystem roots used by Monitor routes and their store handles."""

    project_root: Path
    live_repo_root: Path
    dashboards_dir: Path
    batch_state_dir: Path
    curriculum_root: Path
    plans_root: Path
    backup_dir: Path
    logs_dir: Path
    queue_dir: Path
    pid_dir: Path
    effective_roots: Mapping[str, Path] = field(default_factory=dict)
    images_dir: Path | None = None
    textbooks_dir: Path | None = None
    sources_db_path: Path = Path()
    message_db_path: Path = Path()
    session_streams_db_path: Path = Path()
    epics_db_path: Path = Path()

    def __post_init__(self) -> None:
        if not isinstance(self.effective_roots, MappingProxyType):
            object.__setattr__(
                self,
                "effective_roots",
                _frozen_mapping(self.effective_roots),
            )


@dataclass(frozen=True)
class DatabaseHandle:
    """Read-only or read-write handle to a SQLite database."""

    path: Path
    _opener: Callable[..., Any] = field(repr=False, compare=False)

    def connect(self, *, read_only: bool = False) -> Any:
        return self._opener(self.path, read_only=read_only)


@dataclass(frozen=True)
class MonitorStores:
    """Store handles owned by one Monitor application context."""

    sources_db: DatabaseHandle | None = None
    message_db: DatabaseHandle | None = None
    presence_store: dict[tuple[str, str, str], ObserverPresence] | None = None
    report_store: dict[str, StoredReport] | None = None
    session_streams_database: SessionStreamDatabase | None = None
    session_streams_store: SessionStreamStore | None = None
    epics_database: SessionStreamDatabase | None = None
    epics_store: SessionStreamStore | None = None
    image_store: ImageStore | None = None
    work_in_flight: dict[str, concurrent.futures.Future[dict[str, Any]]] | None = None


@dataclass
class MonitorRuntime:
    """Mutable lifetime state owned by one :class:`MonitorContext`.

    ``MonitorContext`` itself remains frozen so roots and store wiring cannot
    drift after app construction.  This small runtime holder is the safe home
    for lazy, immutable snapshots and for work/resources that must be drained
    when the app exits.
    """

    _derived: dict[str, Any] = field(default_factory=dict, repr=False)
    _resources: list[Any] = field(default_factory=list, repr=False)
    _background_work: set[Any] = field(default_factory=set, repr=False)
    _lock: threading.RLock = field(default_factory=threading.RLock, repr=False)

    def get_or_create_derived(self, key: str, factory: Callable[[], Any]) -> Any:
        """Return one context-scoped derived snapshot for ``key``."""
        with self._lock:
            if key not in self._derived:
                self._derived[key] = factory()
            return self._derived[key]

    def get_or_create_resource(
        self,
        key: str,
        factory: Callable[[], Any],
    ) -> Any:
        """Return one lazily-created context resource and retain its owner."""
        with self._lock:
            if key in self._derived:
                return self._derived[key]
            resource = factory()
            self._derived[key] = resource
            if resource not in self._resources:
                self._resources.append(resource)
            return resource

    def register_resource(self, resource: Any) -> Any:
        """Register an eagerly-created resource exactly once."""
        with self._lock:
            if resource not in self._resources:
                self._resources.append(resource)
        return resource

    def register_background_work(self, work: Any) -> Any:
        """Track a future-like context task until it settles."""
        with self._lock:
            self._background_work.add(work)

        add_done_callback = getattr(work, "add_done_callback", None)
        if callable(add_done_callback):
            add_done_callback(self._forget_background_work)
        return work

    def _forget_background_work(self, work: Any) -> None:
        with self._lock:
            self._background_work.discard(work)

    def background_work(self) -> tuple[Any, ...]:
        """Return a stable snapshot of not-yet-drained context work."""
        with self._lock:
            return tuple(self._background_work)

    def resources(self) -> tuple[Any, ...]:
        """Return resources retained by this context."""
        with self._lock:
            return tuple(self._resources)

    async def close_resources(self, *extra: Any) -> None:
        """Close retained resources and any explicitly supplied replacements."""
        resources: list[Any] = []
        seen: set[int] = set()
        for resource in (*self.resources(), *extra):
            if resource is None or id(resource) in seen:
                continue
            seen.add(id(resource))
            resources.append(resource)

        for resource in resources:
            close = getattr(resource, "close", None)
            if not callable(close):
                continue
            result = close()
            if inspect.isawaitable(result):
                await result


@dataclass(frozen=True)
class MonitorContext:
    """Immutable roots plus the store handles for one Monitor app instance."""

    roots: MonitorRoots
    stores: MonitorStores
    root: Path | None = field(default=None, repr=False, compare=False)
    runtime: MonitorRuntime = field(default_factory=MonitorRuntime, repr=False, compare=False)

    def with_roots(self, **overrides: Any) -> MonitorContext:
        """Return a new context with ``roots`` overridden and stores rebuilt against it.

        ``replace(self, roots=replace(self.roots, **overrides))`` looks
        equivalent but is not: it leaves ``stores`` bound to the *old*
        roots (e.g. ``stores.message_db`` still points at the pre-override
        path). This mirrors ``_build_context``'s two-step build instead —
        an interim context with the overridden roots, empty stores, and a
        fresh runtime, then stores rebuilt against that interim context so
        handles bind to the final roots.
        """
        new_roots = replace(self.roots, **overrides)
        interim = MonitorContext(roots=new_roots, stores=MonitorStores(), root=self.root)
        return replace(interim, stores=_stores(interim, fixture=self.root is not None))

    def _resolve_db_path(self, database: os.PathLike[str] | str) -> Path:
        """Resolve a database target and enforce a fixture root, if present."""
        resolved = _as_path(database).resolve()
        if self.root is not None:
            fixture_root = self.root.resolve()
            if not resolved.is_relative_to(fixture_root):
                raise ValueError("database path escapes the fixture context root")
        return resolved

    def _open_db(
        self,
        database: os.PathLike[str] | str,
        *,
        read_only: bool = False,
        session_streams: bool = False,
    ) -> Any:
        """Open one database through the context's single guarded choke point."""
        path = self._resolve_db_path(database)
        if session_streams:
            return SessionStreamDatabase(path)
        if read_only:
            return connect_sqlite(f"file:{path}?mode=ro", uri=True)
        return connect_sqlite(str(path))


def get_ctx(request: Request) -> MonitorContext:
    """Return the context attached to the app serving the current request."""
    return request.app.state.ctx


def resolve_context(ctx: MonitorContext | None = None) -> MonitorContext:
    """Return ``ctx`` when provided; otherwise the live production context.

    #7496 / #7494: NEVER reads the module-global ``app``. Request paths use
    ``Depends(get_ctx)``. Plain-Python callers that omit ``ctx`` get
    ``production_context()``. Internal helpers that own roots or stores must
    take an explicit ``MonitorContext`` — do not add helpers that consult a
    global app, and do not reintroduce per-module copies of this function.
    """
    if isinstance(ctx, MonitorContext):
        return ctx
    return production_context()


def _effective_roots(project_root: Path) -> Mapping[str, Path]:
    from .docs_router import (  # noqa: PLC0415  # lazy-ok: avoid circular import between monitor_context and docs_router
        build_effective_roots,
    )

    return _frozen_mapping(build_effective_roots(project_root))


def _roots(
    *,
    project_root: Path,
    live_repo_root: Path,
    dashboards_dir: Path,
    batch_state_dir: Path,
    curriculum_root: Path,
    message_db_path: Path,
    session_streams_db_path: Path,
    backup_dir: Path,
) -> MonitorRoots:
    image_dir = project_root / "data" / "textbook_images"
    return MonitorRoots(
        project_root=project_root,
        live_repo_root=live_repo_root,
        dashboards_dir=dashboards_dir,
        batch_state_dir=batch_state_dir,
        curriculum_root=curriculum_root,
        plans_root=curriculum_root / "plans",
        backup_dir=backup_dir,
        logs_dir=project_root / "logs",
        queue_dir=project_root / "agents_extensions" / "shared" / "consultation-queue",
        pid_dir=project_root / ".mcp" / "servers" / "message-broker" / "pids",
        effective_roots=_effective_roots(project_root),
        images_dir=image_dir,
        textbooks_dir=project_root / "data" / "textbooks",
        sources_db_path=project_root / "data" / "sources.db",
        message_db_path=message_db_path,
        session_streams_db_path=session_streams_db_path,
        epics_db_path=session_streams_db_path,
    )


def _stores(context: MonitorContext, *, fixture: bool) -> MonitorStores:
    roots = context.roots
    session_database = context._open_db(roots.session_streams_db_path, session_streams=True)

    if fixture:
        presence_store: dict[Any, Any] = {}
        report_store: dict[Any, Any] = {}
        work_in_flight: dict[Any, Any] = {}
    else:
        # Lazy imports avoid a cycle: monitor_context ↔ observer_presence /
        # project_state_store (those modules Depends(get_ctx) on us).
        from .observer_presence import (  # noqa: PLC0415  # lazy-ok: break monitor_context ↔ observer_presence cycle
            _STORE as _PRESENCE_STORE,
        )
        from .project_state_store import (  # noqa: PLC0415  # lazy-ok: break monitor_context ↔ project_state_store cycle
            _STORE as _REPORT_STORE,
        )

        presence_store = _PRESENCE_STORE
        report_store = _REPORT_STORE
        work_in_flight = _WORK_IN_FLIGHT_BUILDS

    from .images_router import (  # noqa: PLC0415  # lazy-ok: avoid circular import between monitor_context and images_router
        ImageStore,
    )

    images_dir = roots.images_dir or (roots.project_root / "data" / "textbook_images")
    textbooks_dir = roots.textbooks_dir or (roots.project_root / "data" / "textbooks")
    annotations_file = images_dir / "image_text_pairs.jsonl"
    session_store = SessionStreamStore(session_database)
    image_store = ImageStore(
        images_dir=images_dir,
        textbooks_dir=textbooks_dir,
        annotations_file=annotations_file,
        project_root=roots.project_root,
    )
    context.runtime.register_resource(image_store)

    return MonitorStores(
        sources_db=DatabaseHandle(roots.sources_db_path, context._open_db),
        message_db=DatabaseHandle(roots.message_db_path, context._open_db),
        presence_store=presence_store,
        report_store=report_store,
        session_streams_database=session_database,
        session_streams_store=session_store,
        # Migration note: migrate legacy standalone epics.db data into this DB before startup.
        # Epics and session streams intentionally share one database handle and
        # store: both are projections over the same context-owned file.
        epics_database=session_database,
        epics_store=session_store,
        image_store=image_store,
        work_in_flight=work_in_flight,
    )


def _build_context(
    *,
    project_root: Path,
    live_repo_root: Path,
    dashboards_dir: Path,
    batch_state_dir: Path,
    curriculum_root: Path,
    message_db_path: Path,
    session_streams_db_path: Path,
    backup_dir: Path,
    fixture: bool,
) -> MonitorContext:
    root = project_root.resolve() if fixture else None
    roots = _roots(
        project_root=project_root,
        live_repo_root=live_repo_root,
        dashboards_dir=dashboards_dir,
        batch_state_dir=batch_state_dir,
        curriculum_root=curriculum_root,
        message_db_path=message_db_path,
        session_streams_db_path=session_streams_db_path,
        backup_dir=backup_dir,
    )
    context = MonitorContext(roots=roots, stores=MonitorStores(), root=root)
    return replace(context, stores=_stores(context, fixture=fixture))


@lru_cache(maxsize=1)
def _cached_production_context(
    project_root: Path,
    live_repo_root: Path,
    dashboards_dir: Path,
    batch_state_dir: Path,
    curriculum_root: Path,
    message_db_path: Path,
    session_streams_db_path: Path,
    backup_dir: Path,
) -> MonitorContext:
    return _build_context(
        project_root=project_root,
        live_repo_root=live_repo_root,
        dashboards_dir=dashboards_dir,
        batch_state_dir=batch_state_dir,
        curriculum_root=curriculum_root,
        message_db_path=message_db_path,
        session_streams_db_path=session_streams_db_path,
        backup_dir=backup_dir,
        fixture=False,
    )


def production_context() -> MonitorContext:
    """Build a cached context keyed by the current production configuration."""
    project_root = Path(config.PROJECT_ROOT)
    live_repo_root = Path(config.LIVE_REPO_ROOT)
    return _cached_production_context(
        project_root,
        live_repo_root,
        Path(config.DASHBOARDS_DIR),
        Path(config.BATCH_STATE_DIR),
        Path(config.CURRICULUM_ROOT),
        Path(config.MESSAGE_DB),
        default_database_path(live_repo_root),
        Path(os.environ.get("BACKUP_DIR", str(project_root / "data" / "backups"))),
    )


# Preserve the cache lifecycle hook used by tests and operational callers while
# keeping configuration resolution outside the cached zero-argument wrapper.
production_context.cache_clear = _cached_production_context.cache_clear  # type: ignore[attr-defined]


def fixture_context(root: os.PathLike[str] | str) -> MonitorContext:
    """Build a context whose roots and stores are entirely under ``root``."""
    fixture_root = _as_path(root).resolve()
    return _build_context(
        project_root=fixture_root,
        live_repo_root=fixture_root,
        dashboards_dir=fixture_root / "dashboards",
        batch_state_dir=fixture_root / "batch_state",
        curriculum_root=fixture_root / "curriculum" / "l2-uk-en",
        message_db_path=fixture_root / ".mcp" / "servers" / "message-broker" / "messages.db",
        session_streams_db_path=fixture_root / ".agent" / "session-streams" / "v1" / "session-streams.sqlite3",
        backup_dir=fixture_root / "data" / "backups",
        fixture=True,
    )


__all__ = [
    "DatabaseHandle",
    "MonitorContext",
    "MonitorRoots",
    "MonitorRuntime",
    "MonitorStores",
    "fixture_context",
    "get_ctx",
    "production_context",
    "resolve_context",
]
