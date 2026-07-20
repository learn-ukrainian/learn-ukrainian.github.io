"""Request / delivery executor skeleton (Fleet Comms PR-D / #5512).

One path for foreground and background work: create a durable request, resolve
endpoint (incl. permanent Gemini→AGY retirement), run adapter conformance on a
raw capture, store the raw artifact, and advance request state only on proven
completion.

Bridge defaults remain legacy. Opt-in message plane (PR-E) may shadow/dual_write
via ``scripts.fleet_comms.message_plane`` without flipping production defaults.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from scripts.fleet_comms.adapter_conformance import CaptureInput, conform
from scripts.fleet_comms.artifacts import ArtifactStore
from scripts.fleet_comms.contracts import CompletionState, ResponseEnvelope, new_id
from scripts.fleet_comms.endpoints import EndpointRegistry, load_endpoint_registry
from scripts.fleet_comms.migrations import apply_migrations

REQUEST_STATES = frozenset(
    {"queued", "running", "complete", "incomplete", "failed", "expired", "dead_lettered"}
)


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True, slots=True)
class RequestRecord:
    request_id: str
    request_message_id: str
    requested_recipient: str
    resolved_recipient: str
    state: str
    expires_at: str
    completion_state: str
    created_at: str
    updated_at: str
    envelope: ResponseEnvelope | None = None
    raw_capture_artifact_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "request_id": self.request_id,
            "request_message_id": self.request_message_id,
            "requested_recipient": self.requested_recipient,
            "resolved_recipient": self.resolved_recipient,
            "state": self.state,
            "expires_at": self.expires_at,
            "completion_state": self.completion_state,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "raw_capture_artifact_id": self.raw_capture_artifact_id,
        }
        if self.envelope is not None:
            payload["envelope"] = self.envelope.to_dict()
        return payload


class RequestExecutorError(RuntimeError):
    """Request executor refused an operation."""


class RequestExecutor:
    """Durable request lifecycle over communications SQLite + artifact store."""

    def __init__(
        self,
        *,
        store: ArtifactStore | None = None,
        registry: EndpointRegistry | None = None,
        root: Path | None = None,
        default_ttl_seconds: int | None = None,
    ) -> None:
        self.store = store or ArtifactStore(root=root)
        self.registry = registry or load_endpoint_registry()
        self.default_ttl_seconds = default_ttl_seconds
        self._conn = self.store.connection
        apply_migrations(self._conn)

    def close(self) -> None:
        self.store.close()

    def __enter__(self) -> RequestExecutor:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def create_request(
        self,
        *,
        recipient: str,
        body: str,
        sender: str = "request-executor",
        ttl_seconds: int | None = None,
        conversation_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RequestRecord:
        endpoint, matched_name = self.registry.resolve(recipient)
        # resolve(): live → (endpoint, endpoint.name); retired → (successor, retired_name).
        requested = matched_name
        resolved = endpoint.name
        ttl = ttl_seconds
        if ttl is None:
            ttl = self.default_ttl_seconds if self.default_ttl_seconds is not None else endpoint.default_ttl_seconds
        now = _utc_now()
        expires = now + timedelta(seconds=int(ttl))
        conv = conversation_id or new_id("conversation")
        msg_id = new_id("message")
        req_id = new_id("request")
        now_s = _iso(now)
        expires_s = _iso(expires)

        self._conn.execute(
            "INSERT OR IGNORE INTO conversations(conversation_id, created_at, source, title) VALUES (?, ?, ?, ?)",
            (conv, now_s, "request-executor", None),
        )
        self._conn.execute(
            """INSERT INTO comms_messages(
                message_id, conversation_id, kind, sender, recipient, body_inline,
                content_sha256, metadata_json, created_at
            ) VALUES (?, ?, 'request', ?, ?, ?, ?, ?, ?)""",
            (
                msg_id,
                conv,
                sender,
                resolved,
                body,
                None,
                json.dumps(metadata or {}, sort_keys=True),
                now_s,
            ),
        )
        self._conn.execute(
            """INSERT INTO requests(
                request_id, request_message_id, requested_recipient, resolved_recipient,
                state, expires_at, completion_state, invocation_spec_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, 'queued', ?, 'unknown', ?, ?, ?)""",
            (
                req_id,
                msg_id,
                requested,
                resolved,
                expires_s,
                json.dumps(
                    {
                        "recipient": recipient,
                        "requested_recipient": requested,
                        "resolved_recipient": resolved,
                        "ttl_seconds": ttl,
                    },
                    sort_keys=True,
                ),
                now_s,
                now_s,
            ),
        )
        self._conn.commit()
        return self.get_request(req_id)

    def get_request(self, request_id: str) -> RequestRecord:
        row = self._conn.execute(
            "SELECT * FROM requests WHERE request_id = ?", (request_id,)
        ).fetchone()
        if row is None:
            raise RequestExecutorError(f"request not found: {request_id}")
        return RequestRecord(
            request_id=str(row["request_id"]),
            request_message_id=str(row["request_message_id"]),
            requested_recipient=str(row["requested_recipient"]),
            resolved_recipient=str(row["resolved_recipient"]),
            state=str(row["state"]),
            expires_at=str(row["expires_at"]),
            completion_state=str(row["completion_state"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )

    def execute_capture(
        self,
        request_id: str,
        *,
        adapter: str | None = None,
        stdout: str = "",
        stderr: str = "",
        returncode: int | None = 0,
        events: tuple[dict[str, Any], ...] = (),
        raw_bytes: bytes | None = None,
        session_id: str | None = None,
    ) -> RequestRecord:
        """Run adapter conformance on a capture and persist the outcome.

        Production adapters will stream into the artifact store then call this
        with the same bytes. Tests inject fixtures directly.
        """
        req = self.get_request(request_id)
        if req.state not in {"queued", "running"}:
            raise RequestExecutorError(f"request {request_id} is not executable (state={req.state})")
        if req.expires_at < _iso(_utc_now()):
            self._set_state(request_id, "expired", CompletionState.UNKNOWN)
            raise RequestExecutorError(f"request {request_id} expired")

        self._set_state(request_id, "running", CompletionState.UNKNOWN)
        adapter_name = (adapter or req.resolved_recipient).lower()
        capture = CaptureInput(
            adapter=adapter_name,
            stdout=stdout,
            stderr=stderr,
            returncode=returncode,
            events=events,
            raw_bytes=raw_bytes,
            session_id=session_id,
            transport_metadata={"request_id": request_id},
        )
        raw = raw_bytes
        if raw is None:
            raw = "\n".join(
                [stdout or "", "---stderr---", stderr or "", f"---rc={returncode}---"]
            ).encode("utf-8")
        art = self.store.store_bytes(
            raw,
            producer=f"adapter:{adapter_name}",
            retention_class="raw-capture",
            mime_type="application/x-ndjson" if events or stdout.lstrip().startswith("{") else "text/plain",
            logical_filename=f"{request_id}.capture",
        )
        envelope = conform(capture)
        # Rebind envelope to the real artifact id/digest from the store.
        envelope = ResponseEnvelope(
            segments=envelope.segments,
            completion_state=envelope.completion_state,
            provider_stop_reason=envelope.provider_stop_reason,
            terminal_event_observed=envelope.terminal_event_observed,
            process_returncode=envelope.process_returncode,
            transport_metadata={**envelope.transport_metadata, "artifact_store_id": art.artifact_id},
            raw_capture_artifact_id=art.artifact_id,
            raw_capture_sha256=art.sha256,
            session_id=envelope.session_id or session_id,
            token_metadata=envelope.token_metadata,
            tool_call_metadata=envelope.tool_call_metadata,
        )
        self.store.reference(req.request_message_id, art.artifact_id, relation="raw_capture")

        request_state = self._map_completion_to_request_state(envelope.completion_state)
        now_s = _iso(_utc_now())
        row = self._conn.execute(
            "SELECT invocation_spec_json FROM requests WHERE request_id = ?",
            (request_id,),
        ).fetchone()
        spec: dict[str, Any] = {}
        if row and row[0]:
            try:
                loaded = json.loads(str(row[0]))
                if isinstance(loaded, dict):
                    spec = loaded
            except json.JSONDecodeError:
                spec = {}
        spec["raw_capture_artifact_id"] = art.artifact_id
        spec["completion_state"] = envelope.completion_state.value
        self._conn.execute(
            """UPDATE requests SET state = ?, completion_state = ?, updated_at = ?,
               invocation_spec_json = ?
               WHERE request_id = ?""",
            (
                request_state,
                envelope.completion_state.value,
                now_s,
                json.dumps(spec, sort_keys=True),
                request_id,
            ),
        )
        # Reply message when we have text (even incomplete).
        if envelope.response_text:
            reply_id = new_id("message")
            preview = envelope.response_text[:500]
            self._conn.execute(
                """INSERT INTO comms_messages(
                    message_id, conversation_id, in_reply_to, kind, sender, recipient,
                    body_inline, body_artifact_id, content_sha256, metadata_json, created_at
                ) VALUES (
                    ?,
                    (SELECT conversation_id FROM comms_messages WHERE message_id = ?),
                    ?, 'reply', ?, ?, ?, ?, ?, ?, ?
                )""",
                (
                    reply_id,
                    req.request_message_id,
                    req.request_message_id,
                    req.resolved_recipient,
                    "request-executor",
                    preview,
                    art.artifact_id,
                    art.sha256,
                    json.dumps({"completion_state": envelope.completion_state.value}, sort_keys=True),
                    now_s,
                ),
            )
            self.store.reference(reply_id, art.artifact_id, relation="body")
        self._conn.commit()
        record = self.get_request(request_id)
        return RequestRecord(
            request_id=record.request_id,
            request_message_id=record.request_message_id,
            requested_recipient=record.requested_recipient,
            resolved_recipient=record.resolved_recipient,
            state=record.state,
            expires_at=record.expires_at,
            completion_state=record.completion_state,
            created_at=record.created_at,
            updated_at=record.updated_at,
            envelope=envelope,
            raw_capture_artifact_id=art.artifact_id,
        )

    @staticmethod
    def _map_completion_to_request_state(state: CompletionState) -> str:
        if state is CompletionState.COMPLETE:
            return "complete"
        if state is CompletionState.FAILED:
            return "failed"
        if state in {
            CompletionState.LENGTH_LIMITED,
            CompletionState.TRANSPORT_INCOMPLETE,
            CompletionState.UNKNOWN,
        }:
            return "incomplete"
        return "incomplete"

    def _set_state(self, request_id: str, state: str, completion: CompletionState) -> None:
        if state not in REQUEST_STATES:
            raise RequestExecutorError(f"invalid request state: {state}")
        self._conn.execute(
            "UPDATE requests SET state = ?, completion_state = ?, updated_at = ? WHERE request_id = ?",
            (state, completion.value, _iso(_utc_now()), request_id),
        )
        self._conn.commit()


def open_executor(root: Path | None = None) -> RequestExecutor:
    """Factory used by CLI/tests."""
    return RequestExecutor(root=root)
