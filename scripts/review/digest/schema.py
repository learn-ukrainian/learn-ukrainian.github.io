"""Schema loader and validator for module digest documents (#8430 WP 15 Part R2a)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from . import codes
from .error import DigestError

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = REPO_ROOT / "schemas/module-digest-v1.schema.json"

_VALIDATOR: Draft202012Validator | None = None
_VALIDATORS: dict[tuple[str, str], Draft202012Validator] = {}


def _resolve_schema_path(schema_name: str, repo_root: Path | None = None) -> Path:
    from .generator import _checked_path, resolve_repo_root

    root = resolve_repo_root(repo_root)
    cand_rel = f"schemas/{schema_name}"
    return _checked_path(root, cand_rel, "schemas")


def _load_validator(path: Path) -> Draft202012Validator:
    """Validate path exists and load/cache Draft202012Validator keyed on (resolved path, sha256)."""
    if not path.is_file():
        raise DigestError(codes.DIGEST_SCHEMA_INVALID, f"schema file not found: {path}")
    try:
        raw = path.read_bytes()
    except Exception as exc:
        raise DigestError(codes.DIGEST_SCHEMA_INVALID, f"schema file unreadable: {exc}") from exc

    file_sha256 = hashlib.sha256(raw).hexdigest()
    cache_key = (str(path.resolve()), file_sha256)
    if cache_key in _VALIDATORS:
        return _VALIDATORS[cache_key]

    try:
        schema = json.loads(raw.decode("utf-8"))
        validator = Draft202012Validator(schema)
    except Exception as exc:
        raise DigestError(codes.DIGEST_SCHEMA_INVALID, f"schema file unreadable: {exc}") from exc

    _VALIDATORS[cache_key] = validator
    return validator


def get_validator(schema_path: Path | None = None, repo_root: Path | None = None) -> Draft202012Validator:
    """Return a cached Draft202012Validator for module-digest-v1.schema.json."""
    from .generator import _checked_path, resolve_repo_root

    global _VALIDATOR
    root = resolve_repo_root(repo_root)
    if schema_path is not None:
        path = _checked_path(root, schema_path, "schemas")
    else:
        path = _resolve_schema_path("module-digest-v1.schema.json", repo_root=root)
    validator = _load_validator(path)
    if schema_path is None and repo_root is None:
        _VALIDATOR = validator
    return validator


def get_cached_validator(schema_name: str, repo_root: Path | None = None) -> Draft202012Validator:
    """Return a cached Draft202012Validator for any schema under schemas/."""
    from .generator import resolve_repo_root

    root = resolve_repo_root(repo_root)
    path = _resolve_schema_path(schema_name, repo_root=root)
    return _load_validator(path)


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
        raise DigestError(
            codes.OBSERVED_INVALID, f"observed file {obs_path} breaks schema at {path_str}: {first.message}"
        )


def validate_resolutions_schema(doc: Any, res_path: Path, *, repo_root: Path | None = None) -> None:
    """Validate resolutions receipts document against resolution-receipts-v1.schema.json."""
    validator = get_cached_validator("resolution-receipts-v1.schema.json", repo_root)
    errors = sorted(validator.iter_errors(doc), key=lambda e: [str(p) for p in e.absolute_path])
    if errors:
        first = errors[0]
        path_str = ".".join(str(p) for p in first.absolute_path) or "root"
        raise DigestError(
            codes.RESOLUTIONS_INVALID, f"resolutions file {res_path} breaks schema at {path_str}: {first.message}"
        )


def validate_provenance_schema(doc: Any, prov_path: Path, *, repo_root: Path | None = None) -> None:
    """Validate provenance document against lesson-provenance-v1.schema.json."""
    validator = get_cached_validator("lesson-provenance-v1.schema.json", repo_root)
    errors = sorted(validator.iter_errors(doc), key=lambda e: [str(p) for p in e.absolute_path])
    if errors:
        first = errors[0]
        path_str = ".".join(str(p) for p in first.absolute_path) or "root"
        raise DigestError(
            codes.PROVENANCE_INVALID, f"provenance file {prov_path} breaks schema at {path_str}: {first.message}"
        )
