"""ClaudeAdapter — wraps the local ``claude`` CLI (npx fallback) for the runtime.

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

- **``--output-format stream-json``**: Forces machine-readable output so
  tool calls can be captured from the CLI trace.

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

import json
import logging
import os
import re
import shutil
import subprocess
from functools import cache
from pathlib import Path
from typing import Any

from ..result import ParseResult
from ..tool_calls import normalize_tool_calls, parse_json_events
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
_DISCUSS_READONLY_TOOL_CONFIG_KEY = "discussion_readonly"
_AGENT_FLAG_MIN_VERSION = (2, 1, 119)


def _isolated_review_response_schema(tool_config: dict[str, Any]) -> str:
    """Return the canonical structured-output schema for isolated reviews."""
    from scripts.review.isolation import (
        ReviewIsolationError,
        canonical_isolated_review_schema,
    )

    changed_paths = tool_config.get("review_changed_paths")
    if not isinstance(changed_paths, list) or not all(
        isinstance(path, str) and path for path in changed_paths
    ):
        raise ValueError("ClaudeAdapter: isolated review changed paths required")
    try:
        schema = canonical_isolated_review_schema(changed_paths)
    except ReviewIsolationError as exc:
        raise ValueError(f"ClaudeAdapter: {exc}") from exc
    return json.dumps(schema, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def _discussion_readonly_requested(tool_config: dict | None) -> bool:
    """Return True when the caller is an ab discuss read-only invocation."""
    return bool(
        os.environ.get("AB_DISCUSS_READONLY") == "1" or (tool_config or {}).get(_DISCUSS_READONLY_TOOL_CONFIG_KEY)
    )


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
            "`claude update` (native install) or "
            "`npm install -g @anthropic-ai/claude-code@latest`"
        )
    return version


def _default_claude_bin() -> str | None:
    """Resolve the native ``claude`` binary: PATH first, then the default
    install target ``~/.local/bin/claude`` (present even when the caller's
    PATH omits it — mirrors ai_agent_bridge._config and start-claude.sh:33).
    Returns None when no native install exists. (deepseek review-4881
    follow-up on #4875.)"""
    found = shutil.which("claude")
    if found:
        return found
    default = Path.home() / ".local/bin/claude"
    if default.is_file():
        return str(default)
    return None


class ClaudeAdapter:
    """Adapter for the ``claude`` CLI in print mode (local binary preferred)."""

    name: str = "claude"
    default_model: str = "claude-opus-4-8"
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
            - ``output_format: str`` — defaults to "stream-json" so tool
              calls can be captured from the CLI trace.
            - ``use_bare: bool`` — explicit opt-out of --bare (default: auto-enable
              when no session + ANTHROPIC_API_KEY is set)
            - ``max_budget_usd: float`` — optional Claude Code print-mode
              API spend cap, emitted as ``--max-budget-usd <amount>``

        ``effort``: optional reasoning-level string. When non-None and the
        probed Claude binary supports ``--effort`` (CC 2.1.98+), the flag
        is appended as ``--effort <level>``. Otherwise we log a warning
        and proceed without the flag. Claude CLI versions below 2.1.116
        are rejected outright due to the 2026-04-23 postmortem gate.
        """
        tc: dict[str, Any] = tool_config or {}
        discussion_readonly = _discussion_readonly_requested(tool_config)
        review_isolation = bool(tc.get("review_isolation"))
        review_write_root: Path | None = None
        if review_isolation:
            from scripts.review.isolation import validated_review_write_root

            review_write_root = validated_review_write_root(tc)
        if discussion_readonly and mode != "read-only":
            raise ValueError("AB_DISCUSS_READONLY requires mode='read-only'")

        # Command prefix — prefer the local native ``claude`` binary; ``npx``
        # is the fallback for machines without a native install (#4875).
        #
        # History (both flips were empirically diagnosed — check before
        # flipping again):
        # - Pre-#1684: local binary first. On 2026-05-05 that let dispatched
        #   runs silently drift behind the npx-managed version (local 2.1.126
        #   vs npx 2.1.128), so #1684 flipped to npx-first.
        # - #4875 (2026-07-10): the ``@anthropic-ai/claude-code`` npm package
        #   became a thin shim around a NATIVE installer — ``npx @latest``
        #   now exits rc=1 in ~8s with "Error: claude native binary not
        #   installed" (stdout empty, no stderr diagnostic). Every dispatched
        #   claude run died at spawn; last successful lane dispatch was
        #   2026-05-31. The native binary on PATH self-updates, so the
        #   #1684 version-drift concern no longer applies; the
        #   ``_ensure_supported_claude_cli_version`` gate below still rejects
        #   stale binaries (< 2.1.116) loudly.
        #
        # Callers can still override by passing
        # ``tool_config={"cmd_prefix": [...]}`` (preserved unchanged).
        cmd_prefix = tc.get("cmd_prefix")
        if review_isolation:
            trusted = tc.get("review_engine_binary")
            if not isinstance(trusted, str) or not Path(trusted).is_absolute():
                raise ValueError("ClaudeAdapter: trusted review_engine_binary required")
            cmd = [trusted]
        elif cmd_prefix:
            cmd = [cmd_prefix] if isinstance(cmd_prefix, str) else list(cmd_prefix)
        else:
            claude_bin = _default_claude_bin()
            if claude_bin:
                cmd = [claude_bin]
            elif shutil.which("npx"):
                cmd = ["npx", "@anthropic-ai/claude-code@latest"]
            else:
                raise RuntimeError(
                    "Cannot dispatch Claude Code: neither a `claude` binary "
                    "nor `npx` was found on PATH. Install the native Claude "
                    "CLI (https://claude.com/claude-code) or Node.js "
                    "(provides npx)."
                )

        probe_prefix = tuple(cmd)
        # Review binaries are probed later, inside the verified OS sandbox.
        cli_version = None if review_isolation else _ensure_supported_claude_cli_version(probe_prefix)

        cmd.append("-p")
        # NB: the actual prompt positional is appended at the END below, after a
        # `--` separator. Reason: Claude CLI uses Commander.js, which parses any
        # argv starting with `-`/`--` as a flag — even in positional position —
        # unless preceded by `--` (end-of-options marker). Channel-context
        # prompts from `ab discuss` start with `--- context: shared (sha256: ...)`
        # which Commander then treats as `unknown option '---'`. The `--`
        # separator makes the parser stop interpreting flags. (Bug surfaced
        # 2026-05-05 during the Claude+Gemini deliberation pilot.)

        # --bare: fast path when stateless and API key is set.
        # Disabled if we're resuming/starting a named session (those need
        # full session plumbing).
        has_session = session_id is not None
        use_bare = tc.get("use_bare")
        if use_bare is None:
            # Auto-decide: enable if no session and API key is set
            use_bare = not has_session and bool(os.environ.get("ANTHROPIC_API_KEY"))
        # Review isolation (#5285): force bare/no-project load when requested.
        if review_isolation or tc.get("use_bare"):
            use_bare = True
        if use_bare and not has_session:
            cmd.append("--bare")
        if review_isolation:
            # Exact read/search tools + empty setting sources: no write/shell
            # tools and no project CLAUDE.md/hooks/skills when flags are honored.
            if "setting_sources" in tc:
                cmd.extend(["--setting-sources", str(tc.get("setting_sources") or "")])
            cmd.extend(["--tools", str(tc.get("allowed_tools") or "")])
            mcp_config_path = tc.get("mcp_config_path")
            if not tc.get("strict_mcp_config") or not isinstance(mcp_config_path, str):
                raise ValueError("ClaudeAdapter: isolated review requires strict empty MCP config")
            mcp_path = Path(mcp_config_path)
            try:
                mcp_resolved = mcp_path.resolve(strict=True)
            except OSError as exc:
                raise ValueError("ClaudeAdapter: invalid isolated review MCP config path") from exc
            if (
                review_write_root is None
                or not mcp_path.is_absolute()
                or not mcp_resolved.is_relative_to(review_write_root)
                or not mcp_path.is_file()
                or mcp_path.is_symlink()
            ):
                raise ValueError("ClaudeAdapter: invalid isolated review MCP config path")
            if mcp_resolved.read_bytes() != b'{"mcpServers":{}}\n':
                raise ValueError("ClaudeAdapter: isolated review MCP config is not empty")
            cmd.extend(["--strict-mcp-config", "--mcp-config", str(mcp_resolved)])
            cmd.extend(["--json-schema", _isolated_review_response_schema(tc)])

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

        max_budget_usd = tc.get("max_budget_usd")
        if max_budget_usd is not None:
            # Claude Code only honors --max-budget-usd in print mode. This
            # adapter always uses -p, so the constraint is satisfied here.
            cmd.extend(["--max-budget-usd", f"{float(max_budget_usd):.2f}"])

        # Effort (reasoning level) — version-gated. See #1396.
        if effort is not None and not review_isolation:
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
                    "Claude CLI at %s does not support --effort; ignoring effort=%r and using CLI default (#1396)",
                    probe_prefix,
                    effort,
                )

        # Output format
        output_format = str(tc.get("output_format", "stream-json"))
        if output_format != "stream-json":
            raise ValueError(
                "ClaudeAdapter requires tool_config output_format='stream-json' "
                "so tool-call trace parsing fails closed instead of degrading "
                f"to text output; got {output_format!r}"
            )
        cmd.extend(["--output-format", output_format])
        cmd.append("--verbose")

        if discussion_readonly:
            cmd.extend(["--tools", "Read,Grep,Glob,LS"])

        requested_agent = tc.get("agent")
        if requested_agent:
            if cli_version and cli_version < _AGENT_FLAG_MIN_VERSION:
                raise RuntimeError(
                    f"Claude CLI < 2.1.119 does not support --agent for print-mode subprocesses; got {cli_version!r}."
                )
            cmd.extend(["--agent", str(requested_agent)])

        # Mode-specific flags
        if mode == "danger":
            cmd.append("--dangerously-skip-permissions")
        # read-only and workspace-write use the same Claude invocation;
        # write permission is governed by the caller's tool_config, not
        # a distinct CLI mode flag.

        # MCP tool restrictions (pipeline reviewers)
        mcp_config_path = tc.get("mcp_config_path")
        allowed_tools = tc.get("allowed_tools")
        if mcp_config_path and allowed_tools and not review_isolation:
            cmd.extend(["--mcp-config", str(mcp_config_path), "--allowedTools", allowed_tools])

        # Cache-warmth optimization (CC 2.1.98+)
        if cli_version and cli_version >= _EFFORT_MIN_VERSION:
            cmd.append("--exclude-dynamic-system-prompt-sections")

        # Large sealed review dossiers can exceed execve ARG_MAX. Claude print
        # mode accepts text on stdin, so the isolation path never places review
        # evidence in argv. Ordinary calls retain the positional behavior.
        if not review_isolation:
            # Prompt positional MUST be last, preceded by `--` end-of-options marker.
            # See comment near `cmd.append("-p")` above for the Commander.js rationale.
            cmd.extend(["--", prompt])

        return InvocationPlan(
            cmd=cmd,
            cwd=cwd,
            stdin_payload=prompt if review_isolation else "",
            output_file=None,
            env_overrides={"AB_DISCUSS_READONLY": "1"} if discussion_readonly else {},
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
        _ = output_file  # Unused — Claude doesn't use -o file
        _ = call_start_time

        events = parse_json_events(stdout, source="claude", logger=_logger)
        tool_calls = normalize_tool_calls(events)
        stream_response = _extract_stream_json_response(events)
        effective_stdout = stream_response if events else stdout.strip()

        session_id: str | None = None
        sid_match = _SESSION_ID_RE.search(stdout or "")
        if sid_match:
            session_id = sid_match.group(1)
        for event in events:
            sid = event.get("session_id") or event.get("sessionId")
            if isinstance(sid, str) and sid:
                session_id = sid
                break

        # Session JSONL is authoritative when stream-json stdout drops tool rows
        # (measured: subscription tooled bakeoff cells with MCP, 2026-07-08).
        if plan is not None and plan.cwd is not None and session_id:
            session_path = _claude_session_jsonl_path(plan.cwd, session_id)
            if session_path is not None:
                recovered = _tool_calls_from_claude_session_jsonl(session_path)
                if len(recovered) > len(tool_calls):
                    tool_calls = recovered

        # Claude Code 2.1.117 does not document a dedicated rate-limit exit
        # code in `claude --help`. The safest remaining signal is a
        # rate-limit phrase on stderr from a failed or empty-response call.
        # We intentionally ignore stdout here: successful Claude responses can
        # legitimately discuss "rate limited" without the task being blocked.
        usable_response = bool(effective_stdout)
        failed_call = returncode != 0 or not usable_response
        rate_limited = failed_call and bool(_RATE_LIMIT_RE.search(stderr or ""))

        # Success classification
        ok = returncode == 0 and usable_response and not rate_limited
        response = effective_stdout if ok else ""

        # Stderr excerpt on failure
        stderr_excerpt: str | None = None
        if not ok:
            excerpt_source = stderr.strip() or effective_stdout or stdout.strip() or ""
            stderr_excerpt = excerpt_source[:500] or None

        return ParseResult(
            ok=ok,
            response=response,
            stderr_excerpt=stderr_excerpt,
            rate_limited=rate_limited,
            session_id=session_id,
            tokens=None,  # Claude CLI doesn't expose tokens in text output
            tool_calls=tool_calls,
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


def _claude_project_slug(cwd: Path) -> str:
    return str(cwd.resolve()).replace("/", "-")


def _claude_session_jsonl_path(cwd: Path, session_id: str) -> Path | None:
    candidate = Path.home() / ".claude" / "projects" / _claude_project_slug(cwd) / f"{session_id}.jsonl"
    return candidate if candidate.is_file() else None


def _tool_calls_from_claude_session_jsonl(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return normalize_tool_calls(events)


def _extract_stream_json_response(events: list[dict[str, Any]]) -> str:
    """Extract assistant text from Claude ``--output-format stream-json`` events."""
    result_text = ""
    structured_output: dict[str, Any] | None = None
    text_parts: list[str] = []
    for event in events:
        structured = event.get("structured_output")
        if isinstance(structured, dict):
            structured_output = structured
        result = event.get("result")
        if isinstance(result, str) and result.strip():
            result_text = result.strip()
        message = event.get("message")
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, list):
                for item in content:
                    if not isinstance(item, dict):
                        continue
                    if item.get("type") == "text" and isinstance(item.get("text"), str):
                        text_parts.append(item["text"])
        content = event.get("content")
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str):
                    text_parts.append(item["text"])
        elif isinstance(content, str) and event.get("type") in {"text", "assistant"}:
            text_parts.append(content)
    if structured_output is not None:
        return json.dumps(structured_output, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    if result_text:
        return result_text
    return "\n".join(part.strip() for part in text_parts if part.strip()).strip()
