"""HermesQwenAdapter — wraps ``hermes -z PROMPT -m qwen/qwen3.6-{plus|flash|max-preview}``.

Same Hermes ``-z`` one-shot pattern as HermesGrokAdapter and HermesDeepSeekAdapter:
hermes resolves MCP tool calls inside its own session loop using
``~/.hermes/config.yaml``. The adapter only sees Hermes's final assistant message
on stdout, so ``tool_calls_total`` remains ``None`` (unknown, not zero).

Qwen routes through Alibaba's DashScope upstream via OpenRouter; the Hermes
config is already pointed at ``provider: openrouter`` with ``base_url:
https://openrouter.ai/api/v1`` and ``model.default: qwen/qwen3.6-plus`` (set
2026-05-18 by the user when the OpenRouter API key was added).

Model variants surfaced through ``model`` arg:

* ``qwen/qwen3.6-plus`` (default) — Qwen 3.6 Plus, primary content-writing
  candidate for B1+/seminar tracks per the 2026-05-18 multi-writer strategy
  conversation. **Not yet bakeoff-validated as a V7 module writer.**
* ``qwen/qwen3.6-flash`` — faster/cheaper variant for cost-at-scale writing.
* ``qwen/qwen3.6-max-preview`` — top capability tier for adversarial review
  or high-stakes single-module work.
* ``qwen/qwen3.6-35b-a3b:thinking`` — reasoning-augmented variant; expensive
  reasoning tokens but stronger structured-output adherence.

Smoke-tested 2026-05-18:
``hermes -z "..." -m qwen/qwen3.6-plus`` → ``Model: qwen/qwen3.6-plus — running and ready.``

Reasoning effort is config-scoped in Hermes ``-z`` mode (same as Grok and
DeepSeek). This adapter does NOT mutate ``~/.hermes/config.yaml`` per call to
avoid races with concurrent dispatches; if a caller passes ``effort`` and the
readable top-level Hermes config disagrees, we log a warning and continue with
the configured runtime behavior.
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
class HermesQwenParseResult(ParseResult):
    """Parse result with explicit unknown tool-call telemetry.

    Mirrors HermesGrokParseResult / HermesDeepSeekParseResult — Hermes ``-z``
    mode does not expose a structured tool-call trace, so ``tool_calls_total``
    is ``None`` (unknown) rather than ``0`` (zero verified calls). Downstream
    V7 telemetry preserves that distinction.
    """

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


class HermesQwenAdapter:
    """Adapter for the Hermes CLI using Qwen 3.6 (plus, flash, or max-preview)."""

    name: str = "qwen"
    default_model: str = "qwen/qwen3.6-plus"
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
                "Hermes Qwen effort=%r requested, but ~/.hermes/config.yaml "
                "agent.reasoning_effort=%r; using Hermes config without mutation",
                effort,
                configured_effort,
            )
        elif effort and configured_effort is None:
            _logger.warning(
                "Hermes Qwen effort=%r requested, but no readable top-level "
                "agent.reasoning_effort was found in ~/.hermes/config.yaml; "
                "using Hermes config without mutation",
                effort,
            )

        if not _sources_mcp_registered(config):
            _logger.warning(
                "Hermes Qwen did not find enabled mcp_servers.sources in "
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
    ) -> HermesQwenParseResult:
        """Parse Hermes final stdout into a runtime result."""
        _ = output_file
        _ = plan
        _ = call_start_time

        response = _strip_ansi(stdout)
        clean_stderr = _strip_ansi(stderr)
        rate_limited = returncode != 0 and bool(_RATE_LIMIT_RE.search(clean_stderr))
        ok = returncode == 0 and bool(response) and not rate_limited
        stderr_excerpt = None if ok else (clean_stderr or response or None)

        return HermesQwenParseResult(
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
