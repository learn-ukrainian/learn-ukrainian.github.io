"""Metaschema check for JSON Schemas, memoised by schema content."""

from __future__ import annotations

import json
from collections.abc import Mapping
from functools import lru_cache
from typing import Any

from jsonschema import Draft202012Validator


@lru_cache(maxsize=256)
def _check_canonical(canonical: str) -> None:
    Draft202012Validator.check_schema(json.loads(canonical))


def check_schema(schema: Mapping[str, Any]) -> None:
    """``Draft202012Validator.check_schema`` that runs once per distinct schema content.

    Whether a schema satisfies the metaschema is a pure function of its content, so callers that
    reload the same schema file for every validation skip the repeated (tens of milliseconds) check.
    The key is the canonical JSON of the content, never the object identity or path, so an edited
    schema is checked afresh. An invalid schema raises on every call, because a raised check is
    never memoised. A schema that does not round-trip through JSON is checked directly.
    """
    try:
        canonical = json.dumps(schema, sort_keys=True, separators=(",", ":"))
        round_trips = json.loads(canonical) == schema
    except (TypeError, ValueError):
        round_trips = False
    if not round_trips:
        Draft202012Validator.check_schema(schema)
        return
    _check_canonical(canonical)
