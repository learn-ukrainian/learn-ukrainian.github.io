"""ClaudeAdapter — wraps ``npx @anthropic-ai/claude-code@latest`` for the runtime.

Third production adapter. Phase 5 of #1184. Claude is the LAST adapter
to land because it has the most special-case logic:

- **``--bare`` flag**: Skips hooks, LSP, plugin sync, skill walks. Faster
  for scripted calls. Only usable for stateless calls (no session) AND
  when ``ANTHROPIC_API_KEY`` is set (``--bare`` disables OAuth/keychain).

- **``--resume`` vs ``--session-id``**: Two distinct flags with different
  semantics. ``--resume <uuid>`` resumes an existing session (reuses warm
  prompt cache, cheap per call). ``--session-id <uuid>`` starts a NEW
  named session with the given UUID (so future calls can resume it).
  The caller decides which is appropriate; we encode the choice via
  ``tool_config={"is_new_session": bool}``.

- **``--exclude-dynamic-system-prompt-sections``**: CC 2.1.98+ feature
  that improves cross-call prompt caching. Version-gated via
  ``utils.claude_version``.

- **MCP tool restrictions**: ``--mcp-config <path> --allowedTools <list>``
  used by the pipeline reviewers to restrict which MCP tools are
  accessible. Critical for audit gate correctness.

- **``--output-format text``**: Forces plain-text output for machine
  parsing.

Mode handling:
- ``read-only``: No sandbox flag (Claude Code has no explicit sandbox
  for print mode — permissions come from the parent process context).
- ``workspace-write``: Same as read-only for Claude. The distinction
  is enforced by the CALLER deciding whether to pass write-capable
  ``tool_config``, not by a CLI flag.
- ``danger``: Appends ``--dangerously-skip-permissions``. Reserved for
  cases where the caller explicitly needs sandbox bypass.

Liveness paths:
- Returns the project-scoped Claude session JSONL file
  (``~/.claude/projects/<project>/<session>.jsonl``) if we can
  determine it. The runner's mtime poller catches Claude writing
  progress when stdout is buffered or quiet.

Issue: #1184
"""
from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
from functools import cache
from pathlib import Path
from typing import Any

from ..result import ParseResult
from .base import InvocationPlan

_logger = logging.getLogger(__name__)

# Rate-limit patterns (Claude/Anthropic-specific + generic fallbacks)
_RATE_LIMIT_PATTERNS = (
    r"rate limit",
    r"rate_limit",
    r"usage limit",
    r"quota exceeded",
    r"too many requests",
    r"\bHTTP 429\b",
    r"\bstatus 429\b",
    r"\b429\b",
    r"anthropic-rate-limit",
)
_RATE_LIMIT_RE = re.compile("|".join(_RATE_LIMIT_PATTERNS), re.IGNORECASE)

# Anthropic session IDs are UUIDs — used to parse them from stdout if the
# CLI emits them. (Current Claude Code doesn't routinely emit session IDs
# to stdout; the caller passes them IN via tool_config. Parser kept for
# forward compat.)
_SESSION_ID_RE = re.compile(r"session[_-]?id[:=]\s*([0-9a-f-]{8,})", re.IGNORECASE)
_EFFORT_MIN_VERSION = (2, 1, 98)
_MIN_SUPPORTED_CLI_VERSION = (2, 1, 116)
_POSTMORTEM_URL = "https://www.anthropic.com/engineering/april-23-postmortem"


