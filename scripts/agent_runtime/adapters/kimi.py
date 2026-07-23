"""Native Kimi Code CLI adapter for the Kimi K3 subscription lane.

The local Kimi Code installation exposes K3 as ``kimi-code/k3`` and emits
newline-delimited events in ``--output-format stream-json`` mode. OAuth
credentials stay in Kimi's own home directory; this adapter never reads or
injects them.

Kimi Code 0.27.0 evidence (2026-07-17): ``kimi --yolo -p \"…\"`` exits with
``error: Cannot combine --prompt with --yolo.`` Bare ``kimi -p`` also writes
without an approval prompt. Consequently, headless workspace-write and danger
must be flagless (delegate.py already verifies their worktrees), while
read-only is refused because the CLI cannot guarantee it.
"""

from __future__ import annotations

import logging
import os
import re
import shutil
from pathlib import Path
from typing import Any

from scripts.review.model_catalog import kimi_model_aliases

from ..result import ParseResult
from ..tool_calls import normalize_tool_calls, parse_json_events
from .base import InvocationPlan

_logger = logging.getLogger(__name__)

KIMI_DEFAULT_MODEL = "k2.7-coding"
KIMI_BRIDGE_DEFAULT_MODEL = "k3"
KIMI_DEFAULT_EFFORT = "max"
# Catalog-backed aliases keep dispatch, the native launcher, and KimiCC in
# lockstep. The managed seat's usage window depletes fast (operator,
# 2026-07-16), so dispatch defaults to the coding model; K3 (always-max
# reasoning) is reserved for deep asks.
KIMI_MODEL_ALIASES: dict[str, str] = kimi_model_aliases()
KIMI_ALLOWED_MODELS: frozenset[str] = frozenset(KIMI_MODEL_ALIASES)


def resolve_kimi_model(model: str | None) -> str:
    """Map a fleet short name or full CLI alias; reject unregistered names."""
    requested = model or KIMI_DEFAULT_MODEL
    try:
        return KIMI_MODEL_ALIASES[requested]
    except KeyError as exc:
        raise ValueError(
            f"KimiAdapter: unsupported Kimi model {requested!r}; "
            f"allowed: {sorted(KIMI_ALLOWED_MODELS)}"
        ) from exc

_RATE_LIMIT_RE = re.compile(
    r"rate limit|rate_limit|usage limit|quota exceeded|too many requests|\b429\b",
    re.IGNORECASE,
)
_MODE_FLAGS: dict[str, tuple[str, ...]] = {
    "read-only": (),
    "workspace-write": (),
    "danger": (),
}

_READ_ONLY_REFUSAL = (
    "kimi headless auto-approves mutations; read-only cannot be guaranteed "
    "on CLI 0.27 — use another agent"
)


class KimiAdapter:
    """Adapter for native ``kimi`` prompt mode using the K3 model."""

    name: str = "kimi"
    default_model: str = KIMI_DEFAULT_MODEL
    default_effort: str = KIMI_DEFAULT_EFFORT
    supported_modes: frozenset[str] = frozenset(_MODE_FLAGS)

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
        if mode not in self.supported_modes:
            raise ValueError(
                f"KimiAdapter: unsupported mode {mode!r} "
                f"(supported: {sorted(self.supported_modes)})"
            )
        if mode == "read-only":
            raise ValueError(_READ_ONLY_REFUSAL)

        requested_model = resolve_kimi_model(model)

        if effort and requested_model == KIMI_MODEL_ALIASES["k3"] and effort != self.default_effort:
            _logger.warning(
                "Kimi K3 exposes max effort only; ignoring requested effort=%s",
                effort,
            )

        kimi_bin = _resolve_kimi_binary()
        cmd: list[str] = [
            kimi_bin,
            "-p",
            prompt,
            "-m",
            requested_model,
            "--output-format",
            "stream-json",
            *_MODE_FLAGS[mode],
        ]

        if session_id:
            cmd.extend(["--session", session_id])

        config = tool_config or {}
        for skills_dir in _as_string_list(config.get("kimi_skills_dirs")):
            cmd.extend(["--skills-dir", skills_dir])
        for add_dir in _as_string_list(config.get("kimi_add_dirs")):
            cmd.extend(["--add-dir", add_dir])

        _logger.debug(
            "kimi invocation: task=%s mode=%s model=%s effort=%s",
            task_id,
            mode,
            requested_model,
            self.default_effort,
        )

        liveness_paths = tuple(
            path
            for path in (
                Path.home() / ".kimi-code" / "logs" / "kimi-code.log",
                Path.home() / ".kimi-code" / "session_index.jsonl",
            )
            if path.exists()
        )
        return InvocationPlan(
            cmd=cmd,
            cwd=cwd,
            stdin_payload="",
            output_file=None,
            env_overrides={},
            liveness_paths=liveness_paths,
        )

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
        _ = (output_file, plan, call_start_time)

        events = parse_json_events(stdout, source="kimi stream-json", logger=_logger)
        response_parts: list[str] = []
        session_id: str | None = None
        for event in events:
            if event.get("role") == "assistant":
                content = _assistant_text(event.get("content"))
                if content:
                    response_parts.append(content)
            if event.get("role") == "meta" and event.get("type") == "session.resume_hint":
                raw_session_id = event.get("session_id")
                if isinstance(raw_session_id, str) and raw_session_id.strip():
                    session_id = raw_session_id.strip()

        response = "\n".join(response_parts).strip()
        combined = f"{stderr or ''}\n{stdout or ''}"
        call_failed = returncode != 0 or not response
        rate_limited = call_failed and bool(_RATE_LIMIT_RE.search(combined))
        ok = returncode == 0 and bool(response) and not rate_limited

        stderr_excerpt: str | None = None
        if not ok:
            source = (stderr or "").strip() or (stdout or "").strip()
            stderr_excerpt = source[:500] or None
        elif stderr.strip():
            stderr_excerpt = stderr.strip()[:500]

        return ParseResult(
            ok=ok,
            response=response if ok else "",
            stderr_excerpt=stderr_excerpt,
            rate_limited=rate_limited,
            session_id=session_id,
            tokens=None,
            tool_calls=normalize_tool_calls(events),
        )

    def liveness_signal_paths(self, plan: InvocationPlan) -> tuple[Path, ...]:
        return tuple(plan.liveness_paths)


def _resolve_kimi_binary() -> str:
    override = os.environ.get("LEARN_UK_KIMI_BIN")
    # The hermes npm install (@moonshot-ai/kimi-code) is the maintained one;
    # ~/.kimi-code/bin/kimi is the legacy standalone binary and is often stale.
    candidates = (
        override,
        shutil.which("kimi"),
        str(Path.home() / ".hermes" / "node" / "bin" / "kimi"),
        str(Path.home() / ".kimi-code" / "bin" / "kimi"),
    )
    for candidate in candidates:
        if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return str(Path(candidate))
    raise RuntimeError(
        "Kimi Code CLI not found. Install it so `kimi` is on PATH or set "
        "LEARN_UK_KIMI_BIN to the executable path."
    )


def _as_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    values = value if isinstance(value, list | tuple) else [value]
    return [str(item) for item in values if str(item).strip()]


def _assistant_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, str) and item.strip():
                parts.append(item.strip())
            elif isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str) and text.strip():
                    parts.append(text.strip())
        return "\n".join(parts)
    return ""
