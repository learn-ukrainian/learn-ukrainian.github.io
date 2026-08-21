"""Shared occupancy occupant sanitizers (no host probes, no presence store)."""

from __future__ import annotations

import re
from typing import Any

CLOUD_OBSERVER_HOST_ID = "cloud-observer"
OCCUPANT_KINDS = frozenset({"driver", "worker", "job", "service", "observer"})
OBSERVER_STATUSES = frozenset({"working", "blocked", "idle"})
_OPAQUE_HOST_ID = re.compile(r"^[a-z][a-z0-9-]{0,62}$")
_SAFE_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
_TASK_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_SUMMARY_OK = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 .,'!?;()-]{0,79}$")
_IPV4 = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
_IPV6 = re.compile(r":")
_FQDN = re.compile(r"\.[A-Za-z]{2,}$")
_ALIAS_TOKEN = re.compile(
    r"(?:^|[^A-Za-z0-9])(atlas-runner|hramatka|vps)(?:[^A-Za-z0-9]|$)",
    re.IGNORECASE,
)
_SUMMARY_SECRET = re.compile(
    r"(?i)\b(token|password|secret|passwd|api[_-]?key|bearer|reserved_ram|pid)\b"
)
_CANONICAL_ALIASES = frozenset({"atlas-runner", "hramatka", "vps"})
_RESERVED_HOST_IDS = frozenset({CLOUD_OBSERVER_HOST_ID})


def opaque_host_id(value: str) -> bool:
    return bool(
        _OPAQUE_HOST_ID.fullmatch(value)
        and value not in _CANONICAL_ALIASES
        and value not in _RESERVED_HOST_IDS
        and not _IPV4.search(value)
        and not _IPV6.search(value)
        and "." not in value
    )


def safe_field(value: Any, *, role: str = "agent") -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or "/" in text or "\\" in text:
        return None
    if _IPV4.search(text) or _IPV6.search(text) or _FQDN.search(text):
        return None
    token = _TASK_TOKEN if role == "task_id" else _SAFE_TOKEN
    if not token.fullmatch(text):
        return None
    if role != "epic" and _ALIAS_TOKEN.search(text):
        return None
    return text


def safe_summary(value: Any) -> str | None:
    """Short current-work text for the loopback POST ack only.

    Occupancy never echoes this field. Reject paths, addresses, aliases,
    assignment-shaped secrets, and credential keywords.
    """
    if value is None:
        return None
    text = " ".join(str(value).split())
    if not text or len(text) > 80:
        return None
    if any(ch in text for ch in "/\\=@"):
        return None
    if _IPV4.search(text) or _IPV6.search(text) or _FQDN.search(text):
        return None
    if _ALIAS_TOKEN.search(text) or _SUMMARY_SECRET.search(text):
        return None
    if not _SUMMARY_OK.fullmatch(text):
        return None
    return text


def occupant(
    *,
    kind: str,
    agent: Any = None,
    task_id: Any = None,
    epic: Any = None,
    status: Any = None,
) -> dict[str, str | None] | None:
    if kind not in OCCUPANT_KINDS:
        return None
    task = safe_field(task_id, role="task_id")
    if task is None:
        return None
    row: dict[str, str | None] = {
        "kind": kind,
        "agent": safe_field(agent, role="agent"),
        "task_id": task,
        "epic": safe_field(epic, role="epic"),
    }
    if kind == "observer":
        status_text = str(status or "").strip()
        if status_text not in OBSERVER_STATUSES:
            return None
        row["status"] = status_text
    return row
