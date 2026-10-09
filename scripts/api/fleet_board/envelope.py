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


_NULLABLE_NUMBER: dict[str, Any] = {"type": ["number", "null"]}
_NULLABLE_STRING: dict[str, Any] = {"type": ["string", "null"]}
_TIMESTAMP_OR_NULL: dict[str, Any] = {
    "anyOf": [
        {"type": "string", "pattern": TIMESTAMP_PATTERN},
        {"type": "null"},
    ]
}

_FLAG: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["name", "value", "source", "checked_at"],
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "value": {"enum": [True, False, "unknown"]},
        "source": _NULLABLE_STRING,
        "checked_at": _TIMESTAMP_OR_NULL,
    },
}

_EPIC: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["epic", "depends_on", "restart_condition", "state", "flags"],
    "properties": {
        "epic": {"type": "string", "minLength": 1},
        "depends_on": {"type": "array", "items": {"type": "string", "minLength": 1}},
        "restart_condition": _NULLABLE_STRING,
        "state": {
            "anyOf": [
                {"enum": ["working", "idle", "stuck", "dead", "paused", "off"]},
                {"type": "null"},
            ]
        },
        "flags": {"type": "array", "items": _FLAG},
    },
}

_LAYER: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["layer", "kind", "epics"],
    "properties": {
        "layer": {"enum": [0, 1, None]},
        "kind": {"enum": ["foundations", "consumers", "postponed"]},
        "epics": {"type": "array", "items": _EPIC},
    },
}

_ROSTER_DATA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["layers", "foundation_status", "active_alerts"],
    "properties": {
        "layers": {"type": "array", "minItems": 3, "maxItems": 3, "items": _LAYER},
        "foundation_status": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["foundation", "red", "reasons"],
                "properties": {
                    "foundation": {"type": "string", "minLength": 1},
                    "red": {"type": ["boolean", "null"]},
                    "reasons": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "active_alerts": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["name", "summary"],
                "properties": {
                    "name": {"type": "string", "minLength": 1},
                    "summary": _NULLABLE_STRING,
                },
            },
        },
    },
}

_BUDGET_DATA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["subscriptions"],
    "properties": {
        "subscriptions": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["subscription", "used_pct", "elapsed_pct", "pace", "reset_at", "recommendation"],
                "properties": {
                    "subscription": {"type": "string", "minLength": 1},
                    "used_pct": _NULLABLE_NUMBER,
                    "elapsed_pct": _NULLABLE_NUMBER,
                    "pace": _NULLABLE_STRING,
                    "reset_at": _TIMESTAMP_OR_NULL,
                    "recommendation": _NULLABLE_STRING,
                },
            },
        }
    },
}


def endpoint_schema(schema_id: str) -> dict[str, Any]:
    """JSON Schema for one fleet board response, keyed by its ``schema`` value."""
    if schema_id == "fleet.v1.index":
        return _envelope_schema(schema_id, _INDEX_DATA)
    if schema_id == "fleet.v1.schema":
        return _envelope_schema(schema_id, _SCHEMA_DATA)
    if schema_id == "fleet.v1.roster":
        return _envelope_schema(schema_id, _ROSTER_DATA)
    if schema_id == "fleet.v1.budget":
        return _envelope_schema(schema_id, _BUDGET_DATA)
    return _envelope_schema(schema_id, {"type": "object"})
