"""Opaque diagnostic failure codes shared by read-only control-plane consumers."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from scripts.control_plane.storage import (
    Authority,
    ControlPlanePgDsnMissingError,
    ControlPlaneStoreUnavailableError,
    ControlPlaneUnsupportedComponentError,
    StoreId,
    resolve_authority,
)

# Postgres SQLSTATE for insufficient_privilege. A denial is not a dead probe.
_SQLSTATE_INSUFFICIENT_PRIVILEGE = "42501"
# Connect failures are re-raised, and the driver may wrap them again.
# The cap stops a cause/context cycle from walking forever.
_SQLSTATE_CHAIN_LIMIT = 8


def _exception_sqlstate(error: BaseException) -> str | None:
    """Return a five-character SQLSTATE from ``error`` itself, never its text."""
    code = getattr(error, "sqlstate", None)
    if isinstance(code, str) and len(code) == 5 and code.isalnum():
        return code
    return None


def _postgres_sqlstate(error: Exception) -> str | None:
    """Return the first SQLSTATE on ``error`` or its ``__cause__`` / ``__context__`` chain.

    Connection failures arrive wrapped, with the driver exception on
    ``__cause__``. The walk is bounded and remembers identities it has already
    visited, so a cycle returns instead of hanging. Only the code is returned.
    """
    pending: list[BaseException] = [error]
    seen: set[int] = set()
    index = 0
    inspected = 0
    while index < len(pending) and inspected < _SQLSTATE_CHAIN_LIMIT:
        current = pending[index]
        index += 1
        identity = id(current)
        if identity in seen:
            continue
        seen.add(identity)
        inspected += 1
        code = _exception_sqlstate(current)
        if code is not None:
            return code
        for linked in (current.__cause__, current.__context__):
            if isinstance(linked, BaseException) and id(linked) not in seen:
                pending.append(linked)
    return None


def read_failure_code(error: Exception, authority: Authority) -> str:
    """Classify a failed read without reflecting driver text or configuration.

    Codes: ``authority_unsupported_component``, ``pg_dsn_missing``,
    ``sqlite_database_missing``, ``pg_privilege_denied`` (SQLSTATE 42501),
    ``pg_probe_failed``, ``sqlite_probe_failed``.
    """
    if isinstance(error, ControlPlaneUnsupportedComponentError):
        return "authority_unsupported_component"
    if isinstance(error, ControlPlanePgDsnMissingError):
        return "pg_dsn_missing"
    if isinstance(error, ControlPlaneStoreUnavailableError):
        return "sqlite_database_missing"
    if _postgres_sqlstate(error) == _SQLSTATE_INSUFFICIENT_PRIVILEGE:
        return "pg_privilege_denied"
    return "pg_probe_failed" if authority is Authority.PG else "sqlite_probe_failed"


def authority_collector_payload(
    collector: Callable[..., dict[str, Any]],
    db_path: Path,
    *,
    empty_fields: dict[str, Any] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Project a PG-capable collector's actual result, never local-file PG health."""
    from scripts.fleet_comms.efficiency_metrics import EfficiencyMetricsReadError
    from scripts.fleet_comms.opsec_store import COMMS_RESPONSE_SCHEMA_VERSION

    authority = resolve_authority(StoreId.FLEET_COMMS)
    payload: dict[str, Any] = dict(empty_fields or {})
    store = {"kind": "comms-plane", "authority": authority.value, "reachable": False}
    if authority is not Authority.PG and not db_path.is_file():
        payload["db_missing"] = True
    else:
        try:
            payload = collector(db_path, **kwargs)
            store["reachable"] = True
        except EfficiencyMetricsReadError:
            payload["db_error"] = "schema_read_failed"
        except Exception as exc:
            payload["db_error"] = read_failure_code(exc, authority)
            if payload["db_error"] == "authority_unsupported_component":
                store["reachable"] = None
    payload.update(
        response_schema_version=COMMS_RESPONSE_SCHEMA_VERSION,
        content_included=False,
        read_only=True,
        source="authority",
        authority=authority.value,
        store=store,
    )
    return payload
