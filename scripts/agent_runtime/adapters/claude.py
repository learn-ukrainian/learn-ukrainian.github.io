"""ClaudeAdapter — wraps the local ``claude`` CLI (npx fallback) for the runtime.

Third production adapter. Phase 5 of #1184. Claude is the LAST adapter
to land because it has the most special-case logic:

- **``--bare`` flag**: Skips hooks, so guarded headless workers never use it,
  even when an API key is available.

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
- ``read-only`` with ``reviewer_tools=True`` and no explicit ``allowed_tools``:
  ``dontAsk`` permits
  read/search and shell execution (including tests and Python) while denying
  edits and common Git/GitHub mutations. The reviewer's MCP servers never come
  from the reviewed checkout: ``--strict-mcp-config`` loads only a
  harness-built ``sources`` server, started over stdio from the primary
  checkout's interpreter and server script under ``env -i`` and ``python -I``
  (``review_mcp.isolated_sources_mcp_config``), so neither a branch's
  ``.mcp.json`` nor the environment its project settings set can add a
  server, point ``sources`` elsewhere, or run code in the server before it
  starts. Each read-only ``sources`` tool is allowed by name. An
  ``mcp_config_path`` is accepted only for a formal full-access attempt,
  whose harness-written config and tool contract are unchanged. Explicit
  caller tool lists pass through unchanged and do not receive reviewer-only
  restrictions.
  Every ``read-only`` invocation, whatever its profile (ordinary or formal
  reviewer, explicit caller list, ``discussion_readonly``,
  ``review_isolation``, or none), denies each ``sources`` tool that persists
  a live fetch (``sources_read_only.sources_tool_sets``), as
  ``mcp__sources__<tool>`` and as ``mcp__*__<tool>`` so a server registered
  under another name is covered. Deny wins over any allow rule, including
  ``mcp__<server>__*`` and the user's global settings.
  Prefix Bash denies are advisory; the repository PreToolUse guards are the
  primary-checkout write backstop. Claude's bubblewrap sandbox did not stop
  a primary-checkout write in a live probe, so it is not that backstop.
- ``workspace-write``: ``--permission-mode dontAsk`` plus an allow list of
  every worker tool: all Bash, Read/Edit/Write, Grep/Glob/LS, WebFetch,
  WebSearch, and one ``mcp__<server>__*`` rule per server in the worker
  checkout ``.mcp.json`` (the dispatch ``cwd``). An explicit
  ``mcp_config_path`` is read instead. A missing file grants no MCP tools.
  A present file that cannot be read or parsed, or a server name that cannot
  be written into ``--allowedTools``, fails the dispatch. NotebookEdit is
  omitted: the primary-checkout PreToolUse matcher covers Bash and
  Write|Edit|MultiEdit, so a notebook edit would miss that guard. Headless
  ``-p`` otherwise starts in manual mode and denies every tool that would
  prompt. ``acceptEdits`` still prompts for shell and network. ``auto`` can
  refuse a legitimate worker action. ``bypassPermissions`` is not used. It
  still runs hooks, but it approves every tool with no allow list.
  ``--dangerously-skip-permissions`` stays on the danger argv. ``--bare`` is
  what skips hooks. An allow glob ``mcp__*`` is ignored, so each configured
  server is named. The reviewer and sources-writer deny lists do not apply
  (builds and writers keep their cache access). An explicit
  ``allowed_tools`` value stays the sole allow list.
  Threat model: read-only is not a sandbox against the reviewed branch. The
  reviewer runs branch code through its own Bash tool (its tests, for
  example), and that code can write wherever the user can. The reviewer's MCP
  grant must not add a write path beyond that one: the ``sources`` server it
  loads is launched by the harness, not the branch, and every tool it is
  granted is read-only in behavior (``tests/mcp/test_sources_tool_side_effects.py``).
  Whatever the session applies to every process it starts (Bash and hooks
  included) is reviewer-sandbox hardening, outside this grant.
- ``danger``: Appends ``--dangerously-skip-permissions``. Reserved for
  cases where the caller explicitly needs sandbox bypass.
Every headless invocation receives shared PreToolUse guard settings from the
tracked checkout. A hook that exits 2 still blocks the call under
``dontAsk``. ``--bare`` is what skips hooks. Sealed ``review_isolation``
retains ``--safe-mode`` and its OS sandbox; safe mode suppresses hooks and
shell/write tools there.

No background work (#9690): a print-mode run exits when its final turn ends,
so a task it left in the background is killed or never reported. Every
invocation sets ``CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1`` (Bash rejects
``run_in_background``, a requested background subagent runs in the
foreground, MCP calls are not auto-backgrounded) and its ``--settings`` deny
the tools that start or schedule work outside the turn, which that variable
leaves available: Monitor, ScheduleWakeup, CronCreate and Workflow.

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
import shlex
import shutil
import subprocess
from functools import cache
from pathlib import Path
from typing import Any

from ..jsonl import jsonl_lines
from ..result import ParseResult
from ..sources_read_only import sources_tool_sets
from ..tool_calls import normalize_tool_calls, parse_json_events
from ._output_schema import json_value, load_output_schema, plan_output_schema, schema_metadata, structured_result
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
_POSTMORTEM_URL = "https://www.anthropic.com/engineering/april-23-postmortem"
_DISCUSS_READONLY_TOOL_CONFIG_KEY = "discussion_readonly"
_AGENT_FLAG_MIN_VERSION = (2, 1, 119)

# Installed Claude Code 2.1.283 ``--permission-mode`` value for a headless
# worker. dontAsk runs pre-approved tools and denies anything that would
# prompt, so the session never waits. bypassPermissions still runs hooks;
# it is unused here because it approves every tool with no allow list.
WORKSPACE_WRITE_PERMISSION_MODE = "dontAsk"

# Bare tool names match every use. An allow glob ``mcp__*`` is ignored, so
# each configured server is named as ``mcp__<server>__*``. NotebookEdit is
# absent: its PreToolUse matcher does not include the primary-checkout guard.
_WORKSPACE_WRITE_TOOLS = (
    "Bash",
    "Read",
    "Edit",
    "Write",
    "Grep",
    "Glob",
    "LS",
    "WebFetch",
    "WebSearch",
)
_MCP_SERVER_NAME_RE = re.compile(r"^[A-Za-z0-9_-]+$")

# A headless run ends with its final turn: background work it started is lost
# (#9690). Live probes, Claude Code 2.1.289: this variable makes Bash reject
# ``run_in_background`` and runs a requested background subagent in the
# foreground. Monitor, ScheduleWakeup, CronCreate and Workflow stay available
# under it and still start or schedule work past the turn, so they are denied
# by name; a settings deny removes them in dontAsk, bypass and default modes.
# env_sanitize allowlists the variable for the claude provider, and for kimi
# only from adapter overrides. KimiccHarness reuses both constants.
HEADLESS_BACKGROUND_ENV = {"CLAUDE_CODE_DISABLE_BACKGROUND_TASKS": "1"}
HEADLESS_BACKGROUND_TOOL_DENIES = ("Monitor", "ScheduleWakeup", "CronCreate", "Workflow")

# Reader and writer tools come from the sources server's annotations
# (``sources_read_only.sources_tool_sets``). tests/mcp/test_sources_tool_side_effects.py
# ties the annotations to the writes each tool is observed to attempt, so a new
# or write-capable tool is denied to read-only runs without editing a list here.
SOURCES_MCP_SERVER = "sources"

# Ordinary Claude reviewers need a non-interactive shell. Claude Bash deny
# patterns match prefixes only: git -C, wrappers, and interpreters can bypass
# them. The shared PreToolUse guards below provide the checkout backstop.
REVIEWER_PERMISSION_PROFILE = {
    "mode": "dontAsk",
    "allow": ("Read", "Grep", "Glob", "LS", "Bash", "WebFetch", "WebSearch"),
    "deny": (
        "Edit",
        "Write",
        "NotebookEdit",
        "Bash(git push *)",
        "Bash(git commit *)",
        "Bash(git merge *)",
        "Bash(git rebase *)",
        "Bash(git reset *)",
        "Bash(git tag *)",
        "Bash(git branch -D *)",
        "Bash(gh pr merge *)",
        "Bash(gh pr create *)",
        "Bash(gh pr comment *)",
        "Bash(gh pr review *)",
        "Bash(gh pr edit *)",
        "Bash(gh pr close *)",
        "Bash(gh pr reopen *)",
        "Bash(gh issue create *)",
        "Bash(gh issue comment *)",
        "Bash(gh issue edit *)",
        "Bash(gh issue close *)",
        "Bash(gh issue reopen *)",
        "Bash(gh api -X *)",
        "Bash(gh api --method *)",
        "Bash(gh release *)",
        "Bash(gh api -f *)",
        "Bash(gh api -F *)",
        "Bash(gh api --field *)",
        "Bash(gh api --raw-field *)",
        "Bash(gh api --input *)",
        "Bash(gh workflow run *)",
    ),
}


def _mcp_config_path(cwd: Path, tool_config: dict[str, Any]) -> Path:
    """Return the MCP config a write worker's allow list is built from.

    An explicit ``mcp_config_path`` wins. Otherwise the file is the worker
    checkout's ``.mcp.json`` (the dispatch ``cwd``), not the checkout that
    imported this adapter.
    """
    explicit = tool_config.get("mcp_config_path")
    if isinstance(explicit, str) and explicit:
        return Path(explicit)
    return Path(cwd) / ".mcp.json"


def _mcp_server_names(path: Path) -> tuple[str, ...]:
    """Return MCP server names from a Claude config file.

    A missing file grants no servers. A present file that cannot be read or
    parsed, or a server name that cannot be written into a comma-separated
    ``--allowedTools`` value, fails the dispatch instead of dropping the
    server.
    """
    try:
        path.lstat()
    except FileNotFoundError:
        return ()
    except OSError as exc:
        raise ValueError(f"ClaudeAdapter: MCP config {path} is unreadable: {exc}") from exc
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"ClaudeAdapter: MCP config {path} is unreadable: {exc}") from exc
    except (OSError, UnicodeError) as exc:
        raise ValueError(f"ClaudeAdapter: MCP config {path} is unreadable: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"ClaudeAdapter: MCP config {path} is invalid JSON: {exc}") from exc
    servers = data.get("mcpServers") if isinstance(data, dict) else None
    if not isinstance(servers, dict):
        raise ValueError(f"ClaudeAdapter: MCP config {path} must be a JSON object with an mcpServers object")
    names: list[str] = []
    for name in servers:
        if not isinstance(name, str) or not _MCP_SERVER_NAME_RE.fullmatch(name):
            raise ValueError(f"ClaudeAdapter: MCP server name {name!r} in {path} cannot be expressed in --allowedTools")
        names.append(name)
    return tuple(names)


def _workspace_write_allows(cwd: Path, tool_config: dict[str, Any]) -> tuple[str, ...]:
    """Tools a headless write worker may run without a prompt."""
    names: list[str] = list(_WORKSPACE_WRITE_TOOLS)
    for server in _mcp_server_names(_mcp_config_path(cwd, tool_config)):
        names.append(f"mcp__{server}__*")
    return tuple(dict.fromkeys(names))


def _sources_rules(tools: tuple[str, ...]) -> list[str]:
    return [f"mcp__{SOURCES_MCP_SERVER}__{name}" for name in tools]


def _sources_writer_denies(tools: tuple[str, ...]) -> list[str]:
    """Deny each writer under every server name, not only the canonical ``sources``.

    Claude matches MCP rules against the configured server name, so a config,
    project ``.mcp.json``, user config, or plugin that registers the server as,
    say, ``sources_alias`` would escape ``mcp__sources__<tool>``. Deny rules
    accept a glob that must match the whole tool name: ``mcp__*__<tool>``
    removes ``<tool>`` from every server and leaves longer reader names such as
    ``query_ulif_records`` alone (live probe, Claude Code 2.1.288). A
    same-named tool on another server is denied too, which fails closed. The
    exact canonical rule stays first and does not depend on glob support.
    """
    return [*_sources_rules(tools), *(f"mcp__*__{name}" for name in tools)]


def _reviewer_mcp_config() -> str:
    """The ordinary reviewer's only MCP configuration: the trusted stdio sources server.

    Built by the harness from the primary checkout, never read from the
    reviewed checkout, and passed inline with ``--strict-mcp-config``. The
    server starts with a pinned environment and isolated Python startup.
    """
    from scripts.agent_runtime.review_mcp import isolated_sources_mcp_config, sources_server_launch

    return json.dumps(isolated_sources_mcp_config(*sources_server_launch()), separators=(",", ":"))


_DEPLOYED_HOOKS_PREFIX = "$CLAUDE_PROJECT_DIR/.claude/hooks/"
_PROJECT_PYTHON_HOOK_WRAPPER = "run-project-python-hook.sh"
# Guards that need the project interpreter (their parser dependency is not in
# the system Python). Only these may appear in the wrapper form.
PROJECT_PYTHON_GUARDS = frozenset({"guard-pr-merge.py", "guard-admin-merge.py", "guard-branch-switch-in-main.py"})
# A command whose raw text or shell words contain any of these is a fleet guard
# and must take one of the two supported forms.
_FLEET_GUARD_MARKERS = (".claude/hooks/", _PROJECT_PYTHON_HOOK_WRAPPER, *sorted(PROJECT_PYTHON_GUARDS))


def _worker_guard_invocation(command: str, source_root: Path) -> str | None:
    """Translate one deployed hook command into a tracked-source invocation.

    The command is split into shell words first, so quoting and escaping never
    change its classification; an unreadable command raises. The single word
    ``$CLAUDE_PROJECT_DIR/.claude/hooks/<guard>`` becomes the tracked guard
    path. The words ``bash $CLAUDE_PROJECT_DIR/.claude/hooks/run-project-python-hook.sh
    <guard>`` become the project interpreter plus the tracked guard, for the
    guards in ``PROJECT_PYTHON_GUARDS`` only. Any other command naming the hooks
    directory, the wrapper or one of those guards raises, so a guard is never
    silently dropped. Commands naming none of them are not fleet guards and
    return ``None``.
    """
    try:
        argv = shlex.split(command)
    except ValueError as exc:
        raise RuntimeError(f"Claude worker hook command is unreadable: {command}") from exc
    if not any(marker in text for text in (command, *argv) for marker in _FLEET_GUARD_MARKERS):
        return None
    hooks_dir = source_root / "agents_extensions/shared/hooks"
    wrapper = _DEPLOYED_HOOKS_PREFIX + _PROJECT_PYTHON_HOOK_WRAPPER
    if len(argv) == 3 and argv[:2] == ["bash", wrapper] and argv[2] in PROJECT_PYTHON_GUARDS:
        tracked = hooks_dir / argv[2]
        if not tracked.is_file():
            raise RuntimeError(f"Claude worker guard unavailable: {tracked}")
        from scripts.common.repo_root import project_interpreter

        return shlex.join([str(project_interpreter(source_root)), str(tracked)])
    plain = len(argv) == 1 and argv[0].startswith(_DEPLOYED_HOOKS_PREFIX)
    name = argv[0].removeprefix(_DEPLOYED_HOOKS_PREFIX) if plain else ""
    if name not in {"", ".", "..", _PROJECT_PYTHON_HOOK_WRAPPER} and "/" not in name:
        tracked = hooks_dir / name
        if not tracked.is_file():
            raise RuntimeError(f"Claude worker guard unavailable: {tracked}")
        return shlex.quote(str(tracked))
    raise RuntimeError(f"Claude worker guard has an unsupported form: {command}")


def _worker_guard_settings(*, publish_guard: bool = False) -> str:
    """Build hook settings from tracked sources in this checkout."""
    source_root = Path(__file__).resolve().parents[3]
    source = json.loads((source_root / "agents_extensions/shared/settings.json").read_text(encoding="utf-8"))
    groups = []
    for group in source["hooks"]["PreToolUse"]:
        hooks = []
        for hook in group["hooks"]:
            invocation = _worker_guard_invocation(hook.get("command", ""), source_root)
            if invocation is not None:
                hooks.append({**hook, "command": invocation})
        if hooks:
            groups.append({"matcher": group["matcher"], "hooks": hooks})
    if publish_guard:
        guard = source_root / "agents_extensions/shared/hooks/guard-reviewer-publish.py"
        if not guard.is_file():
            raise RuntimeError(f"Claude reviewer publish guard unavailable: {guard}")
        groups.append(
            {"matcher": "Bash", "hooks": [{"type": "command", "command": shlex.quote(str(guard)), "timeout": 5}]}
        )
    if not groups:
        raise RuntimeError("Claude worker PreToolUse guards unavailable")
    return json.dumps({"hooks": {"PreToolUse": groups}}, separators=(",", ":"))


def _headless_worker_settings(*, publish_guard: bool) -> str:
    """Guard hooks plus the background-tool denies every headless run receives."""
    settings = json.loads(_worker_guard_settings(publish_guard=publish_guard))
    settings["permissions"] = {"deny": list(HEADLESS_BACKGROUND_TOOL_DENIES)}
    return json.dumps(settings, separators=(",", ":"))


def _isolated_review_response_schema(tool_config: dict[str, Any]) -> str:
    """Return the canonical structured-output schema for isolated reviews."""
    from scripts.review.isolation import (
        ReviewIsolationError,
        transport_isolated_review_schema,
    )

    changed_paths = tool_config.get("review_changed_paths")
    if not isinstance(changed_paths, list) or not all(isinstance(path, str) and path for path in changed_paths):
        raise ValueError("ClaudeAdapter: isolated review changed paths required")
    try:
        schema = transport_isolated_review_schema()
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
    from scripts.review.isolation import CLAUDE_MIN_SUPPORTED_CLI_VERSION

    version = _probe_claude_cli_version(cmd_prefix)
    if version is not None and version < CLAUDE_MIN_SUPPORTED_CLI_VERSION:
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
    default_model: str = "claude-sonnet-5-5"
    # Operator 2026-08-13: headless/print defaults to high when the caller
    # omits effort; interactive start-claude.sh keeps empty (last session).
    default_effort: str = "high"
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
            - ``allowed_tools: str`` — explicit comma-separated --allowedTools
              value; takes precedence over the opt-in reviewer profile.
            - ``reviewer_tools: True`` — enable the ordinary read-only reviewer
              profile only when no explicit tool list is supplied.
            - ``output_format: str`` — defaults to "stream-json" so tool
              calls can be captured from the CLI trace.
            - ``use_bare: bool`` — legacy option ignored for guarded workers;
              --bare would disable the mandatory PreToolUse hooks.
            - ``max_budget_usd: float`` — optional Claude Code print-mode
              API spend cap, emitted as ``--max-budget-usd <amount>``

        ``effort``: optional reasoning-level string. When None, the headless
        lane default ``high`` is applied (operator 2026-08-13). When the
        probed Claude binary supports ``--effort`` (CC 2.1.98+), the flag
        is appended as ``--effort <level>``. Otherwise we log a warning
        and proceed without the flag. Claude CLI versions below 2.1.116
        are rejected outright due to the 2026-04-23 postmortem gate.
        """
        tc: dict[str, Any] = tool_config or {}
        discussion_readonly = _discussion_readonly_requested(tool_config)
        review_isolation = bool(tc.get("review_isolation"))
        explicit_allowed_tools = tc.get("allowed_tools") is not None
        reviewer_guard = mode == "read-only" and not explicit_allowed_tools and tc.get("reviewer_tools") is True
        # Caller tool restrictions take precedence. Reviewer-only protections
        # are scoped to the default profile so an explicit Bash grant is not
        # silently narrowed by the publish hook or push rewrite.
        ordinary_reviewer = reviewer_guard and not discussion_readonly and not review_isolation
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
        cli_version = (
            None
            if (review_isolation or tc.get("review_attempt_boundary"))
            else _ensure_supported_claude_cli_version(probe_prefix)
        )

        cmd.append("-p")
        # NB: the actual prompt positional is appended at the END below, after a
        # `--` separator. Reason: Claude CLI uses Commander.js, which parses any
        # argv starting with `-`/`--` as a flag — even in positional position —
        # unless preceded by `--` (end-of-options marker). Channel-context
        # prompts from `ab discuss` start with `--- context: shared (sha256: ...)`
        # which Commander then treats as `unknown option '---'`. The `--`
        # separator makes the parser stop interpreting flags. (Bug surfaced
        # 2026-05-05 during the Claude+Gemini deliberation pilot.)

        has_session = session_id is not None
        # --bare skips hooks, including the primary-checkout guard. Never use
        # it for a headless worker, even when an API key is available. Sealed
        # review isolation receives the settings flag too, but its existing
        # --safe-mode suppresses hooks and shell/write tools; the isolated OS
        # sandbox does not mount the checkout's tracked hook paths.
        cmd.extend(["--settings", _headless_worker_settings(publish_guard=reviewer_guard and not review_isolation)])
        if review_isolation:
            # Exact read/search tools + empty setting sources: no write/shell
            # tools and no project CLAUDE.md/hooks/skills when flags are honored.
            cmd.append("--safe-mode")
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

        # Effort (reasoning level) — version-gated. See #1396. Omitted effort
        # defaults to the headless lane default (high, operator 2026-08-13).
        effective_effort = effort if effort is not None else self.default_effort
        if tc.get("review_attempt_boundary") and tc.get("review_access") == "full":
            cmd.extend(["--effort", effective_effort])
        elif not review_isolation:
            # ``supports_effort`` is the single patchable decision point for
            # --effort: tests patch it to simulate an unsupported CLI, and the
            # default-high lane default must ALSO omit the flag when the CLI
            # lacks it. To avoid a second ``claude --version`` subprocess —
            # which broke writer-isolation CI when tests patch runner Popen
            # and capture the probe as argv[0] instead of the real agent
            # command — seed the shared per-prefix cache from the
            # already-probed cli_version so the ``supports_effort`` call is a
            # cache hit in production. Min supported CLI is 2.1.116; --effort
            # landed at 2.1.98 (_EFFORT_MIN_VERSION).
            from utils.claude_version import remember_support, supports_effort

            if cli_version is not None:
                remember_support(probe_prefix, cli_version >= _EFFORT_MIN_VERSION)
            effort_supported = supports_effort(probe_prefix)
            if effort_supported:
                cmd.extend(["--effort", effective_effort])
            else:
                _logger.warning(
                    "Claude CLI at %s does not support --effort; ignoring effort=%r and using CLI default (#1396)",
                    probe_prefix,
                    effective_effort,
                )

        output_schema = load_output_schema(tc)
        if output_schema is not None:
            if review_isolation:
                raise ValueError("ClaudeAdapter: caller output schema conflicts with isolated review schema")
            cmd.extend(["--json-schema", json.dumps(output_schema, separators=(",", ":"))])

        # Output format
        output_format = str(tc.get("output_format", "stream-json"))
        if output_format != "stream-json":
            raise ValueError(
                "ClaudeAdapter requires tool_config output_format='stream-json' "
                "so tool-call trace parsing fails closed instead of degrading "
                "to text output"
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

        # Mode-specific flags. workspace-write must not stay on the print-mode
        # default (manual): nothing answers the prompt, so Bash, edits, web,
        # and MCP are denied. dontAsk runs the worker allow list and still
        # executes the --settings guards; --bare is what skips hooks.
        # Every read-only run denies the sources writers under any server name:
        # deny wins over the formal allow list, an explicit caller list,
        # ``mcp__<server>__*``, and any allow rule in user or checkout
        # settings, whatever name the server is registered under. An unreadable server
        # declaration raises here rather than launching without the denies.
        sources_readers, sources_writers = sources_tool_sets() if mode == "read-only" else ((), ())
        if mode == "danger":
            cmd.append("--dangerously-skip-permissions")
        elif ordinary_reviewer:
            profile = REVIEWER_PERMISSION_PROFILE
            cmd.extend(["--permission-mode", profile["mode"]])
            granted = [*profile["allow"]]
            denied = [*profile["deny"], *_sources_writer_denies(sources_writers)]
            if tc.get("mcp_config_path") and tc.get("review_access") == "full":
                from scripts.agent_runtime.review_mcp import review_tools_allowed_csv

                granted.extend(review_tools_allowed_csv("claude", "full").split(","))
            elif tc.get("mcp_config_path"):
                raise ValueError(
                    "ClaudeAdapter: an ordinary reviewer's MCP config is built by the harness; "
                    "mcp_config_path is accepted only for a formal full-access review attempt"
                )
            else:
                cmd.extend(["--strict-mcp-config", "--mcp-config", _reviewer_mcp_config()])
                granted.extend(_sources_rules(sources_readers))
            cmd.extend(["--allowedTools", ",".join(dict.fromkeys(granted))])
            cmd.extend(["--disallowedTools", ",".join(denied)])
        elif mode == "read-only" and sources_writers:
            cmd.extend(["--disallowedTools", ",".join(_sources_writer_denies(sources_writers))])
        elif mode == "workspace-write" and not review_isolation:
            cmd.extend(["--permission-mode", WORKSPACE_WRITE_PERMISSION_MODE])
            if not explicit_allowed_tools:
                cmd.extend(["--allowedTools", ",".join(_workspace_write_allows(cwd, tc))])

        # MCP tool restrictions (pipeline reviewers)
        mcp_config_path = tc.get("mcp_config_path")
        if tc.get("strict_mcp_config") and mcp_config_path and not review_isolation:
            cmd.extend(["--strict-mcp-config", "--mcp-config", str(mcp_config_path)])
        elif mcp_config_path and not review_isolation:
            cmd.extend(["--mcp-config", str(mcp_config_path)])
        if explicit_allowed_tools and not review_isolation:
            cmd.extend(["--allowedTools", str(tc["allowed_tools"])])

        # Cache-warmth optimization (CC 2.1.98+)
        if cli_version and cli_version >= _EFFORT_MIN_VERSION:
            cmd.append("--exclude-dynamic-system-prompt-sections")

        # Large sealed review dossiers and multi-lesson coherence prompts can
        # exceed execve ARG_MAX (Linux MAX_ARG_STRLEN = 128KB). Claude print
        # mode accepts text on stdin, so the isolation path and large prompts
        # never place review evidence in argv. Ordinary calls retain positional.
        use_stdin = review_isolation or len(prompt.encode("utf-8")) >= 100_000
        if not use_stdin:
            # Prompt positional MUST be last, preceded by `--` end-of-options marker.
            # See comment near `cmd.append("-p")` above for the Commander.js rationale.
            cmd.extend(["--", prompt])

        return InvocationPlan(
            cmd=cmd,
            cwd=cwd,
            stdin_payload=prompt if use_stdin else "",
            output_file=None,
            env_overrides={
                **HEADLESS_BACKGROUND_ENV,
                **({"AB_DISCUSS_READONLY": "1"} if discussion_readonly else {}),
                **({"LU_CLAUDE_READ_ONLY_GIT_PUSH_BLOCK": "1"} if reviewer_guard else {}),
            },
            liveness_paths=self._resolve_liveness_paths(cwd),
            metadata={
                **schema_metadata(output_schema),
                **({"claude_home": str(review_write_root / "home")} if review_write_root is not None else {}),
            },
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
            raw_home = plan.metadata.get("claude_home")
            claude_home = Path(raw_home) if isinstance(raw_home, str) else None
            session_path = _claude_session_jsonl_path(
                plan.cwd,
                session_id,
                home=claude_home,
            )
            if session_path is not None:
                recovered = _tool_calls_from_claude_session_jsonl(session_path)
                if len(recovered) > len(tool_calls):
                    tool_calls = recovered

        output_schema = plan_output_schema(plan)
        if output_schema is not None:
            strict_events = [json_value(line) for line in jsonl_lines(stdout) if line.strip()]
            intact = bool(strict_events) and all(isinstance(event, dict) for event in strict_events)
            terminal = strict_events[-1] if intact else {}
            return structured_result(
                terminal.get("structured_output"),
                output_schema,
                returncode=returncode,
                terminal_ok=(
                    intact
                    and "structured_output" in terminal
                    and terminal.get("type") == "result"
                    and terminal.get("subtype") == "success"
                    and terminal.get("is_error") is False
                    and sum(event.get("type") == "result" for event in strict_events) == 1
                ),
                session_id=session_id,
                tool_calls=tool_calls,
            )

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


def _claude_session_jsonl_path(
    cwd: Path,
    session_id: str,
    *,
    home: Path | None = None,
) -> Path | None:
    base = home or Path.home()
    candidate = base / ".claude" / "projects" / _claude_project_slug(cwd) / f"{session_id}.jsonl"
    return candidate if candidate.is_file() else None


def _tool_calls_from_claude_session_jsonl(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for raw_line in jsonl_lines(path.read_text(encoding="utf-8", errors="replace")):
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
    results: list[str] = []
    structured_output: dict[str, Any] | None = None
    text_parts: list[str] = []
    for event in events:
        structured = event.get("structured_output")
        if isinstance(structured, dict):
            structured_output = structured
        result = event.get("result")
        if isinstance(result, str) and result.strip():
            text = result.strip()
            if not results or results[-1] != text:
                results.append(text)
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
    if results:
        return "\n\n".join(results)
    return "\n".join(part.strip() for part in text_parts if part.strip()).strip()
