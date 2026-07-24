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
from scripts.review.model_catalog import resolve_kimi_model as resolve_kimi_catalog_route

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
    """Adapter for native ``kimi`` or KimiCC (Claude Code host binary)."""

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

        requested_alias = model or KIMI_DEFAULT_MODEL
        try:
            canonical_model_id, routes = resolve_kimi_catalog_route(requested_alias)
        except Exception as exc:
            raise ValueError(
                f"KimiAdapter: unsupported Kimi model {requested_alias!r}; "
                f"allowed: {sorted(KIMI_ALLOWED_MODELS)}"
            ) from exc

        native_bin = _resolve_kimi_binary()
        if native_bin is not None:
            if mode == "read-only":
                raise ValueError(_READ_ONLY_REFUSAL)

            if effort and canonical_model_id == KIMI_MODEL_ALIASES["k3"] and effort != self.default_effort:
                _logger.warning(
                    "Kimi K3 exposes max effort only; ignoring requested effort=%s",
                    effort,
                )

            cmd: list[str] = [
                native_bin,
                "-p",
                prompt,
                "-m",
                canonical_model_id,
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
                "kimi native invocation: task=%s mode=%s model=%s effort=%s",
                task_id,
                mode,
                canonical_model_id,
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

        # KimiCC fallback route (Claude Code host binary pointed at Kimi endpoint)
        claude_bin = _resolve_claude_binary()
        if not claude_bin:
            raise RuntimeError(
                "Kimi lane unavailable: no native `kimi` binary found and `claude` binary for KimiCC is not on PATH."
            )

        endpoint = os.environ.get("KIMICC_ENDPOINT", "coding")
        if endpoint not in ("coding", "platform"):
            raise ValueError(f"KimiAdapter: unsupported endpoint {endpoint!r} (use 'coding' or 'platform')")

        auth = _resolve_kimicc_auth(endpoint)
        if not auth:
            raise RuntimeError(
                "Kimi lane unavailable: no Kimi API credential found for KimiCC route. "
                "Set KIMICC_AUTH_TOKEN, MOONSHOT_API_KEY, KIMI_API_KEY, ANTHROPIC_AUTH_TOKEN, or run `kimi login`."
            )

        token, auth_source = auth
        lead_model = routes["platform_model_id"] if endpoint == "platform" else routes["coding_model_id"]

        base_url = os.environ.get("KIMICC_BASE_URL") or (
            "https://api.moonshot.ai/anthropic" if endpoint == "platform" else "https://api.kimi.com/coding"
        )
        base_url = base_url.rstrip("/")

        cmd = [
            claude_bin,
            "-p",
            "--model",
            lead_model,
            "--output-format",
            "stream-json",
            "--verbose",
        ]
        if mode == "danger":
            cmd.append("--dangerously-skip-permissions")

        cmd.extend(["--", prompt])

        env_overrides = {
            "ANTHROPIC_BASE_URL": base_url,
            "ANTHROPIC_AUTH_TOKEN": token,
            "ANTHROPIC_MODEL": lead_model,
            "ANTHROPIC_DEFAULT_OPUS_MODEL": lead_model,
            "ANTHROPIC_DEFAULT_SONNET_MODEL": lead_model,
            "ANTHROPIC_DEFAULT_HAIKU_MODEL": lead_model,
            "ANTHROPIC_DEFAULT_FABLE_MODEL": lead_model,
            "CLAUDE_CODE_SUBAGENT_MODEL": lead_model,
            "ENABLE_TOOL_SEARCH": "false",
            "LEARN_UKRAINIAN_TRANSPORT": "kimicc",
        }
        if "ANTHROPIC_API_KEY" in os.environ:
            env_overrides["ANTHROPIC_API_KEY"] = ""

        if routes.get("kimicc_alias") == "k3":
            env_overrides["CLAUDE_CODE_EFFORT_LEVEL"] = effort or self.default_effort
        elif effort:
            env_overrides["CLAUDE_CODE_EFFORT_LEVEL"] = effort

        _logger.debug(
            "kimicc invocation: task=%s mode=%s endpoint=%s model=%s auth_source=%s",
            task_id,
            mode,
            endpoint,
            lead_model,
            auth_source,
        )

        liveness_paths = tuple(
            p for p in (Path.home() / ".claude-kimicc", Path.home() / ".claude" / "projects") if p.exists()
        )

        return InvocationPlan(
            cmd=cmd,
            cwd=cwd,
            stdin_payload="",
            output_file=None,
            env_overrides=env_overrides,
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
            elif isinstance(event.get("result"), str) and event.get("result").strip():
                response_parts.append(event["result"].strip())
            elif isinstance(event.get("message"), dict):
                content = event["message"].get("content")
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str):
                            response_parts.append(item["text"].strip())
            if event.get("role") == "meta" and event.get("type") == "session.resume_hint":
                raw_session_id = event.get("session_id")
                if isinstance(raw_session_id, str) and raw_session_id.strip():
                    session_id = raw_session_id.strip()
            sid = event.get("session_id") or event.get("sessionId")
            if isinstance(sid, str) and sid.strip() and not session_id:
                session_id = sid.strip()

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


def _resolve_kimi_binary() -> str | None:
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
    return None


def _resolve_claude_binary() -> str | None:
    found = shutil.which("claude")
    if found:
        return found
    default = Path.home() / ".local" / "bin" / "claude"
    if default.is_file() and os.access(default, os.X_OK):
        return str(default)
    return None


def _resolve_kimicc_auth(endpoint: str) -> tuple[str, str] | None:
    """Resolve KimiCC auth token and its source name without logging the token.

    Precedence matching start-kimicc.sh:
    1. KIMICC_AUTH_TOKEN
    2. MOONSHOT_API_KEY
    3. KIMI_API_KEY
    4. ANTHROPIC_AUTH_TOKEN (coding endpoint only)
    5. OAuth credential via get_oauth_token() (coding endpoint only)
    """
    for env_var in ("KIMICC_AUTH_TOKEN", "MOONSHOT_API_KEY", "KIMI_API_KEY"):
        val = os.environ.get(env_var)
        if val and val.strip():
            return val.strip(), env_var

    if endpoint == "coding":
        val = os.environ.get("ANTHROPIC_AUTH_TOKEN")
        if val and val.strip():
            return val.strip(), "ANTHROPIC_AUTH_TOKEN"

        try:
            from scripts.lib.kimi_coding_oauth import get_oauth_token

            oauth_token = get_oauth_token()
            if oauth_token and oauth_token.strip():
                return oauth_token.strip(), "oauth(kimi login)"
        except Exception as exc:
            _logger.debug("KimiCC OAuth credential lookup failed: %s", exc)

    return None


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
