"""AgyAdapter — wraps the Antigravity (`agy`) CLI for the agent runtime.

Ported from `kubedojo/scripts/agent_runtime/adapters/agy.py` for the
2026-05-20 seminar-writer evaluation. `agy` ships Gemini Flash 3.5
("gemini-3.5-flash-high") on a separate meter from gemini-cli; the
seminar-track writer ADR at
`docs/decisions/pending/2026-05-20-seminar-track-writer-assignment.md`
adds it as candidate D pending empirical testing.

Known behavioral facts as of agy 1.0.0 (verified locally 2026-05-20):

- Headless prompt mode is ``agy -p "<prompt>"``. Stdin prompts are ignored.
- Resume/new conversation is ``--conversation=<uuid>``.
- Write-capable modes use ``--dangerously-skip-permissions``. Read-only
  hangs on interactive permission prompts; callers must force
  ``mode="danger"`` for headless dispatch (mirrors the codex protection).
- No known on-disk session or liveness file exists — stdout is canonical.
- ``agy`` model selection is controlled by the interactive TUI and persists
  across ``agy -p`` invocations; there is no CLI model flag. The runtime
  records the caller-passed ``model`` in the JSONL audit row for
  provenance only.
- ``agy plugin`` only exposes ``import gemini|claude``, ``install``,
  ``enable``, ``disable``. There is no plugin-marketplace browse surface,
  and ``import gemini`` is a no-op in a default install. The adapter
  accepts ``tool_config["mcp_server_names"]`` for API parity with
  ``GeminiAdapter`` but does not act on it today; wire ``agy plugin
  enable <name>`` once concrete MCP servers are available.

Phase-2 follow-up will wire MCP plugin enablement; until then ``-tools``
writer mode will trip ``MCP_TOOLS_NEVER_INVOKED`` if agy is selected,
which is the expected (and informative) signal in the seminar-writer
bakeoff.

Differences from the kubedojo source:

- ``effort: str | None = None`` parameter added on ``build_invocation``
  to match this repo's ``AgentAdapter`` protocol; treated as a no-op with
  a debug log (mirrors the Gemini adapter; follow-up #1396).
"""
from __future__ import annotations

import logging
import os
import re
import shutil
from pathlib import Path

from ..result import ParseResult
from .base import InvocationPlan

_logger = logging.getLogger(__name__)

# Defensive defaults borrowed from Gemini CLI. Agy is new enough that these
# may need adjustment once we see real Antigravity rate-limit errors.
_RATE_LIMIT_PATTERNS = (
    r"RESOURCE_EXHAUSTED",
    r"usage limit reached",
    r"quota exceeded",
    r"daily.{0,10}limit.{0,10}exceeded",
)
_RATE_LIMIT_RE = re.compile("|".join(_RATE_LIMIT_PATTERNS), re.IGNORECASE)


class AgyAdapter:
    """Adapter for the ``agy`` Antigravity CLI."""

    name: str = "agy"
    default_model: str = os.environ.get("LEARN_UK_AGY_MODEL", "gemini-3.5-flash-high")
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
        """Build the ``agy`` print-mode invocation.

        ``model`` is intentionally not mapped to a CLI flag. The active
        model is whichever model the operator selected in the ``agy`` TUI
        panel. ``effort`` is accepted for protocol uniformity but is a
        no-op until agy exposes a reasoning-effort flag (follow-up #1396).
        """
        if mode not in self.supported_modes:
            raise ValueError(f"AgyAdapter: unsupported mode {mode!r}")

        max_budget_usd = (tool_config or {}).get("max_budget_usd")
        if max_budget_usd is not None:
            _logger.warning(
                "non-claude adapter %s ignoring max_budget_usd=%s; "
                "use hard-timeout/silence-timeout instead",
                self.name,
                max_budget_usd,
            )

        if effort is not None:
            _logger.debug(
                "agy effort %r not yet wired through CLI — "
                "using TUI-selected model default (#1396 follow-up)",
                effort,
            )

        agy_bin = shutil.which("agy") or str(Path.home() / ".local/bin/agy")
        # `--dangerously-skip-permissions` is unconditional: any tool-using
        # prompt (file read, shell call) triggers an interactive permission
        # prompt that would hang a headless dispatch waiting for human input.
        # The `mode` field is retained for runtime accounting + adapter-API
        # parity, but agy has no finer-grained permission model than this
        # single flag. Callers (delegate.py/dispatch_smart.py) should force
        # mode=danger for --agent agy to avoid accidental routes around this.
        cmd: list[str] = [agy_bin, "-p", prompt, "--dangerously-skip-permissions"]

        if session_id:
            cmd.append(f"--conversation={session_id}")

        # Phase-2 follow-up: agy uses `agy plugin` for MCP configuration,
        # not a per-invocation CLI flag like gemini-cli. tool_config is
        # accepted for parity but not acted on yet.
        _ = tool_config
        _ = task_id
        _ = model

        return InvocationPlan(
            cmd=cmd,
            cwd=cwd,
            stdin_payload="",
            output_file=None,
            env_overrides={},
            env_unsets=(),
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
    ) -> ParseResult:
        """Parse ``agy -p`` output.

        Stdout is the only known canonical response source. We deliberately
        do not attempt Gemini-style session-file recovery because no
        Antigravity on-disk session location is known yet.
        """
        _ = output_file
        _ = call_start_time
        _ = plan

        stdout_response = (stdout or "").strip()
        stderr_text = (stderr or "").strip()
        combined = f"{stdout_response}\n{stderr_text}"
        hard_limit_hit = bool(_RATE_LIMIT_RE.search(combined))
        call_failed = returncode != 0 or not bool(stdout_response)
        rate_limited = hard_limit_hit and call_failed

        ok = returncode == 0 and bool(stdout_response) and not rate_limited
        response = stdout_response if ok else ""

        # `stderr_excerpt` follows the documented convention in result.py:
        # populated only when there's diagnostic stderr or the call failed.
        # The model hint is informational and lives in the JSONL audit row
        # via env_overrides, not in stderr_excerpt (which is also used as
        # an error-presence signal by some callers).
        stderr_excerpt: str | None = None
        if not ok:
            excerpt_source = stderr_text or stdout_response
            stderr_excerpt = excerpt_source[:500] or None
        elif stderr_text:
            stderr_excerpt = stderr_text[:500]

        return ParseResult(
            ok=ok,
            response=response,
            stderr_excerpt=stderr_excerpt,
            rate_limited=rate_limited,
            session_id=None,
            tokens=None,
        )

    def liveness_signal_paths(self, plan: InvocationPlan) -> tuple[Path, ...]:
        """Agy has no known on-disk liveness signal; stdout is canonical."""
        _ = plan
        return ()