@cache
def _probe_claude_cli_version(cmd_prefix: tuple[str, ...]) -> tuple[int, int, int] | None:
    """Probe ``claude --version`` once per binary prefix for this process."""
    try:
        from utils.claude_version import _parse_claude_semver
    except ImportError:
        return None

    try:
        result = subprocess.run(
            [*cmd_prefix, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None

    combined = f"{result.stdout or ''}\n{result.stderr or ''}".strip()
    return _parse_claude_semver(combined)


def _ensure_supported_claude_cli_version(cmd_prefix: tuple[str, ...]) -> tuple[int, int, int] | None:
    """Reject Claude CLI versions with the 2026-04-23 postmortem regressions."""
    version = _probe_claude_cli_version(cmd_prefix)
    if version is not None and version < _MIN_SUPPORTED_CLI_VERSION:
        raise RuntimeError(
            "Claude CLI < 2.1.116 inherits known quality regressions fixed "
            f"on 2026-04-23 (see {_POSTMORTEM_URL}). Upgrade with: "
            "npm install -g @anthropic-ai/claude-cli@latest"
        )
    return version


class ClaudeAdapter:
    """Adapter for ``npx @anthropic-ai/claude-code@latest`` print mode."""

    name: str = "claude"
    default_model: str = "claude-opus-4-7"
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
        """Build the Claude Code invocation.

        ``tool_config`` keys honored:
            - ``is_new_session: bool`` — if True, use ``--session-id`` (new
              named session); if False or absent, use ``--resume`` (resume
              existing). Only meaningful when ``session_id`` is provided.
            - ``mcp_config_path: str`` — path to .mcp.json for tool restrictions
            - ``allowed_tools: str`` — comma-separated list passed to --allowedTools
            - ``output_format: str`` — defaults to "text"
            - ``use_bare: bool`` — explicit opt-out of --bare (default: auto-enable
              when no session + ANTHROPIC_API_KEY is set)

        ``effort``: optional reasoning-level string. When non-None and the
        probed Claude binary supports ``--effort`` (CC 2.1.98+), the flag
        is appended as ``--effort <level>``. Otherwise we log a warning
        and proceed without the flag. Claude CLI versions below 2.1.116
        are rejected outright due to the 2026-04-23 postmortem gate.
        """
        tc: dict[str, Any] = tool_config or {}

        # Command prefix — respect both the packaged npx path and a local
        # `claude` binary if present. The bridge uses CLAUDE_CMD=["npx", "@anthropic-ai/claude-code@latest"]
        # as the canonical prefix; we default to the same. Callers can
        # override by passing ``tool_config={"cmd_prefix": [...]}``.
        cmd_prefix = tc.get("cmd_prefix")
        if cmd_prefix:
            cmd = [cmd_prefix] if isinstance(cmd_prefix, str) else list(cmd_prefix)
        else:
            claude_bin = shutil.which("claude")
            cmd = [claude_bin] if claude_bin else ["npx", "@anthropic-ai/claude-code@latest"]

        probe_prefix = tuple(cmd)
        cli_version = _ensure_supported_claude_cli_version(probe_prefix)

        cmd.extend(["-p", prompt])

        # --bare: fast path when stateless and API key is set.
        # Disabled if we're resuming/starting a named session (those need
        # full session plumbing).
        has_session = session_id is not None
        use_bare = tc.get("use_bare")
        if use_bare is None:
            # Auto-decide: enable if no session and API key is set
            use_bare = not has_session and bool(os.environ.get("ANTHROPIC_API_KEY"))
        if use_bare and not has_session:
            cmd.append("--bare")

        # Session handling — --session-id (new) vs --resume (existing)
        if has_session:
            is_new = bool(tc.get("is_new_session", False))
            if is_new:
                cmd.extend(["--session-id", session_id])
            else:
                cmd.extend(["--resume", session_id])

        # Model override
        if model:
            cmd.extend(["--model", model])

        # Effort (reasoning level) — version-gated. See #1396.
        if effort is not None:
            # Use the `utils.claude_version.supports_effort` helper so tests
            # can patch the decision at a single point. Inline version
            # comparison bypassed the helper and left CI runs (no Claude CLI
            # installed → cli_version=None) silently dropping --effort even
            # though the test patched supports_effort=True. Root cause of the
            # test_claude_adapter_emits_effort_when_supported CI failure on
            # PR #1474.
            from utils.claude_version import supports_effort
            effort_supported = supports_effort(probe_prefix)
            if effort_supported:
                cmd.extend(["--effort", effort])
            else:
                _logger.warning(
                    "Claude CLI at %s does not support --effort; "
                    "ignoring effort=%r and using CLI default (#1396)",
                    probe_prefix,
                    effort,
                )

        # Output format
        cmd.extend(["--output-format", tc.get("output_format", "text")])

        # Mode-specific flags
        if mode == "danger":
            cmd.append("--dangerously-skip-permissions")
        # read-only and workspace-write use the same Claude invocation;
        # write permission is governed by the caller's tool_config, not
        # a distinct CLI mode flag.

        # MCP tool restrictions (pipeline reviewers)
        mcp_config_path = tc.get("mcp_config_path")
        allowed_tools = tc.get("allowed_tools")
        if mcp_config_path and allowed_tools:
            cmd.extend(["--mcp-config", str(mcp_config_path), "--allowedTools", allowed_tools])

        # Cache-warmth optimization (CC 2.1.98+)
        if cli_version and cli_version >= _EFFORT_MIN_VERSION:
            cmd.append("--exclude-dynamic-system-prompt-sections")

        return InvocationPlan(
            cmd=cmd,
            cwd=cwd,
            stdin_payload="",  # Claude -p takes prompt as positional arg, not stdin
            output_file=None,
            env_overrides={},
            liveness_paths=self._resolve_liveness_paths(cwd),
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
        """Parse Claude CLI output into a ParseResult.

        Claude Code writes the response to stdout. On success, stdout is
        the clean output; on failure, stderr carries the diagnostic.
        """
        # plan / call_start_time unused — Claude doesn't need session-file
        # recovery because the Claude CLI flushes stdout before exit.
        # Kept in the signature to match the uniform protocol (see
        # adapters/base.py).
        _ = output_file  # Unused — Claude doesn't use -o file
        _ = plan
        _ = call_start_time

        # Claude Code 2.1.117 does not document a dedicated rate-limit exit
        # code in `claude --help`, and this runtime currently requests plain
        # text (`--output-format text`), not machine-readable JSON. The safest
        # remaining signal is a rate-limit phrase on stderr from a failed or
        # empty-response call. We intentionally ignore stdout here: successful
        # Claude responses can legitimately discuss "rate limited" without the
        # task being blocked.
        usable_response = bool(stdout.strip())
        failed_call = returncode != 0 or not usable_response
        rate_limited = failed_call and bool(_RATE_LIMIT_RE.search(stderr or ""))

        # Success classification
        ok = returncode == 0 and usable_response and not rate_limited
        response = stdout.strip() if ok else ""

        # Stderr excerpt on failure
        stderr_excerpt: str | None = None
        if not ok:
            excerpt_source = stderr.strip() or stdout.strip() or ""
            stderr_excerpt = excerpt_source[:500] or None

        # Session ID extraction (rare — caller usually passes it IN)
        session_id: str | None = None
        sid_match = _SESSION_ID_RE.search(stdout or "")
        if sid_match:
            session_id = sid_match.group(1)

        return ParseResult(
            ok=ok,
            response=response,
            stderr_excerpt=stderr_excerpt,
            rate_limited=rate_limited,
            session_id=session_id,
            tokens=None,  # Claude CLI doesn't expose tokens in text output
        )

    def liveness_signal_paths(self, plan: InvocationPlan) -> tuple[Path, ...]:
        """Return the project-scoped Claude session JSONL dir for mtime polling.

        We can't know the exact session filename in advance (Claude Code
        creates it when the session starts), so we return the parent
        directory. The runner's mtime poller watches the dir itself, which
        bumps on any child file write — good enough for liveness signal.
        """
        # Caller provided cwd; use it to derive the Claude project dir.
        # The dir is ~/.claude/projects/<project-slug>/ where project-slug
        # is the cwd with special chars replaced.
        _ = plan  # Plan has no cwd; we stored it as env_overrides isn't enough
        # Fall back to the project-wide directory — any recent activity
        # across Claude sessions counts as liveness.
        claude_projects_dir = Path.home() / ".claude" / "projects"
        if claude_projects_dir.exists():
            # Find the most recent project subdir as a best-effort signal
            try:
                subdirs = [p for p in claude_projects_dir.iterdir() if p.is_dir()]
                if subdirs:
                    most_recent = max(subdirs, key=lambda p: p.stat().st_mtime)
                    return (most_recent,)
            except OSError:
                pass
        return ()

    def _resolve_liveness_paths(self, cwd: Path) -> tuple[Path, ...]:
        """Same as liveness_signal_paths but computable at build_invocation time."""
        _ = cwd
        claude_projects_dir = Path.home() / ".claude" / "projects"
        if claude_projects_dir.exists():
            try:
                subdirs = [p for p in claude_projects_dir.iterdir() if p.is_dir()]
                if subdirs:
                    most_recent = max(subdirs, key=lambda p: p.stat().st_mtime)
                    return (most_recent,)
            except OSError:
                pass
        return ()
