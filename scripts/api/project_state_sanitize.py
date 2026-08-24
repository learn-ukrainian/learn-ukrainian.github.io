"""Sanitize and validate per-host project-state reports (no paths or host identity)."""

from __future__ import annotations

import re
from typing import Any

from scripts.api.occupancy_sanitize import (
    _ALIAS_TOKEN,
    _FQDN,
    _IPV4,
    _looks_like_host,
    opaque_host_id,
)

_FULL_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SERVICE_NAME_RE = re.compile(r"^[a-z][a-z0-9-]{0,31}$")
_COLLECTED_AT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")
_SERVICE_STATES = frozenset(
    {"running", "stopped", "degraded", "tunneled", "unavailable", "blocked"}
)
_REPO_KEYS = frozenset({"learn-ukrainian", "sibling"})
_SERVING_MODES = frozenset({"release", "checkout"})
_PORT_HINT = re.compile(r"(?i)(?:^|[^0-9])(?:port|:[0-9]{2,5})(?:[^0-9]|$)")


class ProjectStateValidationError(ValueError):
    """Report payload failed shape or OPSEC validation."""


def _string_forbidden(text: str) -> bool:
    if not text:
        return True
    if "/" in text or "\\" in text:
        return True
    if _looks_like_host(text):
        return True
    if _ALIAS_TOKEN.search(text):
        return True
    if _PORT_HINT.search(text):
        return True
    return bool(_IPV4.search(text) or _FQDN.search(text))


def _scan_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return _string_forbidden(value)
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return value < 0
    if isinstance(value, float):
        return not (value >= 0 and value == value)  # NaN check
    if isinstance(value, dict):
        return any(_scan_value(item) for item in value.values())
    if isinstance(value, list):
        return any(_scan_value(item) for item in value)
    return True


def validate_host_id(host_id: str) -> None:
    if not opaque_host_id(host_id):
        raise ProjectStateValidationError("invalid host_id")


def validate_report_document(document: dict[str, Any]) -> None:
    body = {key: value for key, value in document.items() if key != "collected_at"}
    if _scan_value(body):
        raise ProjectStateValidationError("forbidden token in report")

    host_id = document.get("host_id")
    if not isinstance(host_id, str):
        raise ProjectStateValidationError("invalid host_id")
    validate_host_id(host_id)

    primary = document.get("primary")
    if not isinstance(primary, dict):
        raise ProjectStateValidationError("invalid primary")
    for key in ("head_sha", "origin_main_sha"):
        sha = primary.get(key)
        if not isinstance(sha, str) or not _FULL_SHA_RE.fullmatch(sha):
            raise ProjectStateValidationError(f"invalid {key}")
    age = primary.get("origin_main_age_s")
    if not isinstance(age, (int, float)) or age < 0:
        raise ProjectStateValidationError("invalid origin_main_age_s")
    for key in ("ahead", "behind", "dirty_count"):
        val = primary.get(key)
        if not isinstance(val, int) or val < 0:
            raise ProjectStateValidationError(f"invalid {key}")

    worktrees = document.get("worktrees")
    if not isinstance(worktrees, dict):
        raise ProjectStateValidationError("invalid worktrees")
    count = worktrees.get("count")
    if not isinstance(count, int) or count < 0:
        raise ProjectStateValidationError("invalid worktrees.count")

    services = document.get("services")
    if not isinstance(services, list):
        raise ProjectStateValidationError("invalid services")
    for service in services:
        if not isinstance(service, dict):
            raise ProjectStateValidationError("invalid service row")
        name = service.get("name")
        if not isinstance(name, str) or not _SERVICE_NAME_RE.fullmatch(name):
            raise ProjectStateValidationError("invalid service name")
        state = service.get("state")
        if state not in _SERVICE_STATES:
            raise ProjectStateValidationError("invalid service state")
        repo = service.get("repo")
        if repo not in _REPO_KEYS:
            raise ProjectStateValidationError("invalid service repo")
        mode = service.get("serving_mode")
        if mode not in _SERVING_MODES:
            raise ProjectStateValidationError("invalid serving_mode")
        serving_sha = service.get("serving_sha")
        checkout_sha = service.get("checkout_sha")
        if serving_sha is not None and (
            not isinstance(serving_sha, str) or not _FULL_SHA_RE.fullmatch(serving_sha)
        ):
            raise ProjectStateValidationError("invalid serving_sha")
        if checkout_sha is not None and (
            not isinstance(checkout_sha, str) or not _FULL_SHA_RE.fullmatch(checkout_sha)
        ):
            raise ProjectStateValidationError("invalid checkout_sha")
        if mode == "release" and serving_sha is None and state == "running":
            raise ProjectStateValidationError("release mode requires serving_sha when running")
        if mode == "checkout" and checkout_sha is None and state == "running":
            raise ProjectStateValidationError("checkout mode requires checkout_sha when running")

    collected_at = document.get("collected_at")
    if not isinstance(collected_at, str) or not _COLLECTED_AT_RE.fullmatch(collected_at):
        raise ProjectStateValidationError("invalid collected_at")
