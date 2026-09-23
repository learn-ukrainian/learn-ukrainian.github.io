"""Schema loader and validator for module digest documents (#8430 WP 15 Part R2a)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from . import codes
from .error import DigestError

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = REPO_ROOT / "schemas/module-digest-v1.schema.json"

_VALIDATOR: Draft202012Validator | None = None


def get_validator(schema_path: Path | None = None) -> Draft202012Validator:
    """Return a cached Draft202012Validator for module-digest-v1.schema.json."""
    global _VALIDATOR
    path = schema_path or SCHEMA_PATH
    if path == SCHEMA_PATH and _VALIDATOR is not None:
        return _VALIDATOR
    if not path.is_file():
        raise DigestError(codes.DIGEST_SCHEMA_INVALID, f"schema file not found: {path}")
    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise DigestError(codes.DIGEST_SCHEMA_INVALID, f"schema file unreadable: {exc}") from exc
    validator = Draft202012Validator(schema)
    if path == SCHEMA_PATH:
        _VALIDATOR = validator
    return validator


def validate_digest(doc: Any, *, schema_path: Path | None = None) -> None:
    """Validate document against module-digest-v1.schema.json."""
    validator = get_validator(schema_path)
    errors = sorted(validator.iter_errors(doc), key=lambda e: [str(p) for p in e.absolute_path])
    if errors:
        first = errors[0]
        path_str = ".".join(str(p) for p in first.absolute_path) or "root"
        raise DigestError(codes.DIGEST_SCHEMA_INVALID, f"at {path_str}: {first.message}")
