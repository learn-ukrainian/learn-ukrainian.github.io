"""JSON envelope shared by every fleet board response."""

from __future__ import annotations

import re
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from .sources import SourceReport

TIMESTAMP_PATTERN = r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
_SCHEMA_NAME = re.compile(r"^[a-z0-9_]+$")

_SOURCE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["name", "status", "age_s", "error"],
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "status": {"enum": ["ok", "stale", "unavailable", "not_configured"]},
        "age_s": {"type": ["number", "null"], "minimum": 0},
        "error": {"type": ["string", "null"]},
    },
    "allOf": [
        {
            "if": {"properties": {"status": {"const": "not_configured"}}, "required": ["status"]},
            "then": {"properties": {"age_s": {"type": "null"}, "error": {"type": "null"}}},
        },
        {
            "if": {"properties": {"status": {"const": "unavailable"}}, "required": ["status"]},
            "then": {"properties": {"age_s": {"type": "null"}, "error": {"const": "unavailable"}}},
        },
        {
            "if": {"properties": {"status": {"enum": ["ok", "stale"]}}, "required": ["status"]},
            "then": {"properties": {"error": {"type": "null"}}},
        },
    ],
}

_INDEX_DATA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["endpoints"],
    "properties": {
        "endpoints": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["method", "path", "schema"],
                "properties": {
                    "method": {"enum": ["GET", "POST", "PUT", "PATCH", "DELETE"]},
                    "path": {"type": "string", "minLength": 1},
                    "schema": {"type": "string", "pattern": r"^fleet\.v1\.[a-z0-9_]+$"},
                },
            },
        }
    },
}

_SCHEMA_DATA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["endpoints"],
    "properties": {
        "endpoints": {
            "type": "object",
            "required": ["fleet.v1.index", "fleet.v1.schema"],
            "additionalProperties": {"type": "object"},
            "properties": {
                "fleet.v1.index": {"type": "object"},
                "fleet.v1.schema": {"type": "object"},
            },
        }
    },
}

_NULL_S: dict[str, Any] = {"type": ["string", "null"]}
_NULL_N: dict[str, Any] = {"type": ["number", "null"]}


def _obj(required: list[str], properties: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": required,
        "properties": properties,
    }


_ALERT = _obj(
    ["name", "severity", "summary", "starts_at", "state"],
    {"name": _NULL_S, "severity": _NULL_S, "summary": _NULL_S, "starts_at": _NULL_S, "state": _NULL_S},
)
_STAT = _obj(
    ["name", "value", "status"],
    {
        "name": {"enum": ["disk_pct", "memory_pct", "drivers_live", "probe_status"]},
        "value": _NULL_N,
        "status": {"enum": ["ok", "unavailable"]},
    },
)
_LINK = _obj(
    ["name", "href"],
    {"name": {"enum": ["overview", "fleet"]}, "href": {"type": "string", "minLength": 1}},
)

_DATA_SCHEMAS: dict[str, dict[str, Any]] = {
    "fleet.v1.alerts": _obj(["alerts"], {"alerts": {"type": "array", "items": _ALERT}}),
    "fleet.v1.stats": _obj(
        ["stats"],
        {
            "stats": {
                "type": "array",
                "minItems": 4,
                "maxItems": 4,
                "items": _STAT,
            }
        },
    ),
    "fleet.v1.links": _obj(["links"], {"links": {"type": "array", "items": _LINK}}),
}


def utc_timestamp(moment: datetime | None = None) -> str:
    """UTC timestamp with a ``Z`` suffix and whole seconds."""
    current = moment or datetime.now(UTC)
    current = current.replace(tzinfo=UTC) if current.tzinfo is None else current.astimezone(UTC)
    return current.strftime("%Y-%m-%dT%H:%M:%SZ")


def envelope(
    name: str,
    data: Any,
    sources: Sequence[SourceReport],
    *,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    """Build the shared response object. ``name`` is the schema suffix."""
    suffix = name if _SCHEMA_NAME.fullmatch(name) else "unknown"
    return {
        "schema": f"fleet.v1.{suffix}",
        "generated_at": utc_timestamp(generated_at),
        "sources": [item.as_dict() for item in sources],
        "data": data,
    }


def _envelope_schema(schema_id: str, data_schema: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["schema", "generated_at", "sources", "data"],
        "properties": {
            "schema": {"const": schema_id},
            "generated_at": {"type": "string", "pattern": TIMESTAMP_PATTERN},
            "sources": {"type": "array", "items": _SOURCE_SCHEMA},
            "data": data_schema,
        },
    }


def endpoint_schema(schema_id: str) -> dict[str, Any]:
    """JSON Schema for one fleet board response, keyed by its ``schema`` value."""
    if schema_id == "fleet.v1.index":
        return _envelope_schema(schema_id, _INDEX_DATA)
    if schema_id == "fleet.v1.schema":
        return _envelope_schema(schema_id, _SCHEMA_DATA)
    return _envelope_schema(schema_id, _DATA_SCHEMAS.get(schema_id, {"type": "object"}))
