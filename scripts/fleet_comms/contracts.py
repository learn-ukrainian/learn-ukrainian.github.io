"""Typed, transport-neutral Fleet Communications completion contract."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import uuid4


class CompletionState(StrEnum):
    """Whether a runtime adapter proved a provider response is terminal."""

    COMPLETE = "complete"
    LENGTH_LIMITED = "length_limited"
    TRANSPORT_INCOMPLETE = "transport_incomplete"
    FAILED = "failed"
    UNKNOWN = "unknown"


def new_id(kind: str) -> str:
    """Return a globally unique, readable v1 identifier for durable records."""
    if not kind or any(not (char.islower() or char.isdigit() or char == "-") for char in kind):
        raise ValueError("Fleet Communications ID kinds use lowercase letters, digits, and hyphens")
    return f"{kind}_{uuid4().hex}"


@dataclass(frozen=True, slots=True)
class AssistantSegment:
    """One ordered assistant fragment retained from a runtime capture."""

    text: str
    sequence: int
    provider_event_id: str | None = None

    def __post_init__(self) -> None:
        if self.sequence < 0:
            raise ValueError("Assistant segment sequence must be non-negative")


@dataclass(frozen=True, slots=True)
class ResponseEnvelope:
    """Complete evidence needed to decide whether an output may be accepted.

    ``complete`` requires the adapter to have observed the terminal event it
    documents. Legacy adapters remain ``unknown`` until their B1/B2 conformance
    work supplies this evidence; their existing ``ParseResult.ok`` continues to
    drive compatibility paths during the migration.
    """

    segments: tuple[AssistantSegment, ...]
    completion_state: CompletionState
    provider_stop_reason: str | None = None
    terminal_event_observed: bool = False
    process_returncode: int | None = None
    transport_metadata: dict[str, Any] = field(default_factory=dict)
    raw_capture_artifact_id: str | None = None
    raw_capture_sha256: str | None = None
    session_id: str | None = None
    token_metadata: dict[str, int | None] = field(default_factory=dict)
    tool_call_metadata: tuple[dict[str, Any], ...] = ()

    def __post_init__(self) -> None:
        sequences = [segment.sequence for segment in self.segments]
        if sequences != sorted(sequences) or len(sequences) != len(set(sequences)):
            raise ValueError("Assistant segments must have unique ordered sequences")
        if self.completion_state is CompletionState.COMPLETE and not self.terminal_event_observed:
            raise ValueError("Complete envelopes require an observed terminal event")
        if bool(self.raw_capture_artifact_id) != bool(self.raw_capture_sha256):
            raise ValueError("Raw capture artifact ID and digest must be supplied together")

    @property
    def response_text(self) -> str:
        return "".join(segment.text for segment in self.segments)

    @property
    def is_formal_review_eligible(self) -> bool:
        """Formal review accepts only terminally proven complete output."""
        return self.completion_state is CompletionState.COMPLETE and self.terminal_event_observed

    def to_dict(self) -> dict[str, Any]:
        """Serialize without flattening ordered segments into one ambiguous string."""
        return {
            "segments": [
                {
                    "text": segment.text,
                    "sequence": segment.sequence,
                    "provider_event_id": segment.provider_event_id,
                }
                for segment in self.segments
            ],
            "completion_state": self.completion_state.value,
            "provider_stop_reason": self.provider_stop_reason,
            "terminal_event_observed": self.terminal_event_observed,
            "process_returncode": self.process_returncode,
            "transport_metadata": self.transport_metadata,
            "raw_capture_artifact_id": self.raw_capture_artifact_id,
            "raw_capture_sha256": self.raw_capture_sha256,
            "session_id": self.session_id,
            "token_metadata": self.token_metadata,
            "tool_call_metadata": list(self.tool_call_metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ResponseEnvelope:
        """Deserialize a persisted v1 envelope, validating its invariants."""
        return cls(
            segments=tuple(
                AssistantSegment(
                    text=str(segment["text"]),
                    sequence=int(segment["sequence"]),
                    provider_event_id=segment.get("provider_event_id"),
                )
                for segment in payload["segments"]
            ),
            completion_state=CompletionState(payload["completion_state"]),
            provider_stop_reason=payload.get("provider_stop_reason"),
            terminal_event_observed=bool(payload.get("terminal_event_observed", False)),
            process_returncode=payload.get("process_returncode"),
            transport_metadata=dict(payload.get("transport_metadata", {})),
            raw_capture_artifact_id=payload.get("raw_capture_artifact_id"),
            raw_capture_sha256=payload.get("raw_capture_sha256"),
            session_id=payload.get("session_id"),
            token_metadata=dict(payload.get("token_metadata", {})),
            tool_call_metadata=tuple(payload.get("tool_call_metadata", [])),
        )
