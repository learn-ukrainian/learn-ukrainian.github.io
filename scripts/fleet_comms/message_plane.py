"""Message-plane cutover path (Fleet Comms PR-E / #5512).

Routes ask/reply work through the canonical request plane **when enabled**,
while legacy bridge tables remain the default writer until operator cutover.

Modes (env ``FLEET_COMMS_MESSAGE_PLANE`` or constructor):

- ``off`` (default) — no-op; legacy bridge unchanged
- ``shadow`` — create durable requests + capture completion; never change
  legacy status; emit parity telemetry only
- ``dual_write`` — same as shadow, and only project ``replied`` to legacy
  when completion is proven ``complete`` (incomplete never becomes replied)

No silent global flip. Background workers may reload by ``request_id`` only.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from scripts.fleet_comms.contracts import CompletionState
from scripts.fleet_comms.request_executor import RequestExecutor, RequestRecord

PlaneMode = Literal["off", "shadow", "dual_write"]
ENV_MODE = "FLEET_COMMS_MESSAGE_PLANE"
# Max centrally configured continuation segments for length_limited (Sol).
MAX_CONTINUATIONS = 2


def resolve_plane_mode(raw: str | None = None) -> PlaneMode:
    value = (raw if raw is not None else os.environ.get(ENV_MODE, "off")).strip().lower()
    if value in {"", "0", "false", "off", "disabled"}:
        return "off"
    if value in {"shadow", "dual_write", "off"}:
        return value  # type: ignore[return-value]
    if value in {"dual-write", "dualwrite"}:
        return "dual_write"
    raise ValueError(f"invalid FLEET_COMMS_MESSAGE_PLANE={value!r} (use off|shadow|dual_write)")


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def invocation_digest(
    *,
    recipient: str,
    body: str,
    model: str | None,
    mode: str | None,
    cwd: str | None,
    attachments: tuple[str, ...] = (),
) -> str:
    """Stable digest for foreground/background parity proofs (Sol PR-E/D)."""
    payload = {
        "recipient": recipient,
        "body_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "model": model or "",
        "mode": mode or "",
        "cwd": cwd or "",
        "attachments": list(attachments),
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True, slots=True)
class ParityReport:
    request_id: str
    legacy_message_id: int | None
    request_state: str
    completion_state: str
    legacy_status: str | None
    parity_ok: bool
    notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "legacy_message_id": self.legacy_message_id,
            "request_state": self.request_state,
            "completion_state": self.completion_state,
            "legacy_status": self.legacy_status,
            "parity_ok": self.parity_ok,
            "notes": list(self.notes),
        }


@dataclass(frozen=True, slots=True)
class PlaneResult:
    mode: PlaneMode
    request: RequestRecord | None
    parity: ParityReport | None
    projected_legacy_replied: bool
    continuation_used: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "request": self.request.to_dict() if self.request else None,
            "parity": self.parity.to_dict() if self.parity else None,
            "projected_legacy_replied": self.projected_legacy_replied,
            "continuation_used": self.continuation_used,
        }


class MessagePlane:
    """Canonical message plane with optional legacy projection."""

    def __init__(
        self,
        *,
        mode: PlaneMode | str | None = None,
        executor: RequestExecutor | None = None,
        root: Path | None = None,
        legacy_db: Path | None = None,
        telemetry_path: Path | None = None,
    ) -> None:
        if mode is None:
            self.mode = resolve_plane_mode(None)
        elif isinstance(mode, str):
            self.mode = resolve_plane_mode(mode)
        else:
            self.mode = mode
        self.executor = executor or RequestExecutor(root=root)
        self.legacy_db = legacy_db
        self.telemetry_path = telemetry_path
        self._owns_executor = executor is None

    def close(self) -> None:
        if self._owns_executor:
            self.executor.close()

    def __enter__(self) -> MessagePlane:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    @property
    def enabled(self) -> bool:
        return self.mode != "off"

    def open_ask(
        self,
        *,
        recipient: str,
        body: str,
        sender: str = "message-plane",
        legacy_message_id: int | None = None,
        task_id: str | None = None,
        model: str | None = None,
        transport_mode: str | None = None,
        cwd: str | None = None,
        attachments: tuple[str, ...] = (),
        metadata: dict[str, Any] | None = None,
    ) -> RequestRecord | None:
        """Create a durable request for an ask (shadow/dual_write only)."""
        if not self.enabled:
            return None
        dig = invocation_digest(
            recipient=recipient,
            body=body,
            model=model,
            mode=transport_mode,
            cwd=cwd,
            attachments=attachments,
        )
        meta = {
            "plane_mode": self.mode,
            "legacy_message_id": legacy_message_id,
            "task_id": task_id,
            "model": model,
            "transport_mode": transport_mode,
            "cwd": cwd,
            "attachments": list(attachments),
            "invocation_digest": dig,
            "continuation_count": 0,
            **(metadata or {}),
        }
        return self.executor.create_request(
            recipient=recipient,
            body=body,
            sender=sender,
            metadata=meta,
        )

    def complete_ask(
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
        legacy_message_id: int | None = None,
        legacy_status_writer: Any | None = None,
    ) -> PlaneResult:
        """Run capture conformance and optionally project to legacy.

        ``legacy_status_writer`` if provided is ``callable(message_id, reply_id)``
        used only in dual_write when completion is proven complete.
        """
        if not self.enabled:
            return PlaneResult(
                mode=self.mode,
                request=None,
                parity=None,
                projected_legacy_replied=False,
                continuation_used=0,
            )

        record = self.executor.execute_capture(
            request_id,
            adapter=adapter,
            stdout=stdout,
            stderr=stderr,
            returncode=returncode,
            events=events,
            raw_bytes=raw_bytes,
            session_id=session_id,
        )
        continuation_used = 0
        # Bounded continuation for length_limited (record-only; caller may re-invoke).
        if (
            record.envelope is not None
            and record.envelope.completion_state is CompletionState.LENGTH_LIMITED
        ):
            continuation_used = self._bump_continuation(request_id)

        projected = False
        if (
            self.mode == "dual_write"
            and record.state == "complete"
            and record.completion_state == CompletionState.COMPLETE.value
            and legacy_message_id is not None
            and legacy_status_writer is not None
        ):
            # Projection must not invent a reply id; writer supplies linkage.
            legacy_status_writer(legacy_message_id, record.request_id)
            projected = True

        # incomplete / failed / unknown never project as replied
        if (
            self.mode == "dual_write"
            and record.state != "complete"
            and legacy_message_id is not None
        ):
            self._emit_telemetry(
                {
                    "event": "plane_refuse_legacy_replied",
                    "request_id": request_id,
                    "legacy_message_id": legacy_message_id,
                    "request_state": record.state,
                    "completion_state": record.completion_state,
                    "ts": _utc_now(),
                }
            )

        parity = self.compute_parity(
            request_id,
            legacy_message_id=legacy_message_id,
            legacy_status=self._read_legacy_status(legacy_message_id),
        )
        self._emit_telemetry(
            {
                "event": "plane_complete",
                "request_id": request_id,
                "mode": self.mode,
                "request_state": record.state,
                "completion_state": record.completion_state,
                "parity_ok": parity.parity_ok if parity else None,
                "projected_legacy_replied": projected,
                "continuation_used": continuation_used,
                "ts": _utc_now(),
            }
        )
        return PlaneResult(
            mode=self.mode,
            request=record,
            parity=parity,
            projected_legacy_replied=projected,
            continuation_used=continuation_used,
        )

    def load_request(self, request_id: str) -> RequestRecord:
        """Background worker entry: reload durable request by id only."""
        return self.executor.get_request(request_id)

    def compute_parity(
        self,
        request_id: str,
        *,
        legacy_message_id: int | None = None,
        legacy_status: str | None = None,
    ) -> ParityReport:
        req = self.executor.get_request(request_id)
        notes: list[str] = []
        parity_ok = True

        if req.state == "complete" and req.completion_state != CompletionState.COMPLETE.value:
            parity_ok = False
            notes.append("complete_state_mismatch")

        if legacy_status is not None:
            if legacy_status.startswith("replied:"):
                if req.state != "complete" or req.completion_state != CompletionState.COMPLETE.value:
                    parity_ok = False
                    notes.append("legacy_replied_but_request_not_complete")
            elif req.state == "complete" and req.completion_state == CompletionState.COMPLETE.value:
                if self.mode == "dual_write":
                    notes.append("legacy_not_yet_projected")
                    # Not a hard fail in shadow; dual_write may lag one tick
                    if self.mode == "shadow":
                        pass
            elif req.state in {"incomplete", "failed"} and legacy_status.startswith("replied:"):
                parity_ok = False
                notes.append("incomplete_classified_as_replied")

        if req.completion_state in {
            CompletionState.UNKNOWN.value,
            CompletionState.TRANSPORT_INCOMPLETE.value,
            CompletionState.LENGTH_LIMITED.value,
        } and legacy_status and legacy_status.startswith("replied:"):
            parity_ok = False
            notes.append("unproven_completion_marked_replied")

        return ParityReport(
            request_id=request_id,
            legacy_message_id=legacy_message_id,
            request_state=req.state,
            completion_state=req.completion_state,
            legacy_status=legacy_status,
            parity_ok=parity_ok,
            notes=tuple(notes),
        )

    def may_mark_legacy_replied(self, request_id: str | None) -> bool:
        """Gate for dual_write: only proven complete may become legacy replied."""
        if self.mode != "dual_write" or not request_id:
            # shadow/off: plane does not control legacy; callers keep old behavior
            return self.mode != "dual_write"
        req = self.executor.get_request(request_id)
        return (
            req.state == "complete"
            and req.completion_state == CompletionState.COMPLETE.value
        )

    def _bump_continuation(self, request_id: str) -> int:
        row = self.executor.store.connection.execute(
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
        count = int(spec.get("continuation_count") or 0)
        if count >= MAX_CONTINUATIONS:
            return count
        count += 1
        spec["continuation_count"] = count
        spec["last_continuation_at"] = _utc_now()
        self.executor.store.connection.execute(
            "UPDATE requests SET invocation_spec_json = ?, updated_at = ? WHERE request_id = ?",
            (json.dumps(spec, sort_keys=True), _utc_now(), request_id),
        )
        self.executor.store.connection.commit()
        return count

    def _read_legacy_status(self, message_id: int | None) -> str | None:
        if message_id is None or self.legacy_db is None:
            return None
        path = Path(self.legacy_db)
        if not path.is_file():
            return None
        try:
            conn = sqlite3.connect(str(path))
            try:
                row = conn.execute(
                    "SELECT status FROM messages WHERE id = ?", (message_id,)
                ).fetchone()
                return str(row[0]) if row and row[0] is not None else None
            finally:
                conn.close()
        except sqlite3.Error:
            return None

    def _emit_telemetry(self, event: dict[str, Any]) -> None:
        if self.telemetry_path is None:
            return
        path = Path(self.telemetry_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(event, sort_keys=True) + "\n"
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line)


def open_message_plane(
    *,
    mode: str | None = None,
    root: Path | None = None,
    legacy_db: Path | None = None,
    telemetry_path: Path | None = None,
) -> MessagePlane:
    return MessagePlane(
        mode=mode,
        root=root,
        legacy_db=legacy_db,
        telemetry_path=telemetry_path,
    )
