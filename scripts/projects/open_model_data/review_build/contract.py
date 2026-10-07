"""Frozen omd-review-record.v1 contract (REVIEW_BUILD.md §3)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import astuple, dataclass
from typing import Literal

Outcome = Literal["accepted", "rejected", "withheld", "excluded"]


@dataclass(frozen=True)
class Citation:
    source_id: str
    store: str
    table: str
    row_key: str
    field: str
    locator: str
    field_sha256: str


@dataclass(frozen=True)
class Value:
    slot: str
    text: str
    citations: tuple[Citation, ...]
    span: tuple[int, int] | None
    transform: str


@dataclass(frozen=True)
class Candidate:
    component: str
    unit_id: str
    outcome: Outcome
    reason: str
    evidence: tuple[str, ...]
    operation: str
    slots: tuple[Value, ...]
    context: tuple[Value, ...]
    response: tuple[Value, ...]
    flags: tuple[str, ...]


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def values(candidate: Candidate) -> tuple[Value, ...]:
    return candidate.slots + candidate.context + candidate.response


def record_id(candidate: Candidate) -> str:
    return digest(
        canonical(
            {
                "component": candidate.component,
                "operation": candidate.operation,
                "unit_id": candidate.unit_id,
                "values": [
                    [v.slot, v.text, [astuple(c) for c in v.citations], v.span, v.transform] for v in values(candidate)
                ],
            }
        )
    )


def candidate_from_dict(raw: dict) -> Candidate:
    def read_value(v: dict) -> Value:
        return Value(
            v["slot"],
            v["text"],
            tuple(Citation(**c) for c in v["citations"]),
            tuple(v["span"]) if v["span"] is not None else None,
            v["transform"],
        )

    return Candidate(
        raw["component"],
        raw["unit_id"],
        raw["outcome"],
        raw["reason"],
        tuple(raw["evidence"]),
        raw["operation"],
        tuple(read_value(v) for v in raw["slots"]),
        tuple(read_value(v) for v in raw["context"]),
        tuple(read_value(v) for v in raw["response"]),
        tuple(raw["flags"]),
    )
