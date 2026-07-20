"""Adapter completion-conformance harness (Fleet Comms PR-B1/B2 / #5512).

Maps harness-specific captures into a typed ``ResponseEnvelope``. Adapters may
only emit ``complete`` when their documented terminal contract is observed.
Exit 0 + nonempty text alone is never enough.

B1 primary adapters: codex, claude, agy.
B2 remaining adapters start as stubs that return ``unknown`` until terminal
evidence is proven (Sol: unknown → not formal-review eligible).
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from scripts.fleet_comms.contracts import AssistantSegment, CompletionState, ResponseEnvelope

PRIMARY_ADAPTERS = frozenset({"codex", "claude", "agy"})
# B2 targets — stubs until terminal evidence is wired.
REMAINING_ADAPTERS = frozenset({"grok", "kimi", "cursor", "hermes", "opencode", "hermes-grok", "hermes-qwen", "hermes-deepseek"})


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


def conform_unknown_stub(capture: CaptureInput) -> ResponseEnvelope:
    """B2 stub: transports without proven terminal evidence stay ``unknown``."""
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
}


def conform(capture: CaptureInput) -> ResponseEnvelope:
    """Dispatch to the adapter-specific conformer (or B2 stub)."""
    name = capture.adapter.strip().lower()
    if name in _CONFORMERS:
        return _CONFORMERS[name](capture)
    if name in REMAINING_ADAPTERS or name:
        # Explicit stub path — never invent complete.
        return conform_unknown_stub(CaptureInput(
            adapter=name,
            stdout=capture.stdout,
            stderr=capture.stderr,
            returncode=capture.returncode,
            events=capture.events,
            raw_bytes=capture.raw_bytes,
            session_id=capture.session_id,
            transport_metadata=capture.transport_metadata,
        ))
    raise ValueError(f"Unknown adapter for conformance: {capture.adapter!r}")


def raw_capture_matches(envelope: ResponseEnvelope, raw: bytes) -> bool:
    """Prove raw-capture hash matches bytes (Sol B1 acceptance)."""
    if not envelope.raw_capture_sha256:
        return False
    return hashlib.sha256(raw).hexdigest() == envelope.raw_capture_sha256
