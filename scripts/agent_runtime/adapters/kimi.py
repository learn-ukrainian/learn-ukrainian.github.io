"""KimiAdapter — wraps the managed native ``kimi`` CLI in headless mode.

The Kimi Code installation owns authentication under ``~/.kimi-code``.  This
adapter deliberately invokes that local managed-seat CLI directly; it never
routes Kimi traffic through a token API or a proxy provider.

Headless invocation is ``kimi -p PROMPT -m ALIAS --output-format stream-json``.
Only ``danger`` may append ``-y``: read-only and workspace-write calls leave
approval to the CLI and therefore never opt in to ``-y`` or ``--auto``.
"""
from __future__ import annotations

import json
import logging
import os
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ..result import ParseResult
from ..tool_calls import normalize_tool_calls, parse_json_events
from .base import InvocationPlan

KIMI_DEFAULT_MODEL = "k2.7-coding"
KIMI_BRIDGE_DEFAULT_MODEL = "k3"
KIMI_MODEL_ALIASES: dict[str, str] = {
    "k3": "kimi-code/k3",
    "k2.7-coding": "kimi-code/kimi-for-coding",
    "k2.7-coding-highspeed": "kimi-code/kimi-for-coding-highspeed",
}
_RATE_LIMIT_RE = re.compile(
    r"rate limit|rate_limit|usage limit|quota exceeded|too many requests|\b429\b",
    re.IGNORECASE,
)
_logger = logging.getLogger(__name__)


def resolve_kimi_code_bin() -> str:
    """Resolve the native binary, honoring a non-secret test/host override."""
    return os.environ.get("KIMI_CODE_BIN") or str(Path.home() / ".kimi-code" / "bin" / "kimi")


def resolve_kimi_model(model: str | None) -> str:
    """Map a fleet short name to the CLI alias and reject unregistered names."""
    requested = model or KIMI_DEFAULT_MODEL
    try:
        return KIMI_MODEL_ALIASES[requested]
    except KeyError as exc:
        raise ValueError(
            f"KimiAdapter: unsupported Kimi model {requested!r}; "
            f"allowed: {sorted(KIMI_MODEL_ALIASES)}"
        ) from exc


class KimiAdapter:
    """Adapter for Kimi Code's one-shot native CLI invocation."""

    name: str = "kimi"
    default_model: str = KIMI_DEFAULT_MODEL
    supported_modes: frozenset[str] = frozenset({"read-only", "workspace-write", "danger"})

    def build_invocation(
        self,
        *,
        prompt: str,
        mode: str,
        cwd: Path,
        model: str | None,
        task_id: str | None,
        session_id: str | None,
        tool_config: dict | None,
        effort: str | None = None,
    ) -> InvocationPlan:
        """Build a fresh native Kimi invocation without session resumption."""
        _ = (task_id, session_id, tool_config, effort)
        if mode not in self.supported_modes:
            raise ValueError(
                f"KimiAdapter: unsupported mode {mode!r} "
                f"(supported: {sorted(self.supported_modes)})"
            )

        cmd = [
            resolve_kimi_code_bin(),
            "-p",
            prompt,
            "-m",
            resolve_kimi_model(model),
            "--output-format",
            "stream-json",
        ]
        if mode == "danger":
            cmd.append("-y")
        return InvocationPlan(cmd=cmd, cwd=cwd)

    def parse_response(
        self,
        *,
        stdout: str,
        stderr: str,
        returncode: int,
        output_file: Path | None,
        plan: InvocationPlan | None = None,
        call_start_time: float | None = None,
    ) -> ParseResult:
        """Extract terminal text from stream JSON, retaining generic fallbacks."""
        _ = (output_file, plan, call_start_time)
        events = parse_json_events(stdout, source="kimi", logger=_logger)
        extracted = _stream_text(events)
        if extracted:
            text = extracted
        elif events:
            # Stream parsed but carried no text-bearing events (tool/status
            # only). Raw JSONL must never be promoted to a successful
            # response (silent-error-as-content class — see
            # docs/bug-autopsies/hermes-inband-errors.md).
            text = ""
        else:
            # No JSONL at all: plain-text output mode falls back verbatim.
            text = (stdout or "").strip()
        failed = returncode != 0 or not text
        rate_limited = failed and bool(_RATE_LIMIT_RE.search(f"{stdout}\n{stderr}"))
        ok = returncode == 0 and bool(text) and not rate_limited
        diagnostic = ((stderr or "").strip() or (stdout or "").strip())[:500] or None
        return ParseResult(
            ok=ok,
            response=text if ok else "",
            stderr_excerpt=None if ok else diagnostic,
            rate_limited=rate_limited,
            session_id=None,
            tokens=None,
            tool_calls=normalize_tool_calls(events),
        )

    def liveness_signal_paths(self, plan: InvocationPlan) -> tuple[Path, ...]:
        """Kimi streams progress to stdout, so no filesystem probe is needed."""
        _ = plan
        return ()


def _stream_text(events: list[dict[str, Any]]) -> str:
    """Return a final text value or concatenate incremental text events.

    Kimi's stream protocol is intentionally treated as JSONL rather than a
    fixed undocumented schema.  Prefer an explicit terminal/result payload;
    otherwise join text/delta fields in the event order.
    """
    final: str | None = None
    chunks: list[str] = []
    for event in events:
        event_type = str(event.get("type") or event.get("event") or "").lower()
        value = _event_text(event)
        if not value:
            continue
        if event_type in {"result", "final", "completed", "response.completed"}:
            final = value
        else:
            chunks.append(value)
    return (final or "".join(chunks)).strip()


def _event_text(event: Mapping[str, Any]) -> str | None:
    """Read common stream-json text-bearing fields without guessing sessions."""
    for key in ("text", "response", "result", "content"):
        value = event.get(key)
        if isinstance(value, str) and value:
            return value
    for key in ("delta", "message", "data"):
        value = event.get(key)
        if isinstance(value, Mapping):
            nested = _event_text(value)
            if nested:
                return nested
    return None
