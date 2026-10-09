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


_NULLABLE_TIMESTAMP: dict[str, Any] = {"anyOf": [{"type": "string", "pattern": TIMESTAMP_PATTERN}, {"type": "null"}]}
_CI_VALUE: dict[str, Any] = {"anyOf": [{"enum": ["green", "red", "pending"]}, {"type": "null"}]}
_MQ_VALUE: dict[str, Any] = {"anyOf": [{"enum": ["queued", "not_queued", "dropped"]}, {"type": "null"}]}
_LANE_VALUE: dict[str, Any] = {"type": ["string", "null"], "minLength": 1}
_HOURS_VALUE: dict[str, Any] = {"type": ["number", "null"], "minimum": 0}

_BLOCKER_NONE: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["kind"],
    "properties": {"kind": {"const": "none"}},
}
_BLOCKER_CF: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["kind"],
    "properties": {"kind": {"const": "cf_changes"}},
}
_BLOCKER_CONFLICT: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["kind"],
    "properties": {"kind": {"const": "conflict"}},
}
_BLOCKER_CHECKS: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["kind", "checks"],
    "properties": {
        "kind": {"const": "failing_check"},
        "checks": {"type": "array", "minItems": 1, "items": {"type": "string", "minLength": 1}},
    },
}
_BLOCKER_STACK: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["kind", "number", "state"],
    "properties": {
        "kind": {"const": "stacked_base"},
        "number": {"type": ["integer", "null"], "minimum": 1},
        "state": {"enum": ["open", "closed", "unmerged", "merged"]},
    },
}
_BLOCKER: dict[str, Any] = {
    "oneOf": [_BLOCKER_NONE, _BLOCKER_CF, _BLOCKER_CONFLICT, _BLOCKER_CHECKS, _BLOCKER_STACK]
}

_PR_ITEM: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "number",
        "repo",
        "title",
        "draft",
        "head_sha",
        "epics",
        "ci",
        "cf",
        "gate",
        "mq",
        "keeper",
        "flake_grant",
        "ready_since",
        "stale_green",
        "minutes",
        "stacked_base",
        "hours_idle",
        "blocker",
        "owner_lane",
        "idle_24h",
        "idle_48h",
    ],
    "properties": {
        "number": {"type": "integer", "minimum": 1},
        "repo": {"type": "string", "minLength": 1},
        "title": {"type": "string"},
        "draft": {"type": "boolean"},
        "head_sha": {"type": "string", "minLength": 1},
        "epics": {"type": "array", "items": {"type": "string", "minLength": 1}},
        "ci": _CI_VALUE,
        "cf": {
            "type": "object",
            "additionalProperties": False,
            "required": ["verdict", "at_head"],
            "properties": {
                "verdict": {"type": "string", "minLength": 1},
                "at_head": {"type": "boolean"},
            },
        },
        "gate": _CI_VALUE,
        "mq": _MQ_VALUE,
        "keeper": {
            "type": "object",
            "additionalProperties": False,
            "required": ["hold", "reason"],
            "properties": {
                "hold": {"type": ["boolean", "null"]},
                "reason": {"type": ["string", "null"]},
            },
        },
        "flake_grant": {
            "anyOf": [
                {"type": "null"},
                {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["decision", "used", "at"],
                    "properties": {
                        "decision": {"enum": ["grant", "deny"]},
                        "used": {"type": "boolean"},
                        "at": _NULLABLE_TIMESTAMP,
                    },
                },
            ]
        },
        "ready_since": _NULLABLE_TIMESTAMP,
        "stale_green": {"type": "boolean"},
        "minutes": {"type": ["integer", "null"], "minimum": 0},
        "hours_idle": _HOURS_VALUE,
        "blocker": _BLOCKER,
        "owner_lane": _LANE_VALUE,
        "idle_24h": {"type": "boolean"},
        "idle_48h": {"type": "boolean"},
        "stacked_base": {
            "anyOf": [
                {"type": "null"},
                {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["number", "ref", "state", "mq"],
                    "properties": {
                        "number": {"type": ["integer", "null"], "minimum": 1},
                        "ref": {"type": "string", "minLength": 1},
                        "state": {"anyOf": [{"const": "open"}, {"type": "null"}]},
                        "mq": _MQ_VALUE,
                    },
                },
            ]
        },
    },
}

_PRS_DATA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["prs"],
    "properties": {"prs": {"type": "array", "items": _PR_ITEM}},
}

_PR_DATA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["pr"],
    "properties": {"pr": {"anyOf": [_PR_ITEM, {"type": "null"}]}},
}

_ATTENTION_ITEM: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["number", "repo", "title", "owner_lane", "hours_idle", "idle_24h", "idle_48h", "blocker"],
    "properties": {
        "number": {"type": "integer", "minimum": 1},
        "repo": {"type": "string", "minLength": 1},
        "title": {"type": "string"},
        "owner_lane": _LANE_VALUE,
        "hours_idle": {"type": "number", "minimum": 24},
        "idle_24h": {"const": True},
        "idle_48h": {"type": "boolean"},
        "blocker": _BLOCKER,
    },
}

_NOW_DATA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["attention"],
    "properties": {"attention": {"type": "array", "items": _ATTENTION_ITEM}},
}

_DAY: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["date", "opened", "merged"],
    "properties": {
        "date": {"type": "string", "pattern": r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$"},
        "opened": {"type": "integer", "minimum": 0},
        "merged": {"type": "integer", "minimum": 0},
    },
}

_STATS_DATA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["window_days", "by_repo", "by_lane"],
    "properties": {
        "window_days": {"const": 14},
        "by_repo": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["repo", "backlog", "days"],
                "properties": {
                    "repo": {"type": "string", "minLength": 1},
                    "backlog": {"type": "integer", "minimum": 0},
                    "days": {"type": "array", "minItems": 14, "maxItems": 14, "items": _DAY},
                },
            },
        },
        "by_lane": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["owner_lane", "backlog", "days"],
                "properties": {
                    "owner_lane": _LANE_VALUE,
                    "backlog": {"type": "integer", "minimum": 0},
                    "days": {"type": "array", "minItems": 14, "maxItems": 14, "items": _DAY},
                },
            },
        },
    },
}


def endpoint_schema(schema_id: str) -> dict[str, Any]:
    """JSON Schema for one fleet board response, keyed by its ``schema`` value."""
    if schema_id == "fleet.v1.index":
        return _envelope_schema(schema_id, _INDEX_DATA)
    if schema_id == "fleet.v1.schema":
        return _envelope_schema(schema_id, _SCHEMA_DATA)
    if schema_id == "fleet.v1.prs":
        return _envelope_schema(schema_id, _PRS_DATA)
    if schema_id == "fleet.v1.pr":
        return _envelope_schema(schema_id, _PR_DATA)
    if schema_id == "fleet.v1.now":
        return _envelope_schema(schema_id, _NOW_DATA)
    if schema_id == "fleet.v1.stats":
        return _envelope_schema(schema_id, _STATS_DATA)
    return _envelope_schema(schema_id, {"type": "object"})
