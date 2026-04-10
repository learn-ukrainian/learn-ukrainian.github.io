"""GeminiAdapter — wraps ``gemini`` CLI (Google AI Studio / Gemini CLI) for the runtime.

Second real adapter. Pressure-tests the protocol against the RICHEST existing
flag requirements in the codebase:

- MCP tool restrictions via ``--allowed-mcp-server-names`` (used by
  ``scripts/build/dispatch.py`` for pipeline reviewers to restrict tool
  access).
- Stall detection: the prior art in ``_gemini.py::_stream_with_watchdog``
  was specifically built because Gemini CLI stalls frequently. Our runtime's
  stall watchdog covers this case uniformly — GeminiAdapter doesn't need a
  custom implementation, just the right ``stall_timeout`` default.
- Rate-limit detection: Gemini returns ``RESOURCE_EXHAUSTED``, ``quota
  exceeded``, and occasionally ``No capacity available`` depending on
  backend. Patterns match dispatch.py prior art.
- No session IDs. Gemini CLI doesn't expose them, so ``parse_response``
  returns ``session_id=None`` always. Resume policy is ``bridge_only``
  for cost economics, but session IDs come from the bridge's own SQLite
  ``sessions`` table and are passed in as ``session_id=...`` — we just
  ignore it here because the CLI has no ``--resume`` equivalent anyway.

Key differences from CodexAdapter:
- Output to stdout (no ``-o <file>``); ``output_file`` stays None.
- No sandbox flags. Gemini CLI uses ``--approval-mode=yolo`` for
  writable mode; read-only is the default. There is no ``danger`` mode
  distinct from ``workspace-write``.
- Liveness paths = () — stdout streaming is the only signal we need,
  and it's sufficient because Gemini CLI always writes to stdout.

Issue: #1184
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

from ..result import ParseResult
from .base import InvocationPlan

# Rate-limit patterns — combined with \b boundaries for numeric codes
# to prevent URL false positives (Gemini review finding #5 on #1179 applies here too).
_RATE_LIMIT_PATTERNS = (
    r"RESOURCE_EXHAUSTED",
    r"usage limit reached",
    r"rate limit",
    r"rate_limit",
    r"quota exceeded",
    r"too many requests",
    r"No capacity available",
    r"\bHTTP 429\b",
    r"\bstatus 429\b",
    r"\b429\b",
)
_RATE_LIMIT_RE = re.compile("|".join(_RATE_LIMIT_PATTERNS), re.IGNORECASE)


class GeminiAdapter:
    """Adapter for the ``gemini`` CLI (Google Gemini)."""

    name: str = "gemini"
    default_model: str = "gemini-3.1-pro-preview"
    # Gemini has no sandbox distinction between workspace-write and danger —
    # we accept both names but treat them identically (both mean "CLI may
    # write files in cwd via --approval-mode=yolo").
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
    ) -> InvocationPlan:
        """Build the ``gemini`` CLI invocation.

        Defensively ignores ``session_id``: Gemini CLI has no ``--resume``
        equivalent. The bridge tracks session IDs in its own SQLite table
        and uses them for conversation-context injection into the prompt,
        not for CLI-level resume. We silently drop it here.

        Supports ``tool_config``:
            - ``{"mcp_server_names": ["rag", "other"]}`` → appended as
              ``--allowed-mcp-server-names rag,other``
            - Any other keys are ignored (forward-compatible).
        """
        gemini_bin = shutil.which("gemini") or "gemini"

        cmd: list[str] = [
            gemini_bin,
            "-m", model or self.default_model,
        ]

        # Approval mode: read-only is the default; yolo for write modes.
        # "danger" is treated identically to "workspace-write" because
        # Gemini CLI has no stricter-than-yolo bypass.
        if mode in ("workspace-write", "danger"):
            cmd.append("--approval-mode=yolo")

        # MCP tool restriction via tool_config.
        if tool_config:
            mcp_server_names = tool_config.get("mcp_server_names")
            if mcp_server_names:
                if isinstance(mcp_server_names, (list, tuple)):
                    joined = ",".join(mcp_server_names)
                else:
                    joined = str(mcp_server_names)
                cmd.extend(["--allowed-mcp-server-names", joined])

        # Silently ignore session_id (CLI has no equivalent) and task_id
        # (we don't need it here — runner already logs it via usage record).
        _ = session_id
        _ = task_id

        return InvocationPlan(
            cmd=cmd,
            stdin_payload=prompt,
            output_file=None,  # Gemini writes to stdout only.
            env_overrides={},
            liveness_paths=(),  # stdout streamer is sufficient.
        )

    def parse_response(
        self,
        *,
        stdout: str,
        stderr: str,
        returncode: int,
        output_file: Path | None,
    ) -> ParseResult:
        """Parse Gemini CLI output into a ParseResult.

        Gemini writes the final response to stdout. We trust returncode=0
        as success, fall back to rate-limit detection if non-zero.
        """
        _ = output_file  # unused — Gemini doesn't use -o

        # Check rate limit across stdout + stderr (patterns can appear in either)
        combined_for_rl = f"{stdout}\n{stderr}"
        rate_limited = bool(_RATE_LIMIT_RE.search(combined_for_rl))

        # Success = exit 0, some stdout, not rate-limited.
        ok = returncode == 0 and bool(stdout.strip()) and not rate_limited
        response = stdout.strip() if ok else ""

        stderr_excerpt: str | None = None
        if not ok:
            # Prefer stderr; fall back to stdout if stderr is empty
            # (some Gemini errors land in stdout, especially quota messages).
            excerpt_source = stderr.strip() or stdout.strip() or ""
            stderr_excerpt = excerpt_source[:500] or None

        return ParseResult(
            ok=ok,
            response=response,
            stderr_excerpt=stderr_excerpt,
            rate_limited=rate_limited,
            session_id=None,  # Gemini CLI doesn't expose session IDs.
            tokens=None,      # Nor tokens.
        )

    def liveness_signal_paths(self, plan: InvocationPlan) -> tuple[Path, ...]:
        """Return empty — stdout streaming is the only liveness signal we need.

        Gemini CLI writes to stdout continuously (it's how ``_stream_with_watchdog``
        worked in the prior art). The runner's stdout streamer catches every
        line; no fallback mtime polling needed.

        Gemini DOES write to ``~/.gemini/tmp/<project>/chats/<session>.json``
        but (a) we don't know the project name at adapter level without
        parsing gemini-cli config, and (b) stdout streaming already covers
        the liveness need for this CLI. Leaving the session file path out
        keeps the adapter simple.
        """
        _ = plan
        return ()
