"""Control-plane storage resolver (Phase 0b — sqlite default, real pg adapter).

Private tracker #603 · stamped packet v3
``d29a13cedcdc50c6e97516b237155dad9f53116051aba29211b73bfb058c3bcc``

Sqlite remains the default live brain. This module is a small resolver —
not a dialect-neutral SQL switchboard. Callers that need durable control-plane
state open storage here instead of hard-coding ``sqlite3.connect`` against the
canonical paths. Authority ``pg`` opens a real Postgres connection via
psycopg 3; it never falls back to sqlite.

Stores (closed enum)
--------------------
``fleet_comms``, ``session_streams``, ``write_ownership``, ``task_index``

Per-store authority: ``sqlite`` (default) | ``shadow`` | ``pg``.

Environment
-----------
``LEARN_UKRAINIAN_CP_AUTHORITY``
    Global default authority (``sqlite`` unless overridden).

``LEARN_UKRAINIAN_CP_AUTHORITY_<STORE>``
    Per-store override where ``<STORE>`` is the uppercased enum name, e.g.
    ``LEARN_UKRAINIAN_CP_AUTHORITY_WRITE_OWNERSHIP``.

``LEARN_UKRAINIAN_CP_PG_DSN``
    Postgres DSN for stores with authority ``pg``. Never committed; fail closed
    when missing. No hostnames appear in raised errors — only the store id.

Existing path overrides (honored before connect):
``FLEET_COMMS_ROOT``, ``LEARN_UKRAINIAN_OWNERSHIP_LEDGER``.

Tests may redirect the primary checkout via ``LEARN_UK_REPO_ROOT`` (same as the
Monitor API) or the store-specific overrides above.
"""

from __future__ import annotations

import os
import sqlite3
from enum import StrEnum
from pathlib import Path
from typing import Any

from scripts.common.repo_root import resolve_repo_root

_MODULE_ROOT = resolve_repo_root(Path(__file__), 2)

_ENV_AUTHORITY = "LEARN_UKRAINIAN_CP_AUTHORITY"
_ENV_PG_DSN = "LEARN_UKRAINIAN_CP_PG_DSN"
_ENV_AUTHORITY_PREFIX = "LEARN_UKRAINIAN_CP_AUTHORITY_"
_PG_CONNECT_TIMEOUT_S = 3


class StoreId(StrEnum):
    FLEET_COMMS = "fleet_comms"
    SESSION_STREAMS = "session_streams"
    WRITE_OWNERSHIP = "write_ownership"
    TASK_INDEX = "task_index"


class Authority(StrEnum):
    SQLITE = "sqlite"
    SHADOW = "shadow"
    PG = "pg"


class ControlPlaneError(RuntimeError):
    """Base error for control-plane storage resolution."""


class ControlPlaneSqliteRefusedError(ControlPlaneError):
    """Raised when authority is ``pg`` and a sqlite open was requested."""


class ControlPlanePgDsnMissingError(ControlPlaneError):
    """Raised when authority is ``pg`` but no DSN is configured."""


class ControlPlaneStoreUnavailableError(ControlPlaneError):
    """Raised when a store has no sqlite backing in this slice."""


class ControlPlanePgConnectError(ControlPlaneError):
    """Raised when a Postgres connect fails (message carries store id only)."""


