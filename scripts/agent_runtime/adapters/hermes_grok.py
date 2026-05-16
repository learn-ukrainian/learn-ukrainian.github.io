"""HermesGrokAdapter — wraps ``hermes -z PROMPT -m grok-4.3``.

Hermes resolves MCP tool calls inside its own session loop using the user's
``~/.hermes/config.yaml`` registration. In ``-z`` mode the adapter only sees
Hermes's final assistant message on stdout; there is no Claude/Gemini/Codex
stream-json trace to parse. That means tool-call telemetry is unavailable,
not verified zero. The adapter returns a parse result whose
``tool_calls_total`` is ``None`` so downstream V7 telemetry can preserve that
distinction.

Reasoning effort is also config-scoped for Hermes headless mode. This adapter
never mutates ``~/.hermes/config.yaml`` because doing so per call would race
concurrent V7 builds. If a caller passes ``effort`` and the readable top-level
Hermes config disagrees, we log a warning and continue with the configured
runtime behavior.
"""
from __future__ import annotations

import logging
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from ..result import ParseResult
from .base import InvocationPlan

_logger = logging.getLogger(__name__)

_ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_RATE_LIMIT_RE = re.compile(
    r"rate limit|rate_limit|quota exceeded|too many requests|\bHTTP 429\b|\b429\b",
    re.IGNORECASE,
)
_HERMES_CONFIG_PATH = Path.home() / ".hermes" / "config.yaml"


@dataclass(frozen=True)
class HermesGrokParseResult(ParseResult):
    """Parse result with explicit unknown tool-call telemetry."""

    tool_calls_total: int | None = None


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text or "").strip()


def _read_hermes_config(path: Path = _HERMES_CONFIG_PATH) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return {}
    return data if isinstance(data, dict) else {}


def _top_level_agent_effort(config: dict[str, Any]) -> str | None:
    agent = config.get("agent")
    if not isinstance(agent, dict):
        return None
    effort = agent.get("reasoning_effort")
    if isinstance(effort, str) and effort.strip():
        return effort.strip()
    return None


def _sources_mcp_registered(config: dict[str, Any]) -> bool:
    servers = config.get("mcp_servers")
    if not isinstance(servers, dict):
        return False
    sources = servers.get("sources")
    if not isinstance(sources, dict):
        return False
    return bool(sources.get("enabled") is not False and sources.get("url"))


class HermesGrokAdapter:
    """Adapter for the Hermes CLI using Grok 4.3."""

    name: str = "grok"
    default_model: str = "grok-4.3"
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
        """Build the Hermes one-shot invocation.

        ``tool_config`` is intentionally not translated into CLI flags: Hermes
        discovers MCP servers from ``~/.hermes/config.yaml``. Unknown keys are
        ignored for forward compatibility with the common runtime contract.
        """
        _ = mode
        _ = task_id
        _ = session_id
        _ = tool_config

        config = _read_hermes_config()
        configured_effort = _top_level_agent_effort(config)
        if effort and configured_effort and configured_effort != effort:
            _logger.warning(
                "Hermes Grok effort=%r requested, but ~/.hermes/config.yaml "
                "agent.reasoning_effort=%r; using Hermes config without mutation",
                effort,
                configured_effort,
            )
        elif effort and configured_effort is None:
            _logger.warning(
                "Hermes Grok effort=%r requested, but no readable top-level "
                "agent.reasoning_effort was found in ~/.hermes/config.yaml; "
                "using Hermes config without mutation",
                effort,
            )

        if not _sources_mcp_registered(config):
            _logger.warning(
                "Hermes Grok did not find enabled mcp_servers.sources in "
                "~/.hermes/config.yaml; MCP tool availability depends on Hermes config"
            )

        hermes_bin = shutil.which("hermes") or "hermes"
        return InvocationPlan(
            cmd=[hermes_bin, "-z", prompt, "-m", model or self.default_model],
            cwd=cwd,
            stdin_payload="",
            output_file=None,
            env_overrides={},
            liveness_paths=(),
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
    ) -> HermesGrokParseResult:
        """Parse Hermes final stdout into a runtime result."""
        _ = output_file
        _ = plan
        _ = call_start_time

        response = _strip_ansi(stdout)
        clean_stderr = _strip_ansi(stderr)
        rate_limited = returncode != 0 and bool(_RATE_LIMIT_RE.search(clean_stderr))
        ok = returncode == 0 and bool(response) and not rate_limited
        stderr_excerpt = None if ok else (clean_stderr or response or None)

        return HermesGrokParseResult(
            ok=ok,
            response=response if ok else "",
            stderr_excerpt=stderr_excerpt[:500] if stderr_excerpt else None,
            rate_limited=rate_limited,
            session_id=None,
            tokens=None,
            tool_calls=[],
            tool_calls_total=None,
        )

    def liveness_signal_paths(self, plan: InvocationPlan) -> tuple[Path, ...]:
        """Hermes ``-z`` writes to stdout; no separate liveness files."""
        _ = plan
        return ()
