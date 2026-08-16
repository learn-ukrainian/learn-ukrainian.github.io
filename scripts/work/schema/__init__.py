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

# Finite per-key raw cardinality bounds derived from each closed domain.
# Reject excess raw repetitions *before* canonicalization so request work is
# bounded even when values are duplicates. Singleton domains (orphan,
# repository_id) accept at most one raw value.
FILTER_MAX_RAW_ITEMS: dict[str, int] = {
    "health": len(ALLOWED_HEALTH),
    "kind": len(ALLOWED_KINDS),
    "lifecycle": len(ALLOWED_LIFECYCLES),
    "orphan": 1,
    "repository_id": 1,
    "source_id": len(ALLOWED_SOURCES),
}

# Parsed key emitted for query key ``kind``.
_PARSED_KIND_KEY = "resource_kind"


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


def canonicalize_multivalue(values: list[str]) -> list[str]:
    """Deduplicate and deterministically sort multivalue filter members.

    Permanent projection cache keys must not diverge for equivalent query forms
    such as ``?health=A&health=B`` vs ``?health=B&health=A&health=A``.
    """
    return sorted(set(values))


def filters_to_saved_view_raw(
    filters: dict[str, Any],
) -> dict[str, str | list[str] | None]:
    """Normalize a filter dict (raw or already-parsed) for ``parse_saved_view_params``.

    Accepts both query-shaped keys (``kind``) and the parser's internal
    ``resource_kind`` so endpoint-canonical and direct-call filters re-enter the
    same admission path without encoding drift.
    """
    raw: dict[str, str | list[str] | None] = {}
    for key, value in filters.items():
        if key == _PARSED_KIND_KEY:
            out_key = "kind"
        elif key in ALLOWED_SAVED_VIEW_KEYS:
            out_key = key
        else:
            raise SchemaValidationError(f"saved-view key not allowed: {key}")
        if value is None or value == "":
            continue
        if isinstance(value, bool):
            if out_key != "orphan":
                raise SchemaValidationError(f"boolean not allowed for saved-view: {out_key}")
            raw[out_key] = "true" if value else "false"
        elif isinstance(value, (list, tuple)):
            raw[out_key] = [str(item) for item in value]
        else:
            raw[out_key] = str(value)
    return raw


def admit_projection_filters(filters: dict[str, Any] | None) -> dict[str, Any]:
    """Canonicalize and validate filters at every projection-builder entry point.

    Direct ``build_projection`` / ``build_public_projection`` callers cannot
    bypass saved-view admission: unknown keys and foreign ``repository_id``
    values raise; aliases (``kind`` / ``resource_kind``) collapse to one form.
    """
    if not filters:
        return {}
    return parse_saved_view_params(filters_to_saved_view_raw(filters))


def parse_saved_view_params(raw: dict[str, str | list[str] | None]) -> dict[str, Any]:
    """Validate public-safe saved-view query parameters.

    Rejects unknown keys, free text, overlong values, private endpoint keys, and
    raw multivalue lists that exceed the finite per-key domain bound (checked
    before canonicalization). Multivalue filters are always returned as
    deduplicated, sorted sequences so permanent cache keys stay canonical across
    duplicate/reordered query forms within the allowed raw bound.
    """
    filters: dict[str, Any] = {}
    for key, value in raw.items():
        if value is None or value == "":
            continue
        if key not in ALLOWED_SAVED_VIEW_KEYS:
            raise SchemaValidationError(f"saved-view key not allowed: {key}")
        values = value if isinstance(value, list) else [value]
        # Bound raw request work before any membership / admit work.
        max_items = FILTER_MAX_RAW_ITEMS[key]
        if len(values) > max_items:
            raise SchemaValidationError(
                f"saved-view {key} exceeds max {max_items} values"
            )
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
            filters["health"] = canonicalize_multivalue(cleaned)
        elif key == "kind":
            bad = [v for v in cleaned if v not in ALLOWED_KINDS]
            if bad:
                raise SchemaValidationError(f"invalid kind filter: {bad[0]}")
            filters["resource_kind"] = canonicalize_multivalue(cleaned)
        elif key == "lifecycle":
            bad = [v for v in cleaned if v not in ALLOWED_LIFECYCLES]
            if bad:
                raise SchemaValidationError(f"invalid lifecycle filter: {bad[0]}")
            filters["lifecycle"] = canonicalize_multivalue(cleaned)
        elif key == "orphan":
            if len(cleaned) != 1 or cleaned[0] not in {"true", "false", "1", "0"}:
                raise SchemaValidationError("orphan must be true or false")
            filters["orphan"] = cleaned[0] in {"true", "1"}
        elif key == "repository_id":
            # Public P1: exactly one closed public repository. Arbitrary
            # owner/name strings (and env overrides) must never create cache
            # keys or repoint collectors. Private P2 stays browser-local.
            # Same admission gate as collectors / normalize — no sibling bypass.
            from scripts.work.sources_public import admit_public_repository_id

            for item in cleaned:
                try:
                    admit_public_repository_id(item)
                except ValueError as exc:
                    raise SchemaValidationError(f"invalid repository_id: {item}") from exc
            filters["repository_id"] = canonicalize_multivalue(cleaned)
        elif key == "source_id":
            bad = [v for v in cleaned if v not in ALLOWED_SOURCES]
            if bad:
                raise SchemaValidationError(f"invalid source_id: {bad[0]}")
            filters["source_id"] = canonicalize_multivalue(cleaned)
    return filters


__all__ = [
    "ALLOWED_HEALTH",
    "ALLOWED_KINDS",
    "ALLOWED_LIFECYCLES",
    "ALLOWED_SAVED_VIEW_KEYS",
    "ALLOWED_SOURCES",
    "FILTER_MAX_RAW_ITEMS",
    "SCHEMA_FILENAME",
    "SCHEMA_VERSION",
    "SchemaValidationError",
    "admit_projection_filters",
    "canonicalize_multivalue",
    "filters_to_saved_view_raw",
    "load_schema",
    "parse_saved_view_params",
    "schema_digest_sha256",
    "schema_path",
    "validate_projection",
]
