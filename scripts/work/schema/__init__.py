"""Load and validate the authoritative Work projection schema."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

SCHEMA_FILENAME = "work_projection.v1.json"
SCHEMA_VERSION = "work-projection.v1"

# Saved-view URL keys that are public-safe (enums / booleans / numeric IDs only).
ALLOWED_SAVED_VIEW_KEYS = frozenset(
    {
        "health",
        "kind",
        "lifecycle",
        "orphan",
        "repository_id",
        "source_id",
    }
)
MAX_FILTER_VALUE_LEN = 64
ALLOWED_HEALTH = frozenset({"ON_TRACK", "AT_RISK", "OFF_TRACK", "UNKNOWN"})
ALLOWED_KINDS = frozenset(
    {"issue", "pr", "task", "review", "verification", "arc", "milestone"}
)
# UI-exposed lifecycle chips only; arbitrary values would never-evict cache keys.
ALLOWED_LIFECYCLES = frozenset({"open", "draft", "running", "failed"})
ALLOWED_SOURCES = frozenset({"public-monitor", "private-local-adapter"})


class SchemaValidationError(ValueError):
    """Raised when a projection payload fails the authoritative schema."""


@lru_cache(maxsize=1)
def schema_path() -> Path:
    return Path(__file__).with_name(SCHEMA_FILENAME)


@lru_cache(maxsize=1)
def load_schema() -> dict[str, Any]:
    return json.loads(schema_path().read_text(encoding="utf-8"))


def schema_digest_sha256() -> str:
    import hashlib

    return hashlib.sha256(schema_path().read_bytes()).hexdigest()


def validate_projection(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate a projection document against the JSON Schema when available.

    Uses jsonschema if installed; otherwise performs a strict structural check
    of required top-level fields so tests remain deterministic offline.
    """
    if not isinstance(payload, dict):
        raise SchemaValidationError("projection must be an object")
    required = load_schema().get("required") or []
    missing = [key for key in required if key not in payload]
    if missing:
        raise SchemaValidationError(f"missing required fields: {', '.join(missing)}")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise SchemaValidationError(
            f"unsupported schema_version: {payload.get('schema_version')!r}"
        )
    if payload.get("foundation_status") != "FOUNDATION_COMPLETE":
        raise SchemaValidationError(
            "foundation_status must be FOUNDATION_COMPLETE (never COMPLETE)"
        )
    if payload.get("capabilities", {}).get("mutation") is not False:
        raise SchemaValidationError("capabilities.mutation must be false in foundation")
    try:
        import jsonschema
    except ImportError:  # pragma: no cover - jsonschema is normally present
        return payload
    try:
        jsonschema.validate(payload, load_schema())
    except jsonschema.ValidationError as exc:  # type: ignore[attr-defined]
        raise SchemaValidationError(str(exc.message)) from exc
    return payload


def parse_saved_view_params(raw: dict[str, str | list[str] | None]) -> dict[str, Any]:
    """Validate public-safe saved-view query parameters.

    Rejects unknown keys, free text, overlong values, and private endpoint keys.
    """
    filters: dict[str, Any] = {}
    for key, value in raw.items():
        if value is None or value == "":
            continue
        if key not in ALLOWED_SAVED_VIEW_KEYS:
            raise SchemaValidationError(f"saved-view key not allowed: {key}")
        values = value if isinstance(value, list) else [value]
        cleaned: list[str] = []
        for item in values:
            text = str(item).strip()
            if not text:
                continue
            if len(text) > MAX_FILTER_VALUE_LEN:
                raise SchemaValidationError(f"saved-view value too long for {key}")
            if any(ch.isspace() for ch in text) and key != "repository_id":
                raise SchemaValidationError(f"free text not allowed in saved-view: {key}")
            cleaned.append(text)
        if not cleaned:
            continue
        if key == "health":
            bad = [v for v in cleaned if v not in ALLOWED_HEALTH]
            if bad:
                raise SchemaValidationError(f"invalid health filter: {bad[0]}")
            filters["health"] = cleaned
        elif key == "kind":
            bad = [v for v in cleaned if v not in ALLOWED_KINDS]
            if bad:
                raise SchemaValidationError(f"invalid kind filter: {bad[0]}")
            filters["resource_kind"] = cleaned
        elif key == "lifecycle":
            bad = [v for v in cleaned if v not in ALLOWED_LIFECYCLES]
            if bad:
                raise SchemaValidationError(f"invalid lifecycle filter: {bad[0]}")
            filters["lifecycle"] = cleaned
        elif key == "orphan":
            if len(cleaned) != 1 or cleaned[0] not in {"true", "false", "1", "0"}:
                raise SchemaValidationError("orphan must be true or false")
            filters["orphan"] = cleaned[0] in {"true", "1"}
        elif key == "repository_id":
            # Public P1: exactly one configured repository. Arbitrary owner/name
            # strings would each create a never-evicted projection cache key and
            # force two GitHub enumerations. Private P2 stays browser-local.
            from scripts.work.sources_public import public_repository_id

            allowed_repo = public_repository_id()
            for item in cleaned:
                if "/" not in item or item.startswith("/") or ".." in item:
                    raise SchemaValidationError(f"invalid repository_id: {item}")
                if item != allowed_repo:
                    raise SchemaValidationError(f"invalid repository_id: {item}")
            filters["repository_id"] = cleaned
        elif key == "source_id":
            bad = [v for v in cleaned if v not in ALLOWED_SOURCES]
            if bad:
                raise SchemaValidationError(f"invalid source_id: {bad[0]}")
            filters["source_id"] = cleaned
    return filters


__all__ = [
    "ALLOWED_SAVED_VIEW_KEYS",
    "SCHEMA_FILENAME",
    "SCHEMA_VERSION",
    "SchemaValidationError",
    "load_schema",
    "parse_saved_view_params",
    "schema_digest_sha256",
    "schema_path",
    "validate_projection",
]
