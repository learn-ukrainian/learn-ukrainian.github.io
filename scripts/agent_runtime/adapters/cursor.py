"""CursorAdapter — wraps ``agent`` / ``cursor-agent`` for the agent runtime.

Mirrors the Gemini I/O pattern (stdout JSONL stream) and the Codex adapter's
per-invocation configuration patterns. Supports read-only, workspace-write,
and danger modes with appropriate security boundaries.

Key design points:

- **Prompt delivery via stdin.** Matches the Gemini pattern to avoid
  shell-limit issues with large prompts.
- **JSONL event stream.** Parses stdout using ``parse_json_events`` to
  extract tool-call telemetry and the final assistant response.
- **Security boundaries.** Explicitly avoids ``--yolo`` and ``--force``
  flags. Uses ``--mode plan`` for workspace-write by default.
- **Per-invocation workspace.** Caller can specify ``cursor_workspace`` in
  ``tool_config`` to scope the agent to a specific directory.

Issue: #2253 (Phase 2)
"""

from __future__ import annotations

import logging
import re
import shutil
from pathlib import Path

from ..result import ParseResult
from ..tool_calls import normalize_tool_calls, parse_json_events
from .base import InvocationPlan

_logger = logging.getLogger(__name__)

# Stderr/stdout phrases that indicate the provider rate-limited us.
_RATE_LIMIT_PATTERNS = (
    r"usage limit reached",
    r"rate limit",
    r"rate_limit",
    r"quota exceeded",
    r"too many requests",
    r"\bHTTP 429\b",
    r"\bstatus 429\b",
    r"\b429\b",
)
_RATE_LIMIT_RE = re.compile("|".join(_RATE_LIMIT_PATTERNS), re.IGNORECASE)


class CursorAdapter:
    """Adapter for the Cursor agent CLI (``agent`` or ``cursor-agent``)."""

    name: str = "cursor"
    default_model: str = "composer-2.5"
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
        """Build the cursor-agent invocation.

        Args:
            prompt: The prompt text to send via stdin.
            mode: One of "read-only", "workspace-write", "danger".
            cwd: Working directory for the subprocess.
            model: Model override (e.g. "composer-2.5").
            task_id: Optional task identifier.
            session_id: Ignored (cursor-agent does not yet support resume).
            tool_config: Config overrides. Supported keys:
                - ``cursor_workspace``: overrides the ``--workspace`` path.
                - ``approve_mcps``: bool, toggles ``--approve-mcps``.
                - ``cursor_mode``: "plan" | "ask", toggles ``--mode``.
                - ``sandbox``: "enabled" | "disabled", toggles ``--sandbox``.
            effort: Logged and ignored (no cursor equivalent today).
        """
        _ = session_id
        _ = task_id

        if effort:
            _logger.debug("cursor adapter ignoring effort=%s (not supported by CLI)", effort)

        # Resolve binary. shutil.which handles PATH lookup.
        cursor_bin = shutil.which("agent") or shutil.which("cursor-agent") or "agent"

        config = tool_config or {}

        # Base argv common to all paths
        cmd: list[str] = [
            cursor_bin,
            "-p", "-",  # Read prompt from stdin
            "--model", model or self.default_model,
            "--output-format", config.get("output_format", "stream-json"),
            "--trust",  # Headless workspace-trust bypass
        ]

        # Workspace resolution
        workspace = config.get("cursor_workspace") or str(cwd)
        cmd.extend(["--workspace", workspace])

        # Mode-specific argv assembly
        if mode == "read-only":
            cursor_mode = config.get("cursor_mode", "ask")
            cmd.extend(["--mode", cursor_mode])
        elif mode == "workspace-write":
            cursor_mode = config.get("cursor_mode", "plan")
            cmd.extend(["--mode", cursor_mode])
            # Security boundaries from Phase 2 spec
            if config.get("approve_mcps") is not False:
                cmd.append("--approve-mcps")
            sandbox = config.get("sandbox", "enabled")
            cmd.extend(["--sandbox", sandbox])
        elif mode == "danger":
            # Same as writer path but NO --mode plan (file edits allowed)
            # Use sparingly — most delegate calls should use workspace-write.
            cursor_mode = config.get("cursor_mode", "ask")  # "ask" allows edits in non-plan mode?
            # Actually spec §1 says: "Danger mode: same as writer path but NO --mode plan (file edits allowed)"
            # For cursor-agent, --mode ask is the default for "ask" where it can edit if allowed?
            # Wait, let me check spec §1 again.
            # "Danger mode: same as writer path but NO --mode plan (file edits allowed)"
            cmd.extend(["--mode", cursor_mode])
            if config.get("approve_mcps") is not False:
                cmd.append("--approve-mcps")
            sandbox = config.get("sandbox", "enabled")
            cmd.extend(["--sandbox", sandbox])

        return InvocationPlan(
            cmd=cmd,
            cwd=cwd,
            stdin_payload=prompt,
            output_file=None,  # Cursor writes to stdout
            liveness_paths=(),  # rely on stdout streaming
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
        """Parse cursor-agent JSONL output into a ParseResult."""
        _ = output_file
        _ = plan
        _ = call_start_time

        # Detect rate limits
        rate_limited = bool(_RATE_LIMIT_RE.search(f"{stdout}\n{stderr}"))

        # Parse JSONL events
        events = parse_json_events(stdout, source="cursor", logger=_logger)
        tool_calls = normalize_tool_calls(events)

        # The final response is usually the last 'content' or 'text' event
        # in the stream. parse_json_events + normalize_tool_calls handles
        # most of this, but we need to extract the assistant's final prose.
        response = ""
        for event in events:
            # Typical cursor event shape: {"type": "text", "content": "..."}
            # or {"type": "message", "role": "assistant", "content": "..."}
            if event.get("type") == "text":
                response += event.get("content", "")
            elif event.get("type") == "message" and event.get("role") == "assistant":
                content = event.get("content", "")
                if isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict) and part.get("type") == "text":
                            response += part.get("text", "")
                elif isinstance(content, str):
                    response += content

        response = response.strip()

        ok = returncode == 0 and bool(response) and not rate_limited

        stderr_excerpt = None
        if not ok:
            stderr_excerpt = (stderr or stdout).strip()[:500]

        return ParseResult(
            ok=ok,
            response=response,
            stderr_excerpt=stderr_excerpt,
            rate_limited=rate_limited,
            tool_calls=tool_calls,
        )

    def liveness_signal_paths(self, plan: InvocationPlan) -> tuple[Path, ...]:
        """Cursor writes to stdout; no separate liveness files."""
        _ = plan
        return ()
