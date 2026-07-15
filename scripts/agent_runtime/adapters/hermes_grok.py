"""HermesGrokAdapter — wraps ``hermes -z PROMPT -m grok-4.5``.

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
import shutil
from dataclasses import dataclass
from pathlib import Path

from ..result import ParseResult
from .base import InvocationPlan
from .hermes_common import (
    build_hermes_invocation_context,
    build_hermes_parse_fields,
    resolve_hermes_requested_route,
    sources_mcp_registered,
    top_level_agent_effort,
    translate_mcp_prefix_for_hermes,
)

_logger = logging.getLogger(__name__)

GROK_ALLOWED_MODELS: frozenset[str] = frozenset({"grok-4.5"})

@dataclass(frozen=True)
class HermesGrokParseResult(ParseResult):
    """Parse result with explicit unknown tool-call telemetry."""

    tool_calls_total: int | None = None


class HermesGrokAdapter:
    """Adapter for the Hermes CLI using Grok 4.5."""

    name: str = "grok"
    default_model: str = "grok-4.5"
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

        max_budget_usd = (tool_config or {}).get("max_budget_usd")
        if max_budget_usd is not None:
            _logger.warning(
                "non-claude adapter %s ignoring max_budget_usd=%s; "
                "use hard-timeout/silence-timeout instead",
                self.name,
                max_budget_usd,
            )

        requested_model = model or self.default_model
        if requested_model not in GROK_ALLOWED_MODELS:
            raise ValueError(
                f"HermesGrokAdapter: unsupported Grok model {requested_model!r}; "
                f"allowed: {sorted(GROK_ALLOWED_MODELS)}"
            )
        requested_provider, requested_model, provider_forced = resolve_hermes_requested_route(
            tool_config=tool_config,
            default_provider="xai",
            requested_model=requested_model,
        )
        context = build_hermes_invocation_context(
            tool_config=tool_config,
            requested_provider=requested_provider,
            requested_model=requested_model,
            provider_forced=provider_forced,
        )
        config = context.config
        configured_effort = top_level_agent_effort(config)
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

        if not sources_mcp_registered(config):
            _logger.warning(
                "Hermes Grok did not find enabled mcp_servers.sources in "
                "~/.hermes/config.yaml; MCP tool availability depends on Hermes config"
            )

        hermes_bin = shutil.which("hermes") or "hermes"
        hermes_prompt = translate_mcp_prefix_for_hermes(prompt)
        cmd = [hermes_bin, "-z", hermes_prompt, "-m", requested_model]
        if provider_forced:
            cmd.extend(["--provider", requested_provider])
        return InvocationPlan(
            cmd=cmd,
            cwd=cwd,
            stdin_payload="",
            output_file=None,
            env_overrides=context.env_overrides,
            liveness_paths=(),
            metadata=context.metadata,
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
        _ = call_start_time

        fields = build_hermes_parse_fields(
            stdout=stdout,
            stderr=stderr,
            returncode=returncode,
            plan=plan,
            logger=_logger,
        )

        return HermesGrokParseResult(
            ok=fields.ok,
            response=fields.response,
            stderr_excerpt=fields.stderr_excerpt,
            rate_limited=fields.rate_limited,
            session_id=None,
            tokens=None,
            tool_calls=[],
            substitution=fields.substitution,
            tool_calls_total=None,
        )

    def liveness_signal_paths(self, plan: InvocationPlan) -> tuple[Path, ...]:
        """Hermes ``-z`` writes to stdout; no separate liveness files."""
        _ = plan
        return ()