def _repo_root(repo_root: Path | None) -> Path:
    if repo_root is not None:
        return repo_root
    configured = (os.environ.get("LEARN_UK_REPO_ROOT") or "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return _MODULE_ROOT


def _parse_authority(raw: str) -> Authority:
    try:
        return Authority(raw.strip().lower())
    except ValueError as exc:
        raise ControlPlaneError(f"unknown control-plane authority: {raw!r}") from exc


def resolve_authority(store: StoreId) -> Authority:
    """Return the configured authority for ``store``."""
    per_store = (os.environ.get(f"{_ENV_AUTHORITY_PREFIX}{store.name}") or "").strip()
    if per_store:
        return _parse_authority(per_store)
    global_default = (os.environ.get(_ENV_AUTHORITY) or "").strip()
    if global_default:
        return _parse_authority(global_default)
    return Authority.SQLITE


def sqlite_path(store: StoreId, *, repo_root: Path | None = None) -> Path:
    """Resolve the canonical sqlite file for ``store`` without opening it."""
    root = _repo_root(repo_root)
    if store is StoreId.FLEET_COMMS:
        from scripts.fleet_comms.paths import default_plane_root

        plane_root = default_plane_root(
            repo_root=root,
            allow_non_git=repo_root is not None or bool(os.environ.get("LEARN_UK_REPO_ROOT")),
        )
        return plane_root / "comms.sqlite3"
    if store is StoreId.SESSION_STREAMS:
        from agents_extensions.shared.session_streams.db import default_database_path

        return default_database_path(root)
    if store is StoreId.WRITE_OWNERSHIP:
        override = (os.environ.get("LEARN_UKRAINIAN_OWNERSHIP_LEDGER") or "").strip()
        if override:
            return Path(override).expanduser().resolve()
        return root / "batch_state" / "tasks" / "write-ownership.sqlite3"
    if store is StoreId.TASK_INDEX:
        raise ControlPlaneStoreUnavailableError(
            "task_index has no sqlite backing in Phase 0; use a later slice"
        )
    raise ControlPlaneStoreUnavailableError(f"unknown store: {store}")


def _pg_dsn() -> str:
    return (os.environ.get(_ENV_PG_DSN) or "").strip()


def _connect_postgres(store: StoreId, *, read_only: bool) -> Any:
    """Open a real Postgres connection; never touch sqlite paths."""
    import psycopg

    dsn = _pg_dsn()
    if not dsn:
        raise ControlPlanePgDsnMissingError(
            f"control-plane store {store.value!r} requires {_ENV_PG_DSN}"
        )

    connect_kwargs: dict[str, Any] = {
        "connect_timeout": _PG_CONNECT_TIMEOUT_S,
    }
    if read_only:
        # Session-default read-only so autocommit and explicit txs honor it.
        connect_kwargs["options"] = "-c default_transaction_read_only=on"

    try:
        return psycopg.connect(dsn, **connect_kwargs)
    except Exception as exc:
        # OPSEC: never surface hostnames / userinfo from the DSN or libpq.
        raise ControlPlanePgConnectError(
            f"control-plane store {store.value!r} postgres connect failed"
        ) from exc


def connect(
    store: StoreId,
    *,
    path: Path | str | None = None,
    read_only: bool = False,
    repo_root: Path | None = None,
    **sqlite_kwargs: Any,
) -> sqlite3.Connection | Any:
    """Open the configured backend for ``store``.

    ``sqlite`` and ``shadow`` open the existing canonical sqlite files
    (``shadow`` remains a sqlite synonym in this slice).

    ``pg`` requires ``LEARN_UKRAINIAN_CP_PG_DSN`` and opens Postgres via
    psycopg 3. It never creates or opens a sqlite file for that store and
    never falls back to sqlite. A ``path`` argument is ignored under ``pg``
    (callers historically pass the sqlite location; it must not be touched).
    ``ControlPlaneSqliteRefusedError`` remains for explicit sqlite-under-pg
    refusals elsewhere; it is not the ``pg`` success path.
    """
    authority = resolve_authority(store)
    if authority is Authority.PG:
        # Never open or create the sqlite path — even when callers pass one.
        # path / sqlite_kwargs / repo_root apply only to sqlite|shadow.
        return _connect_postgres(store, read_only=read_only)

    if authority not in {Authority.SQLITE, Authority.SHADOW}:
        raise ControlPlaneError(f"unsupported authority for store {store.value!r}")

    db_path = (
        Path(path).expanduser().resolve()
        if path is not None
        else sqlite_path(store, repo_root=repo_root)
    )
    if read_only:
        if not db_path.is_file():
            raise ControlPlaneStoreUnavailableError(
                f"control-plane store {store.value!r} database does not exist"
            )
        uri = f"file:{db_path.resolve().as_posix()}?mode=ro"
        conn = sqlite3.connect(uri, uri=True, **sqlite_kwargs)
    else:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path), **sqlite_kwargs)
    return conn
