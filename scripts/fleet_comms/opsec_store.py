"""OPSEC-safe store descriptors for fleet-comms Monitor surfaces (#7182)."""

from __future__ import annotations

from typing import Any

COMMS_RESPONSE_SCHEMA_VERSION = "comms.v2"


def store_descriptor(
    *,
    kind: str,
    reachable: bool,
    schema_versions: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return an opaque store label without filesystem paths."""
    payload: dict[str, Any] = {"kind": kind, "reachable": reachable}
    if schema_versions is not None:
        payload["schema_versions"] = schema_versions
    return payload
