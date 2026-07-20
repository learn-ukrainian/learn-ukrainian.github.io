"""Adapter completion-conformance harness (Fleet Comms PR-B1/B2 / #5512).

Maps harness-specific captures into a typed ``ResponseEnvelope``. Adapters may
only emit ``complete`` when their documented terminal contract is observed.
Exit 0 + nonempty text alone is never enough.

B1 primary adapters: codex, claude, agy.
B2 remaining adapters: grok, kimi, cursor, hermes (+ hermes-*), opencode —
each implements a real harness-specific terminal contract. Missing terminal
evidence yields ``unknown`` (formal-review ineligible).
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from scripts.fleet_comms.contracts import AssistantSegment, CompletionState, ResponseEnvelope

PRIMARY_ADAPTERS = frozenset({"codex", "claude", "agy"})
REMAINING_ADAPTERS = frozenset(
    {
        "grok",
        "grok-build",
        "grok-hermes",
        "kimi",
        "cursor",
        "hermes",
        "hermes-grok",
        "hermes-qwen",
        "hermes-deepseek",
        "opencode",
    }
)

_LENGTH_REASONS = frozenset(
    {
        "length",
        "max_tokens",
        "max_output_tokens",
        "maxtokens",
        "max_token",
        "length_limit",
        "output_length",
    }
)
_ERROR_REASONS = frozenset(
    {
        "error",
        "failed",
        "failure",
        "aborted",
        "abort",
        "cancelled",
        "canceled",
        "refused",
    }
)
_HERMES_HTTP_ERROR_RE = re.compile(r"^HTTP\s+[45]\d{2}\b")


@dataclass(frozen=True, slots=True)
class CaptureInput:
    """Raw transport capture fed into the conformance harness."""

    adapter: str
    stdout: str = ""
    stderr: str = ""
    returncode: int | None = None
    events: tuple[dict[str, Any], ...] = ()
    raw_bytes: bytes | None = None
    session_id: str | None = None
    transport_metadata: Mapping[str, Any] | None = None


def _parse_jsonl(text: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            events.append(payload)
    return events


def _ordered_segments(texts: Iterable[str]) -> tuple[AssistantSegment, ...]:
    segments: list[AssistantSegment] = []
    for index, text in enumerate(texts):
        if text is None:
            continue
        value = str(text)
        if not value:
            continue
        segments.append(AssistantSegment(text=value, sequence=index))
    return tuple(segments)


def _raw_hash(capture: CaptureInput) -> tuple[str | None, str | None]:
    raw = capture.raw_bytes
    if raw is None:
        # Deterministic capture of the inputs we observed.
        raw = "\n".join(
            [
                capture.stdout or "",
                "---stderr---",
                capture.stderr or "",
                f"---rc={capture.returncode}---",
            ]
        ).encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    # Artifact ID is content-addressed preview; store layer assigns real IDs.
    return f"artifact_raw_{digest[:16]}", digest


def _envelope(
    *,
    segments: Sequence[AssistantSegment],
    state: CompletionState,
    terminal: bool,
    capture: CaptureInput,
    stop_reason: str | None,
    extra_meta: Mapping[str, Any] | None = None,
) -> ResponseEnvelope:
    art_id, digest = _raw_hash(capture)
    meta = dict(capture.transport_metadata or {})
    meta["adapter"] = capture.adapter
    if extra_meta:
        meta.update(extra_meta)
    return ResponseEnvelope(
        segments=tuple(segments),
        completion_state=state,
        provider_stop_reason=stop_reason,
        terminal_event_observed=terminal,
        process_returncode=capture.returncode,
        transport_metadata=meta,
        raw_capture_artifact_id=art_id,
        raw_capture_sha256=digest,
        session_id=capture.session_id,
    )


def conform_codex(capture: CaptureInput) -> ResponseEnvelope:
    """Codex: terminal proof is a ``task_complete`` event (or equivalent).

    Segments come from ordered ``agent_message`` / ``message`` assistant texts.
    ``reason=length`` maps to length_limited even when text is present.
    """
    events = list(capture.events) if capture.events else _parse_jsonl(capture.stdout)
    texts: list[str] = []
    stop_reason: str | None = None
    terminal = False
    session_id = capture.session_id

    for event in events:
        etype = str(event.get("type") or event.get("event") or "")
        if etype in {"agent_message", "message", "item.completed"}:
            item = event.get("item") if isinstance(event.get("item"), dict) else event
            text = item.get("text") if isinstance(item, dict) else None
            if text is None and isinstance(item, dict):
                content = item.get("content")
                if isinstance(content, str):
                    text = content
                elif isinstance(content, list):
                    parts = [
                        str(part.get("text", ""))
                        for part in content
                        if isinstance(part, dict) and part.get("type") in {None, "text", "output_text"}
                    ]
                    text = "".join(parts)
            if isinstance(text, str) and text:
                texts.append(text)
        if etype == "task_complete":
            terminal = True
            stop_reason = str(event.get("reason") or event.get("stop_reason") or "task_complete")
        if etype in {"turn.completed", "response.completed"}:
            # Weaker signal — not terminal alone without task_complete.
            stop_reason = stop_reason or str(event.get("reason") or etype)
        reason = event.get("reason") or event.get("stop_reason")
        if isinstance(reason, str) and reason in {"length", "max_tokens", "max_output_tokens"}:
            stop_reason = reason
        sid = event.get("session_id") or event.get("thread_id")
        if isinstance(sid, str) and sid:
            session_id = sid

    segments = _ordered_segments(texts)
    if not segments and capture.stdout.strip() and not events:
        # Plain text fallback — never complete without terminal evidence.
        segments = _ordered_segments([capture.stdout.strip()])

    length_limited = stop_reason in {"length", "max_tokens", "max_output_tokens"}
    if capture.returncode not in (None, 0) and not terminal:
        state = CompletionState.FAILED if not segments else CompletionState.TRANSPORT_INCOMPLETE
        return _envelope(
            segments=segments,
            state=state,
            terminal=False,
            capture=capture,
            stop_reason=stop_reason or f"rc={capture.returncode}",
            extra_meta={"session_id_resolved": session_id},
        )
    if length_limited:
        return _envelope(
            segments=segments,
            state=CompletionState.LENGTH_LIMITED,
            terminal=terminal,
            capture=CaptureInput(
                adapter=capture.adapter,
                stdout=capture.stdout,
                stderr=capture.stderr,
                returncode=capture.returncode,
                events=tuple(events),
                raw_bytes=capture.raw_bytes,
                session_id=session_id,
                transport_metadata=capture.transport_metadata,
            ),
            stop_reason=stop_reason,
        )
    if terminal:
        return _envelope(
            segments=segments,
            state=CompletionState.COMPLETE,
            terminal=True,
            capture=CaptureInput(
                adapter=capture.adapter,
                stdout=capture.stdout,
                stderr=capture.stderr,
                returncode=capture.returncode,
                events=tuple(events),
                raw_bytes=capture.raw_bytes,
                session_id=session_id,
                transport_metadata=capture.transport_metadata,
            ),
            stop_reason=stop_reason or "task_complete",
        )
    if segments and capture.returncode in (None, 0):
        # Nonempty + exit 0 without terminal → unknown (never complete).
        return _envelope(
            segments=segments,
            state=CompletionState.UNKNOWN,
            terminal=False,
            capture=CaptureInput(
                adapter=capture.adapter,
                stdout=capture.stdout,
                stderr=capture.stderr,
                returncode=capture.returncode,
                events=tuple(events),
                raw_bytes=capture.raw_bytes,
                session_id=session_id,
                transport_metadata=capture.transport_metadata,
            ),
            stop_reason=stop_reason or "missing_terminal_event",
        )
    if not segments:
        return _envelope(
            segments=(),
            state=CompletionState.TRANSPORT_INCOMPLETE,
            terminal=False,
            capture=capture,
            stop_reason=stop_reason or "empty_capture",
        )
    return _envelope(
        segments=segments,
        state=CompletionState.UNKNOWN,
        terminal=False,
        capture=capture,
        stop_reason=stop_reason,
    )


def conform_claude(capture: CaptureInput) -> ResponseEnvelope:
    """Claude stream-json: terminal proof is a final ``result`` event type.

    Ordered assistant text segments are retained from every text item, not only
    the last event (Sol multi-turn NDJSON requirement).
    """
    events = list(capture.events) if capture.events else _parse_jsonl(capture.stdout)
    texts: list[str] = []
    stop_reason: str | None = None
    terminal = False
    session_id = capture.session_id

    for event in events:
        etype = str(event.get("type") or "")
        sid = event.get("session_id") or event.get("sessionId")
        if isinstance(sid, str) and sid:
            session_id = sid
        if etype in {"assistant", "content_block_delta", "text"}:
            content = event.get("content") or event.get("message", {}).get("content") if isinstance(event.get("message"), dict) else event.get("content")
            if isinstance(content, str) and content:
                texts.append(content)
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text" and isinstance(part.get("text"), str):
                        texts.append(part["text"])
            delta = event.get("delta")
            if isinstance(delta, dict) and isinstance(delta.get("text"), str):
                texts.append(delta["text"])
        if etype == "result":
            terminal = True
            result_text = event.get("result")
            if isinstance(result_text, str) and result_text.strip():
                texts.append(result_text.strip())
            stop_reason = str(event.get("subtype") or event.get("stop_reason") or "result")
            if event.get("is_error") is True:
                stop_reason = "error"
        reason = event.get("stop_reason") or event.get("reason")
        if isinstance(reason, str) and reason in {"max_tokens", "length"}:
            stop_reason = reason

    segments = _ordered_segments(texts)
    if not segments and capture.stdout.strip() and not events:
        segments = _ordered_segments([capture.stdout.strip()])

    length_limited = stop_reason in {"max_tokens", "length"}
    if capture.returncode not in (None, 0) and not terminal:
        state = CompletionState.FAILED if not segments else CompletionState.TRANSPORT_INCOMPLETE
        return _envelope(
            segments=segments,
            state=state,
            terminal=False,
            capture=capture,
            stop_reason=stop_reason or f"rc={capture.returncode}",
        )
    if length_limited:
        return _envelope(
            segments=segments,
            state=CompletionState.LENGTH_LIMITED,
            terminal=terminal,
            capture=CaptureInput(
                adapter=capture.adapter,
                stdout=capture.stdout,
                stderr=capture.stderr,
                returncode=capture.returncode,
                events=tuple(events),
                raw_bytes=capture.raw_bytes,
                session_id=session_id,
                transport_metadata=capture.transport_metadata,
            ),
            stop_reason=stop_reason,
        )
    if terminal and stop_reason != "error":
        return _envelope(
            segments=segments,
            state=CompletionState.COMPLETE,
            terminal=True,
            capture=CaptureInput(
                adapter=capture.adapter,
                stdout=capture.stdout,
                stderr=capture.stderr,
                returncode=capture.returncode,
                events=tuple(events),
                raw_bytes=capture.raw_bytes,
                session_id=session_id,
                transport_metadata=capture.transport_metadata,
            ),
            stop_reason=stop_reason or "result",
        )
    if terminal and stop_reason == "error":
        return _envelope(
            segments=segments,
            state=CompletionState.FAILED,
            terminal=True,
            capture=capture,
            stop_reason="error",
        )
    if segments and capture.returncode in (None, 0):
        return _envelope(
            segments=segments,
            state=CompletionState.UNKNOWN,
            terminal=False,
            capture=CaptureInput(
                adapter=capture.adapter,
                stdout=capture.stdout,
                stderr=capture.stderr,
                returncode=capture.returncode,
                events=tuple(events),
                raw_bytes=capture.raw_bytes,
                session_id=session_id,
                transport_metadata=capture.transport_metadata,
            ),
            stop_reason=stop_reason or "missing_terminal_event",
        )
    if not segments:
        return _envelope(
            segments=(),
            state=CompletionState.TRANSPORT_INCOMPLETE,
            terminal=False,
            capture=capture,
            stop_reason=stop_reason or "empty_capture",
        )
    return _envelope(
        segments=segments,
        state=CompletionState.UNKNOWN,
        terminal=False,
        capture=capture,
        stop_reason=stop_reason,
    )


def conform_agy(capture: CaptureInput) -> ResponseEnvelope:
    """AGY bridge: terminal proof is a final RESULT marker / done event.

    Multi-line RESULT bodies are ordered segments; missing RESULT → unknown.
    """
    events = list(capture.events) if capture.events else _parse_jsonl(capture.stdout)
    texts: list[str] = []
    stop_reason: str | None = None
    terminal = False
    session_id = capture.session_id

    for event in events:
        etype = str(event.get("type") or event.get("event") or "")
        if etype in {"assistant", "message", "text"}:
            text = event.get("text") or event.get("content") or event.get("result")
            if isinstance(text, str) and text:
                texts.append(text)
        if etype in {"result", "done", "RESULT", "task_complete"}:
            terminal = True
            stop_reason = str(event.get("reason") or etype)
            body = event.get("result") or event.get("content") or event.get("text")
            if isinstance(body, str) and body.strip():
                texts.append(body.strip())
        reason = event.get("stop_reason") or event.get("reason")
        if isinstance(reason, str) and reason in {"length", "max_tokens"}:
            stop_reason = reason
        sid = event.get("session_id")
        if isinstance(sid, str) and sid:
            session_id = sid

    if not events and capture.stdout:
        # Text RESULT: prefix protocol used by some bridge paths.
        lines = capture.stdout.splitlines()
        collecting = False
        body: list[str] = []
        for line in lines:
            if line.lstrip().startswith("RESULT:"):
                collecting = True
                terminal = True
                stop_reason = "RESULT"
                rest = line.split("RESULT:", 1)[1].strip()
                if rest:
                    body.append(rest)
                continue
            if collecting:
                body.append(line)
        if body:
            texts.append("\n".join(body).strip())

    segments = _ordered_segments(texts)
    length_limited = stop_reason in {"length", "max_tokens"}
    if capture.returncode not in (None, 0) and not terminal:
        state = CompletionState.FAILED if not segments else CompletionState.TRANSPORT_INCOMPLETE
        return _envelope(
            segments=segments,
            state=state,
            terminal=False,
            capture=capture,
            stop_reason=stop_reason or f"rc={capture.returncode}",
        )
    if length_limited:
        return _envelope(
            segments=segments,
            state=CompletionState.LENGTH_LIMITED,
            terminal=terminal,
            capture=CaptureInput(
                adapter=capture.adapter,
                stdout=capture.stdout,
                stderr=capture.stderr,
                returncode=capture.returncode,
                events=tuple(events),
                raw_bytes=capture.raw_bytes,
                session_id=session_id,
                transport_metadata=capture.transport_metadata,
            ),
            stop_reason=stop_reason,
        )
    if terminal:
        return _envelope(
            segments=segments,
            state=CompletionState.COMPLETE,
            terminal=True,
            capture=CaptureInput(
                adapter=capture.adapter,
                stdout=capture.stdout,
                stderr=capture.stderr,
                returncode=capture.returncode,
                events=tuple(events),
                raw_bytes=capture.raw_bytes,
                session_id=session_id,
                transport_metadata=capture.transport_metadata,
            ),
            stop_reason=stop_reason or "result",
        )
    if segments and capture.returncode in (None, 0):
        return _envelope(
            segments=segments,
            state=CompletionState.UNKNOWN,
            terminal=False,
            capture=CaptureInput(
                adapter=capture.adapter,
                stdout=capture.stdout,
                stderr=capture.stderr,
                returncode=capture.returncode,
                events=tuple(events),
                raw_bytes=capture.raw_bytes,
                session_id=session_id,
                transport_metadata=capture.transport_metadata,
            ),
            stop_reason=stop_reason or "missing_terminal_event",
        )
    if not segments:
        return _envelope(
            segments=(),
            state=CompletionState.TRANSPORT_INCOMPLETE,
            terminal=False,
            capture=capture,
            stop_reason=stop_reason or "empty_capture",
        )
    return _envelope(
        segments=segments,
        state=CompletionState.UNKNOWN,
        terminal=False,
        capture=capture,
        stop_reason=stop_reason,
    )


def _is_length_reason(reason: str | None) -> bool:
    if not reason:
        return False
    normalized = reason.strip().lower().replace("-", "_")
    return normalized in _LENGTH_REASONS


def _is_error_reason(reason: str | None) -> bool:
    if not reason:
        return False
    normalized = reason.strip().lower().replace("-", "_")
    return normalized in _ERROR_REASONS


def _with_session(
    capture: CaptureInput,
    *,
    events: Sequence[dict[str, Any]] | None = None,
    session_id: str | None = None,
) -> CaptureInput:
    return CaptureInput(
        adapter=capture.adapter,
        stdout=capture.stdout,
        stderr=capture.stderr,
        returncode=capture.returncode,
        events=tuple(events) if events is not None else capture.events,
        raw_bytes=capture.raw_bytes,
        session_id=session_id if session_id is not None else capture.session_id,
        transport_metadata=capture.transport_metadata,
    )


def _finish(
    *,
    segments: Sequence[AssistantSegment],
    terminal: bool,
    stop_reason: str | None,
    capture: CaptureInput,
    events: Sequence[dict[str, Any]] | None = None,
    session_id: str | None = None,
    extra_meta: Mapping[str, Any] | None = None,
    error_terminal: bool = False,
) -> ResponseEnvelope:
    """Shared completion-state matrix used by B1/B2 conformers."""
    bound = _with_session(capture, events=events, session_id=session_id)
    length_limited = _is_length_reason(stop_reason)
    if capture.returncode not in (None, 0) and not terminal:
        state = CompletionState.FAILED if not segments else CompletionState.TRANSPORT_INCOMPLETE
        return _envelope(
            segments=segments,
            state=state,
            terminal=False,
            capture=bound,
            stop_reason=stop_reason or f"rc={capture.returncode}",
            extra_meta=extra_meta,
        )
    if length_limited:
        return _envelope(
            segments=segments,
            state=CompletionState.LENGTH_LIMITED,
            terminal=terminal,
            capture=bound,
            stop_reason=stop_reason,
            extra_meta=extra_meta,
        )
    if terminal and (error_terminal or _is_error_reason(stop_reason)):
        return _envelope(
            segments=segments,
            state=CompletionState.FAILED,
            terminal=True,
            capture=bound,
            stop_reason=stop_reason or "error",
            extra_meta=extra_meta,
        )
    if terminal:
        return _envelope(
            segments=segments,
            state=CompletionState.COMPLETE,
            terminal=True,
            capture=bound,
            stop_reason=stop_reason or "terminal",
            extra_meta=extra_meta,
        )
    if segments and capture.returncode in (None, 0):
        return _envelope(
            segments=segments,
            state=CompletionState.UNKNOWN,
            terminal=False,
            capture=bound,
            stop_reason=stop_reason or "missing_terminal_event",
            extra_meta=extra_meta,
        )
    if not segments:
        return _envelope(
            segments=(),
            state=CompletionState.TRANSPORT_INCOMPLETE,
            terminal=False,
            capture=bound,
            stop_reason=stop_reason or "empty_capture",
            extra_meta=extra_meta,
        )
    return _envelope(
        segments=segments,
        state=CompletionState.UNKNOWN,
        terminal=False,
        capture=bound,
        stop_reason=stop_reason,
        extra_meta=extra_meta,
    )


def _assistant_text_from_content(value: Any) -> str:
    """Extract assistant prose from string / content-block shapes."""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, str) and item:
                parts.append(item)
            elif isinstance(item, dict) and item.get("type") in {None, "text", "output_text"}:
                text = item.get("text")
                if isinstance(text, str) and text:
                    parts.append(text)
        return "".join(parts)
    return ""


def _parse_json_object_tolerant(stdout: str) -> dict[str, Any] | None:
    """Parse a single JSON object, tolerating leading/trailing log noise."""
    text = (stdout or "").strip()
    if not text:
        return None
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        try:
            value = json.loads(text[start : end + 1])
            return value if isinstance(value, dict) else None
        except json.JSONDecodeError:
            return None
    return None


def conform_grok(capture: CaptureInput) -> ResponseEnvelope:
    """Native grok headless JSON: terminal proof is a present ``stopReason``.

    Documented shape (``GrokBuildAdapter``): ``{text, stopReason, sessionId}``.
    Plain-text / JSON without ``stopReason`` is never ``complete``.
    """
    events = list(capture.events) if capture.events else _parse_jsonl(capture.stdout)
    texts: list[str] = []
    stop_reason: str | None = None
    terminal = False
    session_id = capture.session_id

    def absorb_object(obj: Mapping[str, Any]) -> None:
        nonlocal stop_reason, terminal, session_id
        text = obj.get("text")
        if isinstance(text, str) and text.strip():
            texts.append(text.strip())
        # Prefer documented camelCase; accept snake_case drift.
        if "stopReason" in obj or "stop_reason" in obj:
            terminal = True
            raw = obj.get("stopReason", obj.get("stop_reason"))
            if raw is not None:
                stop_reason = str(raw)
        sid = obj.get("sessionId") or obj.get("session_id")
        if isinstance(sid, str) and sid:
            session_id = sid

    if events:
        for event in events:
            absorb_object(event)
    else:
        obj = _parse_json_object_tolerant(capture.stdout)
        if obj is not None:
            absorb_object(obj)
        elif capture.stdout.strip():
            # Plain-text fallback path used by the adapter — no terminal proof.
            texts.append(capture.stdout.strip())

    # Normalize: grok JSON text is stripped in the adapter on success.
    segments = _ordered_segments(texts)
    return _finish(
        segments=segments,
        terminal=terminal,
        stop_reason=stop_reason,
        capture=capture,
        events=events,
        session_id=session_id,
        extra_meta={"terminal_contract": "stopReason"},
    )


def conform_kimi(capture: CaptureInput) -> ResponseEnvelope:
    """Kimi stream-json: terminal proof is a completion meta event.

    Documented terminal: ``role=meta`` + ``type=session.resume_hint`` (emitted
    after a finished run; adapter already keys session resume on it). Optional
    completion signals: meta ``status`` with a finished state, or explicit
    ``result``/``done`` event types if the CLI adds them.
    """
    events = list(capture.events) if capture.events else _parse_jsonl(capture.stdout)
    texts: list[str] = []
    stop_reason: str | None = None
    terminal = False
    session_id = capture.session_id

    for event in events:
        role = str(event.get("role") or "")
        etype = str(event.get("type") or event.get("event") or "")
        if role == "assistant":
            content = _assistant_text_from_content(event.get("content"))
            if content:
                texts.append(content)
            reason = event.get("stop_reason") or event.get("finish_reason") or event.get("reason")
            if isinstance(reason, str) and reason:
                stop_reason = reason
                if _is_length_reason(reason) or _is_error_reason(reason):
                    # Explicit stop/finish reason on an assistant turn is terminal.
                    terminal = True
        if role == "meta" and etype == "session.resume_hint":
            terminal = True
            stop_reason = stop_reason or "session.resume_hint"
            sid = event.get("session_id")
            if isinstance(sid, str) and sid.strip():
                session_id = sid.strip()
        if role == "meta" and etype == "status":
            state = str(event.get("state") or "").strip().lower()
            if state in {"done", "completed", "finished", "idle", "ready"}:
                terminal = True
                stop_reason = stop_reason or f"status:{state}"
            elif state in {"error", "failed"}:
                terminal = True
                stop_reason = "error"
        if etype in {"result", "done", "task_complete", "RESULT"}:
            terminal = True
            stop_reason = stop_reason or etype
            body = event.get("result") or event.get("content") or event.get("text")
            if isinstance(body, str) and body.strip():
                texts.append(body.strip())
        reason = event.get("stop_reason") or event.get("finish_reason") or event.get("reason")
        if isinstance(reason, str) and _is_length_reason(reason):
            stop_reason = reason
            terminal = True
        sid = event.get("session_id")
        if isinstance(sid, str) and sid.strip() and role == "meta":
            session_id = sid.strip()

    segments = _ordered_segments(texts)
    if not segments and capture.stdout.strip() and not events:
        segments = _ordered_segments([capture.stdout.strip()])

    return _finish(
        segments=segments,
        terminal=terminal,
        stop_reason=stop_reason,
        capture=capture,
        events=events,
        session_id=session_id,
        extra_meta={"terminal_contract": "session.resume_hint|status|result"},
    )


def conform_cursor(capture: CaptureInput) -> ResponseEnvelope:
    """Cursor stream-json / transcript: terminal proof is ``turn_ended``.

    Segments come from ordered ``text`` / assistant ``message`` events (not only
    the last). ``turn_ended`` with error status → failed; length reasons map to
    ``length_limited``.
    """
    events = list(capture.events) if capture.events else _parse_jsonl(capture.stdout)
    texts: list[str] = []
    stream_chunks: list[str] = []
    stop_reason: str | None = None
    terminal = False
    session_id = capture.session_id
    error_terminal = False

    def flush_stream() -> None:
        if stream_chunks:
            texts.append("".join(stream_chunks))
            stream_chunks.clear()

    for event in events:
        etype = str(event.get("type") or "")
        sid = event.get("sessionId") or event.get("session_id")
        if isinstance(sid, str) and sid:
            session_id = sid

        if etype == "text":
            content = event.get("content")
            if content is not None:
                stream_chunks.append(str(content))
        elif etype == "message" and event.get("role") == "assistant":
            flush_stream()
            text = _assistant_text_from_content(event.get("content"))
            if text:
                texts.append(text)
        elif event.get("role") == "assistant" and isinstance(event.get("message"), dict):
            flush_stream()
            text = _assistant_text_from_content(event["message"].get("content"))
            if text:
                texts.append(text)
        elif etype == "turn_ended":
            flush_stream()
            terminal = True
            status = str(event.get("status") or event.get("reason") or "turn_ended")
            stop_reason = status
            if _is_error_reason(status) or status.lower() in {"error", "failed", "failure"}:
                error_terminal = True
            if _is_length_reason(status):
                stop_reason = status
        elif etype in {"result", "done", "task_complete"}:
            flush_stream()
            terminal = True
            stop_reason = str(event.get("reason") or event.get("subtype") or etype)
            body = event.get("result") or event.get("content") or event.get("text")
            if isinstance(body, str) and body.strip():
                texts.append(body.strip())
            if event.get("is_error") is True:
                error_terminal = True
                stop_reason = "error"

        reason = event.get("stop_reason") or event.get("reason")
        if isinstance(reason, str) and _is_length_reason(reason):
            stop_reason = reason

    flush_stream()
    segments = _ordered_segments(texts)
    if not segments and capture.stdout.strip() and not events:
        segments = _ordered_segments([capture.stdout.strip()])

    return _finish(
        segments=segments,
        terminal=terminal,
        stop_reason=stop_reason,
        capture=capture,
        events=events,
        session_id=session_id,
        error_terminal=error_terminal,
        extra_meta={"terminal_contract": "turn_ended"},
    )


def conform_opencode(capture: CaptureInput) -> ResponseEnvelope:
    """OpenCode ``--format json`` NDJSON: terminal proof is final ``step_finish``.

    Intermediate ``step_finish`` with ``reason=tool-calls`` is NOT terminal.
    Final ``reason=stop`` (and aliases) → complete; ``reason=length`` →
    length_limited. Ordered text parts from every ``type=text`` event are kept
    (Sol multi-turn NDJSON requirement — not last-message-only).
    """
    events = list(capture.events) if capture.events else _parse_jsonl(capture.stdout)
    texts: list[str] = []
    current_turn: list[str] = []
    stop_reason: str | None = None
    terminal = False
    session_id = capture.session_id
    error_terminal = False

    terminal_success_reasons = frozenset(
        {"stop", "end", "end_turn", "endturn", "done", "complete", "completed", "success"}
    )

    def commit_turn() -> None:
        if current_turn:
            msg = "".join(current_turn)
            if msg:
                texts.append(msg)
            current_turn.clear()

    for event in events:
        etype = str(event.get("type") or "")
        sid = event.get("sessionID") or event.get("sessionId") or event.get("session_id")
        if isinstance(sid, str) and sid:
            session_id = sid

        if etype == "text":
            part = event.get("part") if isinstance(event.get("part"), dict) else {}
            text = part.get("text") if part else event.get("text") or event.get("content")
            if isinstance(text, str) and text:
                current_turn.append(text)
            continue

        if etype in {"tool", "tool_use", "step_start"}:
            commit_turn()
            continue

        if etype == "step_finish":
            commit_turn()
            part = event.get("part") if isinstance(event.get("part"), dict) else {}
            reason_raw = part.get("reason") if part else event.get("reason")
            reason = str(reason_raw).strip() if reason_raw is not None else ""
            reason_norm = reason.lower().replace("-", "_")
            if reason_norm in {"tool_calls", "tool-calls", "toolcalls"}:
                # Intermediate step boundary — not completion proof.
                stop_reason = stop_reason or reason or "tool-calls"
                continue
            if _is_length_reason(reason_norm) or _is_length_reason(reason):
                terminal = True
                stop_reason = reason or "length"
                continue
            if _is_error_reason(reason_norm) or reason_norm in {"error", "fail", "failed"}:
                terminal = True
                error_terminal = True
                stop_reason = reason or "error"
                continue
            if reason_norm in terminal_success_reasons or not reason:
                # Empty reason on step_finish is still a finish boundary; treat
                # only explicit success aliases / stop as complete. Bare empty
                # is weaker — require a known success reason for complete.
                if reason_norm in terminal_success_reasons:
                    terminal = True
                    stop_reason = reason or "stop"
                else:
                    stop_reason = stop_reason or "step_finish"
                continue
            # Unknown reason: observe the finish event but only mark terminal
            # when the reason is a known success/length/error class.
            stop_reason = reason

        if etype in {"result", "done", "task_complete"}:
            commit_turn()
            terminal = True
            stop_reason = str(event.get("reason") or etype)

    commit_turn()
    segments = _ordered_segments(texts)
    if not segments and capture.stdout.strip() and not events:
        segments = _ordered_segments([capture.stdout.strip()])

    return _finish(
        segments=segments,
        terminal=terminal,
        stop_reason=stop_reason,
        capture=capture,
        events=events,
        session_id=session_id,
        error_terminal=error_terminal,
        extra_meta={"terminal_contract": "step_finish.reason"},
    )


def conform_hermes(capture: CaptureInput) -> ResponseEnvelope:
    """Hermes ``-z`` one-shot: plain stdout has no documented terminal event.

    Hermes adapters only see the final assistant message on stdout (no
    stream-json). Without structured terminal evidence the envelope is
    ``unknown`` — never ``complete`` on exit 0 + text alone.

    If a capture *does* include structured events (result/done/task_complete)
    or a grok-shaped ``stopReason`` object, those are honored. In-band
    ``HTTP 4xx/5xx`` provider errors (documented Hermes failure shape) map to
    ``failed``.
    """
    events = list(capture.events) if capture.events else _parse_jsonl(capture.stdout)
    texts: list[str] = []
    stop_reason: str | None = None
    terminal = False
    session_id = capture.session_id
    error_terminal = False
    extra: dict[str, Any] = {
        "terminal_contract": "structured_only",
        "formal_review_eligible": False,
    }

    if events:
        for event in events:
            etype = str(event.get("type") or event.get("event") or "")
            if etype in {"assistant", "message", "text"}:
                text = event.get("text") or event.get("content") or event.get("result")
                if isinstance(text, str) and text:
                    texts.append(text)
            if etype in {"result", "done", "RESULT", "task_complete"}:
                terminal = True
                stop_reason = str(event.get("reason") or etype)
                body = event.get("result") or event.get("content") or event.get("text")
                if isinstance(body, str) and body.strip():
                    texts.append(body.strip())
            if "stopReason" in event or "stop_reason" in event:
                terminal = True
                raw = event.get("stopReason", event.get("stop_reason"))
                if raw is not None:
                    stop_reason = str(raw)
                text = event.get("text")
                if isinstance(text, str) and text.strip():
                    texts.append(text.strip())
            reason = event.get("stop_reason") or event.get("reason")
            if isinstance(reason, str) and _is_length_reason(reason):
                stop_reason = reason
                terminal = True
            sid = event.get("session_id")
            if isinstance(sid, str) and sid:
                session_id = sid
    else:
        obj = _parse_json_object_tolerant(capture.stdout)
        if obj is not None and ("stopReason" in obj or "stop_reason" in obj):
            terminal = True
            raw = obj.get("stopReason", obj.get("stop_reason"))
            stop_reason = str(raw) if raw is not None else "stopReason"
            text = obj.get("text")
            if isinstance(text, str) and text.strip():
                texts.append(text.strip())
            sid = obj.get("sessionId") or obj.get("session_id")
            if isinstance(sid, str) and sid:
                session_id = sid
        else:
            cleaned = (capture.stdout or "").strip()
            # Strip ANSI the same way Hermes adapters do (minimal: control seq).
            cleaned = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", cleaned).strip()
            if cleaned and _HERMES_HTTP_ERROR_RE.match(cleaned.splitlines()[0].strip()):
                # Documented in-band provider error as the final assistant line.
                error_terminal = True
                terminal = True
                stop_reason = "inband_http_error"
                # Do not promote the error string as a successful segment.
            elif cleaned:
                texts.append(cleaned)

    segments = _ordered_segments(texts)
    return _finish(
        segments=segments,
        terminal=terminal,
        stop_reason=stop_reason,
        capture=capture,
        events=events,
        session_id=session_id,
        error_terminal=error_terminal,
        extra_meta=extra,
    )


def conform_unknown_stub(capture: CaptureInput) -> ResponseEnvelope:
    """Fallback for unregistered transports: never invent ``complete``."""
    text = capture.stdout.strip()
    segments = _ordered_segments([text] if text else [])
    return _envelope(
        segments=segments,
        state=CompletionState.UNKNOWN,
        terminal=False,
        capture=capture,
        stop_reason="adapter_conformance_stub",
        extra_meta={"formal_review_eligible": False, "b2_status": "stub"},
    )


_CONFORMERS: dict[str, Callable[[CaptureInput], ResponseEnvelope]] = {
    "codex": conform_codex,
    "claude": conform_claude,
    "agy": conform_agy,
    # B2 — native / remaining adapters
    "grok": conform_grok,
    "grok-build": conform_grok,
    "kimi": conform_kimi,
    "cursor": conform_cursor,
    "opencode": conform_opencode,
    "hermes": conform_hermes,
    "hermes-grok": conform_hermes,
    "hermes-qwen": conform_hermes,
    "hermes-deepseek": conform_hermes,
    "grok-hermes": conform_hermes,
}


def conform(capture: CaptureInput) -> ResponseEnvelope:
    """Dispatch to the adapter-specific conformer (or unknown stub)."""
    name = capture.adapter.strip().lower()
    if name in _CONFORMERS:
        return _CONFORMERS[name](capture)
    if name:
        # Unregistered transport — never invent complete.
        return conform_unknown_stub(
            CaptureInput(
                adapter=name,
                stdout=capture.stdout,
                stderr=capture.stderr,
                returncode=capture.returncode,
                events=capture.events,
                raw_bytes=capture.raw_bytes,
                session_id=capture.session_id,
                transport_metadata=capture.transport_metadata,
            )
        )
    raise ValueError(f"Unknown adapter for conformance: {capture.adapter!r}")


def raw_capture_matches(envelope: ResponseEnvelope, raw: bytes) -> bool:
    """Prove raw-capture hash matches bytes (Sol B1 acceptance)."""
    if not envelope.raw_capture_sha256:
        return False
    return hashlib.sha256(raw).hexdigest() == envelope.raw_capture_sha256
