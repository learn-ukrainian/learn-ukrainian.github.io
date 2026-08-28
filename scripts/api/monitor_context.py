"""Application-scoped roots and store handles for the Monitor API."""

from __future__ import annotations

import os
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path
from types import MappingProxyType
from typing import Any

from fastapi import Request

from agents_extensions.shared.session_streams.db import (
    SessionStreamDatabase,
    default_database_path,
)
from agents_extensions.shared.session_streams.store import SessionStreamStore

from . import config
from .docs_router import EFFECTIVE_ROOTS
from .observer_presence import _STORE as _PRESENCE_STORE
from .project_state_store import _STORE as _REPORT_STORE
from .resilience import connect_sqlite


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
    sources_db_path: Path | None = None
    message_db_path: Path | None = None
    session_streams_db_path: Path | None = None
    epics_db_path: Path | None = None

    def __getitem__(self, name: str) -> Path | Mapping[str, Path] | None:
        return getattr(self, name)


@dataclass(frozen=True)
class DatabaseHandle:
    """A validated database target whose connection is opened on demand."""

    path: Path
    _opener: Callable[..., Any] = field(repr=False, compare=False)

    def connect(self, *, read_only: bool = False) -> Any:
        """Open the database through its owning context."""
        return self._opener(self.path, read_only=read_only)

    open = connect


@dataclass(frozen=True)
class MonitorStores:
    """Store handles owned by one Monitor application context."""

    sources_db: DatabaseHandle | None = None
    message_db: DatabaseHandle | None = None
    presence_store: dict[Any, Any] | None = None
    report_store: dict[Any, Any] | None = None
    session_streams_database: SessionStreamDatabase | None = None
    session_streams_store: SessionStreamStore | None = None
    epics_database: SessionStreamDatabase | None = None
    epics_store: SessionStreamStore | None = None

    def __getitem__(self, name: str) -> Any:
        return getattr(self, name)

    def items(self) -> Iterator[tuple[str, Any]]:
        for name in self.__dataclass_fields__:
            yield name, getattr(self, name)


@dataclass(frozen=True)
class MonitorContext:
    """Immutable roots plus the store handles for one Monitor app instance."""

    roots: MonitorRoots
    stores: MonitorStores
    root: Path | None = field(default=None, repr=False, compare=False)

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


def _effective_roots(project_root: Path) -> Mapping[str, Path]:
    project_root_resolved = project_root.resolve()
    remapped: dict[str, Path] = {}
    for name, path in EFFECTIVE_ROOTS.items():
        candidate = Path(path)
        try:
            relative = candidate.resolve().relative_to(project_root_resolved)
        except ValueError:
            relative = Path(name)
        remapped[name] = project_root / relative
    return _frozen_mapping(remapped)


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
    epics_database = context._open_db(roots.epics_db_path, session_streams=True)

    if fixture:
        presence_store: dict[Any, Any] = {}
        report_store: dict[Any, Any] = {}
    else:
        presence_store = _PRESENCE_STORE
        report_store = _REPORT_STORE

    return MonitorStores(
        sources_db=DatabaseHandle(roots.sources_db_path, context._open_db),
        message_db=DatabaseHandle(roots.message_db_path, context._open_db),
        presence_store=presence_store,
        report_store=report_store,
        session_streams_database=session_database,
        session_streams_store=SessionStreamStore(session_database),
        epics_database=epics_database,
        epics_store=SessionStreamStore(epics_database),
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


def production_context() -> MonitorContext:
    """Build a context from the current production configuration resolution."""
    project_root = Path(config.PROJECT_ROOT)
    live_repo_root = Path(config.LIVE_REPO_ROOT)
    return _build_context(
        project_root=project_root,
        live_repo_root=live_repo_root,
        dashboards_dir=Path(config.DASHBOARDS_DIR),
        batch_state_dir=Path(config.BATCH_STATE_DIR),
        curriculum_root=Path(config.CURRICULUM_ROOT),
        message_db_path=Path(config.MESSAGE_DB),
        session_streams_db_path=default_database_path(live_repo_root),
        backup_dir=Path(
            os.environ.get("BACKUP_DIR", str(project_root / "data" / "backups"))
        ),
        fixture=False,
    )


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
    "MonitorStores",
    "fixture_context",
    "get_ctx",
    "production_context",
]
