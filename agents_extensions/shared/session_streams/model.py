"""Typed values shared by the session-stream storage and hook surfaces."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

STREAM_ID_RE = re.compile(r"^(?:epic:[1-9][0-9]*|shared:[a-z][a-z0-9-]{0,63})$")
IDENTITY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,255}$")


class EntryType(StrEnum):
    """The only entry types accepted by the append API."""

    BINDING_ORDER = "binding_order"
    NEGATIVE_CONSTRAINT = "negative_constraint"
    DECISION = "decision"
    STATE = "state"
    NEXT_ACTION = "next_action"
    NOTE = "note"


PINNED_ENTRY_TYPES = frozenset({EntryType.BINDING_ORDER, EntryType.NEGATIVE_CONSTRAINT})


class SessionState(StrEnum):
    """Lifecycle states for one driver run."""

    OPEN = "open"
    ROLLING = "rolling"
    CLOSED = "closed"


@dataclass(frozen=True)
class LeaseHolder:
    """Exact harness-owned identity for one lease holder."""

    agent: str
    harness: str
    instance_id: str
    process_id: int
    task_id: str | None = None

    def validate(self) -> None:
        for label, value in (
            ("agent", self.agent),
            ("harness", self.harness),
            ("instance_id", self.instance_id),
        ):
            if not IDENTITY_RE.fullmatch(value):
                raise ValueError(f"{label} must be a non-empty path-safe identity")
        if self.task_id is not None and not IDENTITY_RE.fullmatch(self.task_id):
            raise ValueError("task_id must be a path-safe identity when supplied")
        if self.process_id <= 0:
            raise ValueError("process_id must be a positive integer")


@dataclass(frozen=True)
class Lease:
    """The exact fenced write authority returned by session open/heartbeat."""

    stream_id: str
    session_id: str
    lease_id: str
    generation: int
    fencing_token: int
    holder: LeaseHolder
    heartbeat_at: str
    expires_at: str
    ttl_seconds: int
    version: int


@dataclass(frozen=True)
class EntryRef:
    """One normalized reference attached to an immutable entry."""

    kind: str
    uri: str | None = None
    target_entry_id: int | None = None

    def validate(self) -> None:
        if not IDENTITY_RE.fullmatch(self.kind):
            raise ValueError("reference kind must be a path-safe identity")
        if (self.uri is None) == (self.target_entry_id is None):
            raise ValueError("a reference must set exactly one of uri or target_entry_id")
        if self.uri is not None and (not self.uri.strip() or "\x00" in self.uri):
            raise ValueError("reference uri must be non-empty text without NUL")
        if self.target_entry_id is not None and self.target_entry_id <= 0:
            raise ValueError("target_entry_id must be positive")


@dataclass(frozen=True)
class Entry:
    """One immutable semantic-memory entry."""

    entry_id: int
    stream_id: str
    session_id: str
    agent: str
    harness: str
    ts: str
    type: EntryType
    body: str
    body_sha256: str
    idempotency_key: str
    refs: tuple[EntryRef, ...] = ()


@dataclass(frozen=True)
class StreamDigest:
    """Pinned entries followed by a bounded recent non-pinned tail."""

    stream_id: str
    limit: int
    pinned: tuple[Entry, ...]
    recent: tuple[Entry, ...]
    high_water_entry_id: int

    @property
    def entries(self) -> tuple[Entry, ...]:
        return self.pinned + self.recent

    @property
    def digest_sha256(self) -> str:
        payload = {
            "stream_id": self.stream_id,
            "limit": self.limit,
            "high_water_entry_id": self.high_water_entry_id,
            "pinned": [entry_as_dict(entry) for entry in self.pinned],
            "recent": [entry_as_dict(entry) for entry in self.recent],
        }
        return sha256_text(canonical_json(payload))


@dataclass(frozen=True)
class ForceCloseProof:
    """Recorded proof that an expired holder process was absent at apply time."""

    stream_id: str
    session_id: str
    lease_id: str
    holder_instance_id: str
    holder_process_id: int
    heartbeat_at: str
    expires_at: str
    observed_at: str
    heartbeat_age_seconds: int
    process_probe: str
    candidate_agent: str
    candidate_harness: str
    candidate_instance_id: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": "session_stream_force_close.v1",
            "stream_id": self.stream_id,
            "session_id": self.session_id,
            "lease_id": self.lease_id,
            "holder_instance_id": self.holder_instance_id,
            "holder_process_id": self.holder_process_id,
            "heartbeat_at": self.heartbeat_at,
            "expires_at": self.expires_at,
            "observed_at": self.observed_at,
            "heartbeat_age_seconds": self.heartbeat_age_seconds,
            "process_probe": self.process_probe,
            "candidate_agent": self.candidate_agent,
            "candidate_harness": self.candidate_harness,
            "candidate_instance_id": self.candidate_instance_id,
        }


def validate_stream_id(stream_id: str) -> str:
    """Return a canonical stream ID or fail closed."""
    if not STREAM_ID_RE.fullmatch(stream_id):
        raise ValueError("stream_id must be epic:<positive-number> or shared:<path-safe-name>")
    return stream_id


def utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def isoformat_z(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("timestamps must be timezone-aware")
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("stored timestamps must include a timezone")
    return parsed.astimezone(UTC)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def entry_as_dict(entry: Entry) -> dict[str, Any]:
    return {
        "entry_id": entry.entry_id,
        "stream": entry.stream_id,
        "session_id": entry.session_id,
        "agent": entry.agent,
        "harness": entry.harness,
        "ts": entry.ts,
        "type": entry.type.value,
        "body": entry.body,
        "body_sha256": entry.body_sha256,
        "idempotency_key": entry.idempotency_key,
        "refs": [
            {"kind": ref.kind, "uri": ref.uri, "target_entry_id": ref.target_entry_id}
            for ref in entry.refs
        ],
    }
