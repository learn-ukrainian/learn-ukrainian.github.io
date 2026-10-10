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

_NULL_STRING = {"type": ["string", "null"]}
_NULL_BOOL = {"type": ["boolean", "null"]}
_NULL_INT = {"type": ["integer", "null"], "minimum": 0}

_STATE = {"enum": ["working", "idle", "stuck", "dead", "paused", "off"]}

_TASK: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["kind", "number", "title"],
    "properties": {
        "kind": {"enum": ["issue", "pr", "none"]},
        "number": {"type": ["integer", "null"], "minimum": 1},
        "title": _NULL_STRING,
    },
}

_DRIVER: dict[str, Any] = {
    "type": ["object", "null"],
    "additionalProperties": False,
    "required": ["agent_id", "cli", "model", "harness", "pid_alive"],
    "properties": {
        "agent_id": {"type": "string", "minLength": 1},
        "cli": _NULL_STRING,
        "model": _NULL_STRING,
        "harness": _NULL_STRING,
        "pid_alive": _NULL_BOOL,
    },
}

_WORKER: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["agent_id", "cli", "model", "task", "state", "state_reason", "since"],
    "properties": {
        "agent_id": {"type": "string", "minLength": 1},
        "cli": _NULL_STRING,
        "model": _NULL_STRING,
        "task": _NULL_STRING,
        "state": _STATE,
        "state_reason": {"type": "string", "minLength": 1},
        "since": _NULL_STRING,
    },
}

_HEALTH: dict[str, Any] = {
    "type": "object", "additionalProperties": False,
    "required": ["agent_id", "status", "measured_at", "context_pct", "compactions", "stop_count", "ask_count", "idle_min"],
    "properties": {
        "agent_id": {"type": ["string", "null"]},
        "status": {"enum": ["ok", "stale", "unknown"]},
        "measured_at": {"type": ["string", "null"], "pattern": TIMESTAMP_PATTERN},
        **{key: {"type": ["number", "null"], "minimum": 0}
           for key in ("context_pct", "compactions", "stop_count", "ask_count", "idle_min")},
    },
}

_NOW_EPIC: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "epic",
        "title",
        "focus",
        "parent",
        "layer",
        "intended",
        "state",
        "state_reason",
        "since",
        "driver",
        "task",
        "workers",
        "health",
    ],
    "properties": {
        "epic": {"type": "string", "minLength": 1},
        "title": _NULL_STRING,
        "focus": _NULL_STRING,
        "parent": _NULL_STRING,
        "layer": _NULL_INT,
        "intended": _NULL_STRING,
        "state": _STATE,
        "state_reason": {"type": "string", "minLength": 1},
        "since": _NULL_STRING,
        "driver": _DRIVER,
        "task": _TASK,
        "workers": {"type": "array", "items": _WORKER},
        "health": _HEALTH,
    },
}

_AGENT: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "agent_id",
        "role",
        "epic",
        "cli",
        "model",
        "task",
        "state",
        "state_reason",
        "last_seen",
    ],
    "properties": {
        "agent_id": {"type": "string", "minLength": 1},
        "role": {"enum": ["driver", "worker", "bot"]},
        "epic": _NULL_STRING,
        "cli": _NULL_STRING,
        "model": _NULL_STRING,
        "task": _NULL_STRING,
        "state": _STATE,
        "state_reason": {"type": "string", "minLength": 1},
        "last_seen": _NULL_STRING,
    },
}

_ATTENTION: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["severity", "kind", "title", "summary", "target"],
    "properties": {
        "severity": {"enum": ["bad", "warn"]},
        "kind": {
            "enum": [
                "dead_driver",
                "stuck_driver",
                "red_foundation",
                "unqueued_pr",
                "alert",
                "usage",
            ]
        },
        "title": {"type": "string", "minLength": 1},
        "summary": {"type": "string", "minLength": 1},
        "target": {
            "type": "object",
            "additionalProperties": False,
            "required": ["type", "id"],
            "properties": {
                "type": {"enum": ["epic", "foundation", "pr", "alert", "usage"]},
                "id": {"type": "string", "minLength": 1},
            },
        },
    },
}

