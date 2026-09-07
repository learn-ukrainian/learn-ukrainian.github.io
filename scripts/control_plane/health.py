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


def read_failure_code(error: Exception, authority: Authority) -> str:
    """Classify a failed read without reflecting driver text or configuration."""
    if isinstance(error, ControlPlaneUnsupportedComponentError):
        return "authority_unsupported_component"
    if isinstance(error, ControlPlanePgDsnMissingError):
        return "pg_dsn_missing"
    if isinstance(error, ControlPlaneStoreUnavailableError):
        return "sqlite_database_missing"
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
