"""OPSEC validation for WorkerRow payloads."""

from __future__ import annotations

import re
from typing import Any

from scripts.api.fleet_workers_models import _EPIC_RE, MAX_WORKERS_PER_REPORT, WorkerRow
from scripts.api.occupancy_sanitize import (
    _ALIAS_TOKEN,
    _FQDN,
    _IPV4,
    _looks_like_host,
)
from scripts.api.project_state_sanitize import ProjectStateValidationError

_BRANCH_HINT = re.compile(r"(?i)(?:^|[^A-Za-z0-9])(?:branch|refs/heads/)")
_PID_HINT = re.compile(r"(?i)(?:^|[^A-Za-z0-9])(?:pid[:\s=]|[\s(]pid[\s)=]|\bpid\b)")
_NONCE_HINT = re.compile(r"(?i)(?:run[_-]?nonce|nonce[:\s=])")
_ERROR_HINT = re.compile(r"(?i)(?:traceback|exception|error[:\s]|stderr)")
_PORT_HINT = re.compile(r"(?i)(?:^|[^0-9])(?:port|:[0-9]{2,5})(?:[^0-9]|$)")


def _worker_string_forbidden(text: str, *, allow_epic: bool = False) -> bool:
    if not text:
        return True
    if "/" in text or "\\" in text:
        return True
    if _looks_like_host(text):
        return True
    if _ALIAS_TOKEN.search(text):
        return True
    if not allow_epic and _PORT_HINT.search(text):
        return True
    if _BRANCH_HINT.search(text):
        return True
    if _PID_HINT.search(text):
        return True
    if _NONCE_HINT.search(text):
        return True
    if _ERROR_HINT.search(text):
        return True
    return bool(_IPV4.search(text) or _FQDN.search(text))


def _scan_worker_row(row: dict[str, Any]) -> bool:
    for key, value in row.items():
        if value is None:
            continue
        if isinstance(value, str):
            if key == "epic" and _EPIC_RE.fullmatch(value):
                continue
            if _worker_string_forbidden(value, allow_epic=key == "epic"):
                return True
        elif isinstance(value, (int, bool)):
            continue
        else:
            return True
    return False


def validate_worker_row_dict(row: dict[str, Any]) -> WorkerRow:
    if not isinstance(row, dict) or _scan_worker_row(row):
        raise ProjectStateValidationError("forbidden token in worker row")
    try:
        return WorkerRow.model_validate(row)
    except Exception as exc:
        raise ProjectStateValidationError("invalid worker row") from exc


def validate_workers_list(workers: Any) -> list[WorkerRow]:
    if not isinstance(workers, list):
        raise ProjectStateValidationError("invalid workers")
    if len(workers) > MAX_WORKERS_PER_REPORT:
        raise ProjectStateValidationError("workers list too long")
    return [validate_worker_row_dict(item) for item in workers if isinstance(item, dict)]