_NOW_DATA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["attention", "epics"],
    "properties": {
        "attention": {"type": "array", "items": _ATTENTION},
        "epics": {"type": "array", "items": _NOW_EPIC},
    },
}

_EPICS_DATA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["epics"],
    "properties": {"epics": {"type": "array", "items": _NOW_EPIC}},
}

_AGENTS_DATA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["agents"],
    "properties": {"agents": {"type": "array", "items": _AGENT}},
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
_NULL_B: dict[str, Any] = {"type": ["boolean", "null"]}


def _obj(required: list[str], properties: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": required,
        "properties": properties,
    }


_RESULT = _obj(["at", "status"], {"at": _NULL_S, "status": _NULL_S})
_RESTORE = _obj(["at", "ok"], {"at": _NULL_S, "ok": _NULL_B})
_DOWNLOAD = _obj(
    ["source", "state", "done", "total", "pct", "last_progress_at", "stalled"],
    {
        "source": {"type": "string", "minLength": 1},
        "state": _NULL_S,
        "done": _NULL_N,
        "total": _NULL_N,
        "pct": _NULL_N,
        "last_progress_at": _NULL_S,
        "stalled": _NULL_B,
    },
)
_DRIVER = _obj(
    ["agent_id", "context_pct", "compactions", "stop_count", "ask_count", "idle_min", "measured_at"],
    {
        "agent_id": {"type": "string", "minLength": 1},
        "context_pct": _NULL_N,
        "compactions": _NULL_N,
        "stop_count": _NULL_N,
        "ask_count": _NULL_N,
        "idle_min": _NULL_N,
        "measured_at": _NULL_S,
    },
)
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
    "fleet.v1.backups": _obj(
        ["age_h", "stale", "last_result", "restore_test"],
        {
            "age_h": _NULL_N,
            "stale": _NULL_B,
            "last_result": {"anyOf": [_RESULT, {"type": "null"}]},
            "restore_test": {"anyOf": [_RESTORE, {"type": "null"}]},
        },
    ),
    "fleet.v1.downloads": _obj(
        ["state", "items"],
        {
            "state": {"anyOf": [{"enum": ["ok", "unknown"]}, {"type": "null"}]},
            "items": {"type": "array", "items": _DOWNLOAD},
        },
    ),
    "fleet.v1.harness": _obj(["drivers"], {"drivers": {"type": "array", "items": _DRIVER}}),
    "fleet.v1.harness_driver": _obj(["driver"], {"driver": {"anyOf": [_DRIVER, {"type": "null"}]}}),
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

_CI_VALUE: dict[str, Any] = {"anyOf": [{"enum": ["green", "red", "pending"]}, {"type": "null"}]}
_MQ_VALUE: dict[str, Any] = {"anyOf": [{"enum": ["queued", "not_queued", "dropped"]}, {"type": "null"}]}

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
                        "at": _TIMESTAMP_OR_NULL,
                    },
                },
            ]
        },
        "ready_since": _TIMESTAMP_OR_NULL,
        "stale_green": {"type": "boolean"},
        "minutes": {"type": ["integer", "null"], "minimum": 0},
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
    if schema_id == "fleet.v1.now":
        return _envelope_schema(schema_id, _NOW_DATA)
    if schema_id == "fleet.v1.epics":
        return _envelope_schema(schema_id, _EPICS_DATA)
    if schema_id == "fleet.v1.epic":
        return _envelope_schema(schema_id, {"anyOf": [_NOW_EPIC, {"type": "null"}]})
    if schema_id == "fleet.v1.agents":
        return _envelope_schema(schema_id, _AGENTS_DATA)
    if schema_id == "fleet.v1.agent":
        return _envelope_schema(schema_id, {"anyOf": [_AGENT, {"type": "null"}]})
    if schema_id == "fleet.v1.prs":
        return _envelope_schema(schema_id, _PRS_DATA)
    if schema_id == "fleet.v1.pr":
        return _envelope_schema(schema_id, _PR_DATA)
    return _envelope_schema(schema_id, _DATA_SCHEMAS.get(schema_id, {"type": "object"}))
