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
_VALIDATORS: dict[str, Draft202012Validator] = {}


def _resolve_schema_path(schema_name: str, repo_root: Path | None = None) -> Path:
    from .generator import _checked_path

    if repo_root is not None:
        cand_rel = f"schemas/{schema_name}"
        schemas_dir = repo_root / "schemas"
        cand = repo_root / cand_rel
        if schemas_dir.exists(follow_symlinks=False) or cand.exists(follow_symlinks=False):
            return _checked_path(repo_root, cand_rel, "schemas")
    return _checked_path(REPO_ROOT, f"schemas/{schema_name}", "schemas")


def get_validator(schema_path: Path | None = None, repo_root: Path | None = None) -> Draft202012Validator:
    """Return a cached Draft202012Validator for module-digest-v1.schema.json."""
    from .generator import _checked_path

    global _VALIDATOR
    root = repo_root or REPO_ROOT
    if schema_path is not None:
        path = _checked_path(root, schema_path, "schemas")
    else:
        path = _resolve_schema_path("module-digest-v1.schema.json", repo_root)
        if repo_root is None and _VALIDATOR is not None:
            return _VALIDATOR
    if not path.is_file():
        raise DigestError(codes.DIGEST_SCHEMA_INVALID, f"schema file not found: {path}")
    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise DigestError(codes.DIGEST_SCHEMA_INVALID, f"schema file unreadable: {exc}") from exc
    validator = Draft202012Validator(schema)
    if schema_path is None and repo_root is None:
        _VALIDATOR = validator
    return validator


def get_cached_validator(schema_name: str, repo_root: Path | None = None) -> Draft202012Validator:
    """Return a cached Draft202012Validator for any schema under schemas/."""
    path = _resolve_schema_path(schema_name, repo_root)
    cache_key = str(path)
    if cache_key in _VALIDATORS:
        return _VALIDATORS[cache_key]
    if not path.is_file():
        raise DigestError(codes.DIGEST_SCHEMA_INVALID, f"schema file not found: {path}")
    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise DigestError(codes.DIGEST_SCHEMA_INVALID, f"schema file unreadable: {exc}") from exc
    validator = Draft202012Validator(schema)
    _VALIDATORS[cache_key] = validator
    return validator


def validate_digest(doc: Any, *, schema_path: Path | None = None, repo_root: Path | None = None) -> None:
    """Validate document against module-digest-v1.schema.json."""
    if schema_path is not None:
        validator = get_validator(schema_path, repo_root=repo_root)
    else:
        validator = get_cached_validator("module-digest-v1.schema.json", repo_root)
    errors = sorted(validator.iter_errors(doc), key=lambda e: [str(p) for p in e.absolute_path])
    if errors:
        first = errors[0]
        path_str = ".".join(str(p) for p in first.absolute_path) or "root"
        raise DigestError(codes.DIGEST_SCHEMA_INVALID, f"at {path_str}: {first.message}")


def validate_plan_schema(doc: Any, plan_path: Path, *, repo_root: Path | None = None) -> None:
    """Validate plan document against module-plan-v2.schema.json."""
    validator = get_cached_validator("module-plan-v2.schema.json", repo_root)
    errors = sorted(validator.iter_errors(doc), key=lambda e: [str(p) for p in e.absolute_path])
    if errors:
        first = errors[0]
        path_str = ".".join(str(p) for p in first.absolute_path) or "root"
        raise DigestError(codes.PLAN_INVALID, f"module plan {plan_path} breaks schema at {path_str}: {first.message}")


def validate_observed_schema(doc: Any, obs_path: Path, *, repo_root: Path | None = None) -> None:
    """Validate observed state document against learner-observed-v1.schema.json."""
    validator = get_cached_validator("learner-observed-v1.schema.json", repo_root)
    errors = sorted(validator.iter_errors(doc), key=lambda e: [str(p) for p in e.absolute_path])
    if errors:
        first = errors[0]
        path_str = ".".join(str(p) for p in first.absolute_path) or "root"
        raise DigestError(codes.OBSERVED_INVALID, f"observed file {obs_path} breaks schema at {path_str}: {first.message}")


def validate_resolutions_schema(doc: Any, res_path: Path, *, repo_root: Path | None = None) -> None:
    """Validate resolutions receipts document against resolution-receipts-v1.schema.json."""
    validator = get_cached_validator("resolution-receipts-v1.schema.json", repo_root)
    errors = sorted(validator.iter_errors(doc), key=lambda e: [str(p) for p in e.absolute_path])
    if errors:
        first = errors[0]
        path_str = ".".join(str(p) for p in first.absolute_path) or "root"
        raise DigestError(codes.RESOLUTIONS_INVALID, f"resolutions file {res_path} breaks schema at {path_str}: {first.message}")
