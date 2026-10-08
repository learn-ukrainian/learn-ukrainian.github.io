"""GrokBuildAdapter — wraps the native ``grok`` CLI headless.

Registry seat id is canonical ``grok`` (historical alias ``grok-build``).
DISTINCT from the Hermes-backed ``grok-hermes`` agent (``HermesGrokAdapter``,
a banned/demoted route pinned to its own legacy model, via the Hermes OAuth
API path). This adapter drives
the local ``grok`` CLI binary (``~/.local/bin/grok``) in
single-turn headless mode:

    grok -p "<prompt>" --output-format streaming-messages-json [-m MODEL] [--effort LEVEL] \
         --permission-mode <mode> --cwd <dir> --no-alt-screen

Headless text is one assistant message per model response. Messages are joined
with a newline so a later ``VERDICT:`` line stays a line (#10005). Chunks
inside one message are concatenated. ``--json-schema`` keeps
``--output-format json`` (the flag implies json). That object is
``{text, stopReason, sessionId, ...}`` and the schema path reads
``structuredOutput``, not ``text``.
The CLI uses its own stored auth under ``~/.grok`` (OAuth), so no API key is
injected — HOME (already allow-listed by env_sanitize) is sufficient.

Mode → ``--permission-mode``:
- ``read-only``       → ``auto`` + unconditional ``Bash``, ``Write`` and ``Edit``
  denies. Reviewers have no shell; only tracked checkout read tools are exposed.
  Fleet and publish PreToolUse guards plus the tracked-read hook provide a
  second layer for reads only, never a replacement for native denies (#9987).
- ``workspace-write`` → ``bypassPermissions`` + ``--always-approve``
  (unattended tool execution and file edits within the dispatch worktree)
  plus the tracked fleet PreToolUse guards through the hook bridge
- ``danger``          → the same argv as ``workspace-write`` (#9008)

Issue #7583: On native Grok 1.0.x CLI, ``acceptEdits --always-approve`` still prompts
for approval on shell commands and terminates headless turns (``stopReason=cancelled``),
while ``plan`` blocks all tool calls outright. Write dispatches map to
``bypassPermissions`` with ``--always-approve``. Ordinary ``read-only``
maps to ``auto`` so non-shell read tools can run. Opted-in reviewers retain
the Bash, Write and Edit denies and expose only tracked-file reads (#9987).

Issue #8965: Grok 1.0.41 treats an explicit ``--permission-mode auto`` as winning
over ``--always-approve``, so ``yolo_mode`` stays false and the auto classifier
refuses ``git push`` before the command runs. ``workspace-write`` therefore uses
``bypassPermissions``, the same mode ``danger`` already uses successfully.
Write sessions install the fleet PreToolUse guards (primary-checkout write,
secret-print, merge, and the rest of the tracked worker set) through the same
hook bridge. They do not load the reviewer publish guard or the read-only Git
push rewrite. Read-only reviewers have no shell and use the hook as a second
layer for tracked reads only (#9987).

Issue #9008: ``danger`` keeps that argv. Claude loads the same fleet guards
on both write modes; ``workspace-write`` is ``dontAsk`` plus an allow list and
``danger`` is ``--dangerously-skip-permissions``. Grok 1.0.41 has no
skip-permissions flag. ``bypassPermissions`` is its always-approve mode, and
hooks still run there. ``dontAsk`` allows only pre-approved tools, and
``auto`` leaves ``yolo_mode`` false, so a headless worker cannot push.
The operator-accepted bypass therefore stays the write mode for both, and
``danger`` keeps ``lu-write-worker`` so the fleet guards stay on. The shared
argv is pinned by ``test_danger_argv_matches_workspace_write``.

Trail and review isolation use their own explicit tool/deny policies; they do
not inherit the ordinary write-dispatch approval grant.

``resume_policy`` is ``never`` in the registry: the CLI's ``--resume`` +
cross-session memory risk worktree contamination — the same footgun as Codex.
The grok CLI is Claude-Code-shaped, so this mirrors ``claude.py`` closely.
"""

from __future__ import annotations

import json
import logging
import os
import re
import shlex
import shutil
import tempfile
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from urllib.parse import quote
from uuid import UUID

from scripts.secret_redactor import redact_text

from ..failure_codes import provider_failure_code, provider_stderr_error
from ..grok_reviewer_permissions import GROK_REVIEWER_TOOLS
from ..jsonl import jsonl_lines
from ..result import ParseResult
from ..trail_isolation import (
    GROK_TRAIL_DENY_TOOLS,
    GROK_TRAIL_TOOLS,
    TrailIsolationError,
    assert_trail_isolation_config,
    trail_isolation_requested,
)
from ._output_schema import json_value, load_output_schema, plan_output_schema, schema_metadata, structured_result
from .base import InvocationPlan

_logger = logging.getLogger(__name__)

# Diagnostics may include provider prose or partial assistant text. Mask path
# shapes after secret redaction and before bounding, including relative paths.
_DIAGNOSTIC_PATH = re.compile(
    r"(?:[A-Za-z]:[\\/]|\\\\|~[\w.-]*[\\/]|\.{1,2}[\\/]|/|[\w.-]+[\\/])"
    r"[^\s'\"`,;<>|)\]}]*"
)


def _stop_diagnostic(envelope: dict | None, stderr: str) -> str:
    """Keep the terminal reason/detail ahead of partial text in a safe excerpt."""

    def safe(value: str) -> str:
        cleaned = _DIAGNOSTIC_PATH.sub("<path>", redact_text(value) or "")
        return " ".join("".join(ch if ch.isprintable() else " " for ch in cleaned).split())

    if envelope is None or "stopReason" not in envelope:
        reason = "missing stopReason"
    else:
        reason = "stopReason=" + safe(json.dumps(envelope["stopReason"], ensure_ascii=False))[:160]
    parts = [f"grok final answer incomplete: {reason}"]
    if envelope is not None:
        # Only terminal envelope fields, never nested tool output. Different
        # CLI releases may expose cancellation/stop detail in these fields.
        detail = {
            key: envelope[key]
            for key in (
                "stopReasonDetail",
                "stopDetail",
                "stopDetails",
                "cancellation_category",
                "cancellationCategory",
                "message",
                "error",
                "structuredOutputError",
            )
            if key in envelope
        }
        if detail:
            parts.append("stop detail: " + safe(json.dumps(detail, ensure_ascii=False))[:220])
    if stderr.strip():
        parts.append(safe(stderr.strip()))
    if envelope is not None and envelope.get("text"):
        parts.append(safe(str(envelope["text"]).strip()))
    # delegate persists the first diagnostic line in .diag. Keep the stop
    # detail on that line too, ahead of stderr and partial answer text.
    return " ".join(parts)[:500]


# Runtime mode → grok CLI --permission-mode value.
# Issue #7583: on grok 1.0.x, acceptEdits does not cover shell headlessly (turn
# cancels), while plan blocks all tool calls. Read-only stays on auto with
# Bash/write denies by default.
# Issue #8965: explicit --permission-mode auto defeats --always-approve
# (yolo_mode stays false) and the auto classifier blocks git push. Write modes
# use bypassPermissions so always-approve stays on.
_MODE_PERMISSION: dict[str, str] = {
    "read-only": "auto",
    "workspace-write": "bypassPermissions",
    "danger": "bypassPermissions",
}

# Non-isolated write-capable dispatches grant --always-approve so tool executions
# run without a human approval prompt.
_UNATTENDED_WRITE_MODES: frozenset[str] = frozenset({"workspace-write", "danger"})

# #9987: native dontAsk cancels allowed Git calls; bypass fails open if a hook
# fails. Retain auto plus the unconditional Bash deny until the driver resolves
# that incompatibility. The hook is defense in depth, never the shell backstop.
_REVIEWER_PERMISSION_MODE = "auto"
_REVIEWER_ALLOW_RULES = ("Read", "Grep")

# Default deny rules for ordinary read-only (issue #7583 / PR #7594 CF): grok
# --permission-mode auto may approve unnamed commands, and prefix Bash denies
# are not fail-closed (gh api, git -C … push, tee, sed -i, …). Deny Bash and
# write tools wholesale, including for callers opting into reviewer hooks.
# Native Grok's documented permission-rule prefixes are Bash, Edit, Write, Read,
# Grep, WebFetch, and MCPTool. These are permission prefixes, not built-in tool
# IDs: ``search_replace`` belongs to ``--disallowed-tools``, not ``--deny``.
_GROK_PERMISSION_RULE_PREFIXES: frozenset[str] = frozenset(
    {"Bash", "Edit", "Grep", "MCPTool", "Read", "WebFetch", "Write"}
)
_READ_ONLY_DENY_RULES: tuple[str, ...] = (
    "Write",
    "Edit",
    "Bash",
)

# MCP servers that are safe to run under an execution-capable permission mode
# (read-only data lookups, no mutations). ONLY these may trigger the plan→exec
# override below; any other / future write-capable server falls back to the
# normal (safer) mode mapping rather than silently gaining execution rights.
_READ_ONLY_MCP_SERVERS: frozenset[str] = frozenset({"sources"})

# Defense-in-depth for MCP reviews: even though `bypassPermissions` auto-approves
# tool calls so the MCP read tools execute, explicit `--deny` rules still win
# (per grok's permission model: deny > bypass). Denying file-write + shell tools
# means a prompt-injected review article cannot make grok mutate the filesystem
# or run shell — it can only call the read-only MCP tools the review needs.
_MCP_REVIEW_DENY_RULES: tuple[str, ...] = (
    "Write",
    "Edit",
    "Bash",
)
# Current CLI default only. grok-4.7-build-fast is about 2x the price and is
# not admitted. grok-4.6 is the previous id and is not admitted.
GROK_ALLOWED_MODELS: frozenset[str] = frozenset({"grok-4.7"})
GROK_SUPPORTED_EFFORTS: frozenset[str] = frozenset({"low", "medium", "high"})
GROK_BUILD_DEFAULT_MODEL = "grok-4.7"
GROK_BUILD_DEFAULT_EFFORT = os.environ.get("LEARN_UK_GROK_BUILD_EFFORT", "high")
_TRAIL_ISOLATION_TOOL_CONFIG_KEYS: frozenset[str] = frozenset(
    {
        "allowed_tools",
        "mcp_config_path",
        "setting_sources",
        "strict_mcp_config",
        "tools",
        "trail_isolation",
        "trail_isolation_cwd",
    }
)

# plan.metadata keys for liveness bind (#6935). Snapshot is the set of
# cwd-scoped session *directory names* that already existed at
# build_invocation; once a post-snapshot child is discovered, its id is
# pinned so later same-cwd peers cannot steal the bind and a plan-only
# poller can reproduce it without adapter instance state.
_META_RESUME_SESSION_ID = "resume_session_id"
_META_LIVENESS_SESSION_ID = "liveness_session_id"
_META_LIVENESS_SNAPSHOT = "liveness_session_dir_snapshot"
_META_REVIEWER_AGENT_FILE = "reviewer_agent_file"
_META_WRITE_GUARD_AGENT_FILE = "write_guard_agent_file"

# Claude matchers auto-expand to some Grok ids. These are the model-facing
# ids that expansion does not cover, so a write session's guards still see
# the shell and file tools the model actually calls.
_WRITE_MATCHER_ALIASES: dict[str, tuple[str, ...]] = {
    "Bash": ("run_terminal_command", "run_terminal_cmd"),
    "Write|Edit|MultiEdit": ("write", "search_replace", "hashline_edit"),
}


def _grok_matcher(matcher: str, *, native_aliases: bool) -> str:
    extras = _WRITE_MATCHER_ALIASES.get(matcher) if native_aliases else None
    if not extras:
        return matcher
    return "|".join((matcher, *extras))


def _guard_agent_definition(
    *,
    name: str,
    description: str,
    body: str,
    publish_guard: bool,
    native_aliases: bool,
) -> str:
    """Build a per-invocation Grok agent whose hooks call the fleet guards.

    Grok has no ``--settings`` flag. Its ``--agent`` definition supports
    PreToolUse hooks for the primary session, as verified against the native
    CLI. The wrapper translates Grok's camelCase event into the Claude-shaped
    payload consumed by the existing guards. ``promptMode`` stays at its
    default (extend), so the body is appended to the base system prompt.
    """
    from .claude import _worker_guard_settings

    source_root = Path(__file__).resolve().parents[3]
    wrapper = source_root / "scripts/agent_runtime/grok_hook_bridge.py"
    if not wrapper.is_file():
        raise RuntimeError(f"Grok hook bridge unavailable: {wrapper}")
    groups = json.loads(_worker_guard_settings(publish_guard=publish_guard))["hooks"]["PreToolUse"]
    lines = [
        "---",
        f"name: {name}",
        f"description: {description}",
        "hooks:",
        "  PreToolUse:",
    ]
    for group in groups:
        matcher = _grok_matcher(str(group["matcher"]), native_aliases=native_aliases)
        lines.extend([f"    - matcher: {json.dumps(matcher)}", "      hooks:"])
        for hook in group["hooks"]:
            command = f"{shlex.quote(str(wrapper))} {shlex.quote(hook['command'])}"
            lines.extend(
                [
                    "        - type: command",
                    f"          command: {json.dumps(command)}",
                    f"          timeout: {max(15, int(hook.get('timeout', 5)))}",
                ]
            )
    lines.extend(["---", body, ""])
    return "\n".join(lines)


def _reviewer_agent_definition(cwd: Path) -> str:
    """Read-only reviewer agent: fleet guards plus the publish guard."""
    from scripts.common.repo_root import project_interpreter

    source_root = Path(__file__).resolve().parents[3]
    guard = source_root / "scripts/agent_runtime/grok_reviewer_permissions.py"
    if not guard.is_file():
        raise RuntimeError("Grok reviewer permission guard unavailable")
    definition = _guard_agent_definition(
        name="lu-read-only-reviewer",
        description="Read-only reviewer with fleet PreToolUse guards",
        body=(
            "Review the requested work using tracked-file reads only. "
            "Approval-requiring tools are denied without prompting. Continue with permitted "
            "read tools on tracked files inside this checkout (grep requires a file path); "
            "do not retry a denied action through a wrapper. "
            "Shell execution is unavailable: auto mode retains the native Bash, Write and "
            "Edit denies. The hook is a second layer for reads only (#9987). "
            "Report any execution evidence you could not obtain."
        ),
        publish_guard=True,
        native_aliases=False,
    )
    guard_command = shlex.join([str(project_interpreter(source_root)), str(guard), "--review-root", str(cwd)])
    # This guard consumes native Grok events directly, before native approval.
    hook = (
        '    - matcher: ".*"\n'
        "      hooks:\n"
        "        - type: command\n"
        f"          command: {json.dumps(guard_command)}\n"
        "          timeout: 15\n"
    )
    return definition.replace("\n---\n", "\n" + hook + "---\n", 1)


def _write_guard_agent_definition() -> str:
    """Write-worker agent: fleet guards, no publish guard, no push rewrite."""
    return _guard_agent_definition(
        name="lu-write-worker",
        description="Write worker with fleet PreToolUse guards",
        body="",
        publish_guard=False,
        native_aliases=True,
    )


def validate_grok_effort(effort: str | None) -> str | None:
    """Return a native Grok effort after enforcing its CLI vocabulary.

    ``delegate.py`` calls this before it creates a worker. Keeping the same
    check here protects direct runtime callers and prevents a malformed
    environment default from reaching the native CLI.
    """
    if effort is None:
        return None
    if effort not in GROK_SUPPORTED_EFFORTS:
        raise ValueError(f"native Grok CLI supports --effort values {sorted(GROK_SUPPORTED_EFFORTS)}; got {effort!r}")
    return effort


def resolve_grok_home(*, env: dict[str, str] | None = None) -> Path:
    """Return the active Grok home (``GROK_HOME`` or ``~/.grok``)."""
    if env is not None and env.get("GROK_HOME"):
        return Path(env["GROK_HOME"])
    configured = os.environ.get("GROK_HOME")
    if configured:
        return Path(configured)
    return Path.home() / ".grok"


def grok_cwd_sessions_dir(grok_home: Path, cwd: Path) -> Path:
    """Return the cwd-keyed sessions parent under ``grok_home``.

    Native Grok stores one directory per session beneath
    ``sessions/<urlquoted-resolved-cwd>/``. Peer sessions that share a cwd
    still get distinct child directories; the shared ``GROK_HOME`` root must
    never be treated as a liveness signal (#6933).
    """
    return grok_home / "sessions" / quote(str(cwd.resolve()), safe="")


def grok_session_dir(grok_home: Path, cwd: Path, session_id: str) -> Path:
    """Return Grok's session directory for ``cwd`` and ``session_id``.

    Native Grok keys sessions by the symlink-resolved working directory.  This
    matters on macOS, where ``/tmp`` normally resolves below ``/private``.
    Keep this in the adapter so bridge callers and trace validators use the
    identical, documented lookup rule.
    """
    return grok_cwd_sessions_dir(grok_home, cwd) / session_id


def _permission_cancellation(
    envelope: dict | None, plan: InvocationPlan | None, call_start_time: float | None
) -> bool:
    """Classify only typed cancellation evidence for this exact native turn."""
    if envelope is None or envelope.get("stopReason") != "cancelled":
        return False
    for key in ("cancellation_category", "cancellationCategory"):
        if envelope.get(key) in ("permission_cancelled", "PermissionCancelled"):
            return True
    # Native JSON may omit the category. Never scan peers or infer it from
    # assistant/tool text; bind the last terminal event to the returned UUID.
    sid = envelope.get("sessionId") or envelope.get("session_id")
    if plan is None or not isinstance(sid, str):
        return False
    try:
        if str(UUID(sid)) != sid:
            return False
        if sid in plan.metadata.get(_META_LIVENESS_SNAPSHOT, ()):
            return False
        events = grok_session_dir(resolve_grok_home(env=plan.env_overrides), plan.cwd, sid) / "events.jsonl"
        terminal = None
        with events.open(encoding="utf-8") as stream:
            for line in stream:
                if not line.strip():
                    continue
                event = json.loads(line)
                if not isinstance(event, dict):
                    return False
                if event.get("type") == "turn_ended":
                    terminal = event
        if terminal is None:
            return False
        if call_start_time is not None:
            stamp = datetime.fromisoformat(terminal["ts"].replace("Z", "+00:00"))
            if stamp.tzinfo is None or stamp.timestamp() < call_start_time:
                return False
        return terminal.get("outcome") == "cancelled" and terminal.get("cancellation_category") == "permission_cancelled"
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, RecursionError):
        return False


class GrokBuildAdapter:
    """Adapter for the native ``grok`` CLI in single-turn headless mode."""

    name: str = "grok"
    default_model: str = GROK_BUILD_DEFAULT_MODEL
    default_effort: str = GROK_BUILD_DEFAULT_EFFORT
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
        if mode not in self.supported_modes:
            raise ValueError(f"GrokBuildAdapter: unsupported mode {mode!r} (supported: {sorted(self.supported_modes)})")
        tc = tool_config or {}
        trail_isolation = trail_isolation_requested(tc)
        trail_cwd: Path | None = None
        if trail_isolation:
            if mode != "read-only":
                raise TrailIsolationError("Grok trail isolation requires mode='read-only'")
            unsupported = sorted(set(tc) - _TRAIL_ISOLATION_TOOL_CONFIG_KEYS)
            if unsupported:
                raise TrailIsolationError(f"Grok trail isolation refuses incompatible tool_config keys: {unsupported}")
            trail_cwd = assert_trail_isolation_config(tc, profile="grok")
        review_isolation = bool(tc.get("review_isolation"))
        reviewer_tools = (
            mode == "read-only"
            and tc.get("reviewer_tools") is True
            and not trail_isolation
            and not review_isolation
            and not tc.get("strict_mcp_config")
            and not tc.get("mcp_server_names")
            and "allowed_tools" not in tc
        )
        review_write_root: Path | None = None
        if review_isolation:
            from scripts.review.isolation import validated_review_write_root

            review_write_root = validated_review_write_root(tc)
            trusted = tc.get("review_engine_binary")
            if not isinstance(trusted, str) or not Path(trusted).is_absolute():
                raise ValueError("GrokBuildAdapter: trusted review_engine_binary required")
            grok_bin = trusted
        else:
            grok_bin = shutil.which("grok")
        if not grok_bin:
            raise RuntimeError(
                "grok CLI not found on PATH. Install the xAI grok CLI "
                "(provides `grok`) to dispatch the native `grok` seat "
                "(historical alias: `grok-build`)."
            )
        requested_model = model or self.default_model
        if requested_model not in GROK_ALLOWED_MODELS:
            raise ValueError(
                f"GrokBuildAdapter: unsupported Grok model {requested_model!r}; allowed: {sorted(GROK_ALLOWED_MODELS)}"
            )
        if "sources" in (tc.get("mcp_server_names") or []):
            prompt = _adapt_prompt_for_grok_build_mcp(prompt)

        cmd: list[str] = [grok_bin]
        mcp_servers_requested = set(tc.get("mcp_server_names") or [])
        mcp_read_only = bool(mcp_servers_requested) and mcp_servers_requested <= _READ_ONLY_MCP_SERVERS
        guard_agent_file: str | None = None
        guard_agent_key: str | None = None
        guard_agent_suffix: str | None = None
        guard_definition: str | None = None
        if reviewer_tools:
            guard_definition = _reviewer_agent_definition(cwd)
            guard_agent_suffix = ".grok-reviewer-agent.md"
            guard_agent_key = _META_REVIEWER_AGENT_FILE
        elif mode in _UNATTENDED_WRITE_MODES and not trail_isolation and not review_isolation and not mcp_read_only:
            # Same tracked PreToolUse set Claude workers load, without the
            # reviewer publish guard. The push rewrite is env-only and stays
            # off this path.
            guard_definition = _write_guard_agent_definition()
            guard_agent_suffix = ".grok-write-agent.md"
            guard_agent_key = _META_WRITE_GUARD_AGENT_FILE
        if guard_definition is not None and guard_agent_suffix is not None:
            with tempfile.NamedTemporaryFile("w", suffix=guard_agent_suffix, delete=False, encoding="utf-8") as handle:
                handle.write(guard_definition)
                guard_agent_file = handle.name
            cmd.extend(["--agent", guard_agent_file])
        execution_cwd = trail_cwd or cwd
        # Prompt: inline via -p for the common case; a hyphen-leading prompt
        # would be misparsed by clap as a flag, so route those through a temp
        # --prompt-file instead (robust for any content).
        if review_isolation and review_write_root is not None:
            write_root = review_write_root
            out_dir = write_root / "tmp"
            execution_cwd = write_root / "exec"
            prompt_file = out_dir / "grok-prompt.txt"
            fd = os.open(
                prompt_file,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
                0o600,
            )
            with os.fdopen(fd, "wb") as handle:
                handle.write(prompt.encode("utf-8"))
            prompt_path = str(prompt_file)
            cmd.extend(["--prompt-file", prompt_path])
        elif prompt.startswith("-"):
            if review_isolation:
                raise ValueError("GrokBuildAdapter: isolated review prompt file requires review_write_root")
            else:
                with tempfile.NamedTemporaryFile(
                    "w", suffix=".grok-prompt.txt", delete=False, encoding="utf-8"
                ) as handle:
                    handle.write(prompt)
                    prompt_path = handle.name
            cmd.extend(["--prompt-file", prompt_path])
        else:
            cmd.extend(["-p", prompt])

        output_schema = load_output_schema(tc)
        # #10005: --output-format json concatenates assistant messages with no
        # separator, so a later VERDICT line is glued onto the previous sentence.
        # streaming-messages-json emits one assistant frame per model response.
        # --json-schema implies json and the verdict is structuredOutput.
        output_format = "json" if output_schema is not None else "streaming-messages-json"
        cmd.extend(["--output-format", output_format, "--no-alt-screen"])
        if output_schema is not None:
            cmd.extend(["--json-schema", json.dumps(output_schema, separators=(",", ":"))])
        # Issue #7583 / #7594: ordinary read-only maps to grok `auto` so non-shell
        # read tools can run. Reviewers deny Bash unconditionally and expose only
        # tracked-file read tools through a closed tool set and all-tool guard.
        # Prefix-only Bash denies are not a closed allowlist under `auto`.
        # MCP-grounded reviews execute tool calls (e.g. sources__verify_words)
        # under bypassPermissions with MCP deny rules.
        # Review isolation (#5285): expose only built-in read tools. The
        # parent-owned OS sandbox limits them to the sealed view; explicit deny
        # rules remove shell/write/nested execution even though headless tool
        # calls require an execution-capable permission mode.
        if trail_isolation:
            permission_mode = "default"
        elif review_isolation:
            permission_mode = str(tc.get("permission_mode") or "bypassPermissions")
        elif reviewer_tools:
            permission_mode = _REVIEWER_PERMISSION_MODE
        else:
            permission_mode = "bypassPermissions" if mcp_read_only else _MODE_PERMISSION[mode]
        cmd.extend(["--permission-mode", permission_mode])
        cmd.extend(["--cwd", str(execution_cwd)])
        if reviewer_tools:
            cmd.extend(["--no-subagents", "--disable-web-search"])
            for rule in _REVIEWER_ALLOW_RULES:
                cmd.extend(["--allow", rule])
            for rule in ("MCPTool", "WebFetch", "WebSearch"):
                cmd.extend(["--deny", rule])
        if (mcp_read_only or mode in _UNATTENDED_WRITE_MODES) and not review_isolation and not trail_isolation:
            cmd.append("--always-approve")
        if mcp_read_only and not review_isolation:
            cmd.append("--no-plan")
            cmd.append("--disable-web-search")
            for rule in _MCP_REVIEW_DENY_RULES:
                cmd.extend(["--deny", rule])
        elif mode == "read-only" and not trail_isolation and not review_isolation:
            for rule in _READ_ONLY_DENY_RULES:
                cmd.extend(["--deny", rule])
        if trail_isolation:
            cmd.extend(
                [
                    "--no-plan",
                    "--no-memory",
                    "--no-subagents",
                    "--disable-web-search",
                    "--verbatim",
                ]
            )
            for rule in GROK_TRAIL_DENY_TOOLS:
                cmd.extend(["--deny", rule])
            for rule in GROK_TRAIL_TOOLS:
                cmd.extend(["--allow", rule])
        elif review_isolation:
            cmd.extend(
                [
                    "--always-approve",
                    "--no-plan",
                    "--no-memory",
                    "--no-subagents",
                    "--disable-web-search",
                    "--verbatim",
                ]
            )
            configured_deny_rules = tc.get("review_deny_tools")
            if configured_deny_rules is None:
                deny_rules = _MCP_REVIEW_DENY_RULES
            elif not isinstance(configured_deny_rules, (list, tuple)):
                raise ValueError("GrokBuildAdapter: review_deny_tools must be a list or tuple")
            else:
                deny_rules = tuple(configured_deny_rules)
                invalid_rules = [
                    rule
                    for rule in deny_rules
                    if not isinstance(rule, str) or rule not in _GROK_PERMISSION_RULE_PREFIXES
                ]
                if invalid_rules:
                    raise ValueError(
                        "GrokBuildAdapter: review_deny_tools contains unsupported Grok permission prefixes: "
                        f"{invalid_rules!r}"
                    )
                missing_rules = set(_MCP_REVIEW_DENY_RULES) - set(deny_rules)
                if missing_rules:
                    raise ValueError(
                        f"GrokBuildAdapter: review_deny_tools must retain fail-closed rules: {sorted(missing_rules)!r}"
                    )
            for rule in deny_rules:
                cmd.extend(["--deny", rule])

        effective_effort = validate_grok_effort(effort or self.default_effort)
        cmd.extend(["-m", requested_model])
        if effective_effort:
            # The native Grok CLI accepts only low|medium|high.
            cmd.extend(["--effort", effective_effort])

        disallowed = tc.get("disallowed_tools")
        if mode == "read-only" and not trail_isolation:
            # search_replace is Grok's native editor tool ID, not a valid
            # --deny prefix. Remove it explicitly in every read-only path.
            if disallowed:
                disallowed_values = [value.strip() for value in str(disallowed).split(",") if value.strip()]
                if "search_replace" not in disallowed_values:
                    disallowed_values.append("search_replace")
                disallowed = ",".join(disallowed_values)
            else:
                disallowed = "search_replace"
        if disallowed:
            cmd.extend(["--disallowed-tools", str(disallowed)])
        allowed = tc.get("allowed_tools")
        if reviewer_tools:
            allowed = ",".join(GROK_REVIEWER_TOOLS)
        if allowed:
            cmd.extend(["--tools", str(allowed)])

        # Resume only if the caller explicitly opts in (delegate dispatch never
        # should — resume_policy=never — to avoid cross-worktree contamination).
        resume_session_id = session_id if session_id and tc.get("resume") else None
        if resume_session_id:
            cmd.extend(["--resume", resume_session_id])

        _logger.debug(
            "grok invocation: task=%s mode=%s permission=%s model=%s effort=%s",
            task_id,
            mode,
            permission_mode,
            requested_model,
            effective_effort,
        )

        snapshot = self._reset_per_invocation_state(
            cwd=execution_cwd,
            env_overrides={},
        )
        metadata: dict[str, object] = {
            **schema_metadata(output_schema),
            "entire_fleet": {
                "requested_model": requested_model,
                "actual_model": requested_model,
            },
            _META_RESUME_SESSION_ID: resume_session_id,
            # Plan-owned snapshot so a plan-only / split-instance poller can
            # exclude pre-existing same-cwd peers without adapter instance
            # state (#6935).
            _META_LIVENESS_SNAPSHOT: sorted(path.name for path in snapshot),
        }
        if guard_agent_file is not None and guard_agent_key is not None:
            metadata[guard_agent_key] = guard_agent_file
        liveness_paths, _discovered = self._liveness_paths_for_cwd(
            execution_cwd,
            bound_session_id=resume_session_id,
            snapshot=snapshot,
            env_overrides={},
        )

        return InvocationPlan(
            cmd=cmd,
            cwd=execution_cwd,
            stdin_payload="",
            output_file=None,
            env_overrides={"LU_CLAUDE_READ_ONLY_GIT_PUSH_BLOCK": "1"} if reviewer_tools else {},
            liveness_paths=liveness_paths,
            metadata=metadata,
            host_harness="grok",
        )

    def cleanup_invocation(self, plan: InvocationPlan) -> None:
        """Remove only the guard agent definition created for this plan."""
        for key, suffix in (
            (_META_REVIEWER_AGENT_FILE, ".grok-reviewer-agent.md"),
            (_META_WRITE_GUARD_AGENT_FILE, ".grok-write-agent.md"),
        ):
            path = plan.metadata.get(key)
            if isinstance(path, str) and path.endswith(suffix):
                Path(path).unlink(missing_ok=True)

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
        _ = output_file  # grok -p flushes to stdout

        # Assemble NDJSON before the single-object parser. That parser spans
        # the first brace to the last and would corrupt a multi-event stream.
        obj = _grok_stream_envelope(stdout)
        if obj is None:
            obj = _parse_json_object(stdout)
        terminal_ok = obj is not None and obj.get("stopReason") == "end_turn"
        permission_cancelled = _permission_cancellation(obj, plan, call_start_time)
        if permission_cancelled:
            obj = {**obj, "cancellation_category": "permission_cancelled"}
        usage = obj.get("modelUsage") if obj else None
        runtime_model = next(iter(usage)) if isinstance(usage, dict) and len(usage) == 1 else None
        if not isinstance(runtime_model, str) or not runtime_model.strip():
            runtime_model = None
        requested_model = self.default_model
        if plan is not None and "-m" in plan.cmd:
            requested_model = plan.cmd[plan.cmd.index("-m") + 1]
        from scripts.review.model_catalog import runtime_model_matches_requested

        attribution = {
            "requested_provider": "grok",
            "requested_model": requested_model,
            "actual_provider": "grok",
            "actual_model": runtime_model,
            "actual_model_known": runtime_model is not None,
            "substituted": bool(runtime_model and not runtime_model_matches_requested(requested_model, runtime_model)),
            "source": "grok-model-usage" if runtime_model else "unattested-harness",
            "marker": None,
        }
        sid = (obj.get("sessionId") or obj.get("session_id")) if obj else None
        provider_error = provider_stderr_error(stderr or "")
        provider_failed = obj is not None and obj.get("type") == "error"
        if provider_failed:
            error = obj.get("error")
            # Native Grok documents type=error with a top-level message;
            # retain the older error field without reading reply/text fields.
            if not isinstance(error, str):
                error = obj.get("message")
            provider_error = error if isinstance(error, str) else ""
        if provider_failed or (returncode != 0 and provider_error):
            failure_code = provider_failure_code(provider_error)
            return ParseResult(
                ok=False,
                response="",
                stderr_excerpt=(
                    _stop_diagnostic(obj, stderr) if not terminal_ok else provider_error[:500] or "grok provider error"
                ),
                rate_limited=failure_code == "rate_limited",
                failure_code=failure_code,
                provider_error_text=provider_error,
                session_id=sid if isinstance(sid, str) and sid else None,
                substitution=attribution,
            )

        output_schema = plan_output_schema(plan)
        if output_schema is not None:
            envelope = json_value(stdout)
            envelope = envelope if isinstance(envelope, dict) else {}
            if permission_cancelled:
                envelope = {**envelope, "cancellation_category": "permission_cancelled"}
            parsed = structured_result(
                envelope.get("structuredOutput"),
                output_schema,
                returncode=returncode,
                terminal_ok=(
                    "structuredOutput" in envelope
                    and envelope.get("stopReason") == "end_turn"
                    and "structuredOutputError" not in envelope
                    and envelope.get("type") != "error"
                ),
                session_id=envelope.get("sessionId"),
            )
            return replace(
                parsed,
                failure_code="permission_cancelled" if permission_cancelled else parsed.failure_code,
                provider_error_text=provider_error,
                substitution=attribution,
                stderr_excerpt=(
                    _stop_diagnostic(envelope, stderr)
                    if envelope.get("stopReason") != "end_turn"
                    else parsed.stderr_excerpt
                ),
            )

        if obj is not None:
            text = str(obj.get("text") or "").strip()
            sid = obj.get("sessionId") or obj.get("session_id")
            session_id = sid if isinstance(sid, str) and sid else None
        else:
            # Keep unframed text for diagnostics; it cannot prove completion.
            text = (stdout or "").strip()
            session_id = None

        # Native Grok can exit 0 after a cancelled permission request and
        # leave only opening narration (#9771). Text alone is not a final
        # answer: require the CLI's exact terminal marker, as the structured
        # path already does. Do not infer completion from the reply body.
        usable = bool(text)
        failed = returncode != 0 or not usable or not terminal_ok
        failure_code = (
            "permission_cancelled"
            if permission_cancelled
            else "provider_stream_incomplete"
            if not terminal_ok
            else provider_failure_code(provider_error)
            if failed
            else None
        )
        rate_limited = failed and failure_code == "rate_limited"
        ok = returncode == 0 and usable and not failed

        stderr_excerpt: str | None = None
        if not ok:
            source = (stderr or "").strip() or (stdout or "").strip() or ""
            stderr_excerpt = source[:500] or None
            if not terminal_ok and (obj is not None or returncode == 0 or text):
                # Preserve partial text only in bounded diagnostics, never in
                # response (which becomes the driver's result file).
                stderr_excerpt = _stop_diagnostic(obj, stderr or (stdout if obj is None else ""))

        return ParseResult(
            ok=ok,
            response=text if ok else "",
            stderr_excerpt=stderr_excerpt,
            rate_limited=rate_limited,
            failure_code=failure_code,
            provider_error_text=provider_error,
            session_id=session_id,
            tokens=None,  # grok JSON does not report token counts
            tool_calls=[],
            substitution=attribution,
        )

    def liveness_signal_paths(self, plan: InvocationPlan) -> tuple[Path, ...]:
        """Return session-scoped paths for the watchdog mtime poller.

        Issue #6933: the shared ``GROK_HOME`` / ``~/.grok`` directory mtime is
        cross-session contaminated — any concurrent Grok process can bump it
        and keep a wedged supervised session looking alive. Watch only the
        cwd-keyed sessions parent plus this invocation's own session dir /
        ``events.jsonl`` (resume id, or a session dir created after the
        build-time snapshot).

        Issue #6935: once a post-snapshot session is discovered, pin its id
        onto ``plan.metadata`` so later same-cwd peers cannot steal the bind
        and a plan-only poller (fresh adapter instance) can reproduce it.
        The build-time child-name snapshot is also stored on the plan for the
        same reason.

        Startup window (accepted tradeoff vs #6933): if ``sessions_root``
        already exists, its mtime is stale until **this** child is created.
        Until then the only path is that parent — a hang before mkdir (auth,
        first download) looks dead to the stall timer, which is the intended
        direction. The mtime poller already baselines missing paths at ``0.0``,
        so a not-yet-created ``sessions_root`` is tolerated; Grok usually
        creates the session dir in seconds while stall timeouts are minutes.
        """
        metadata = plan.metadata if isinstance(plan.metadata, dict) else {}
        bound = self._bound_liveness_session_id(metadata)
        snapshot = self._snapshot_paths_for_plan(plan)
        paths, discovered_id = self._liveness_paths_for_cwd(
            plan.cwd,
            bound_session_id=bound,
            snapshot=snapshot,
            env_overrides=plan.env_overrides or {},
        )
        if discovered_id and not bound:
            # Mutate the plan-owned dict (InvocationPlan is frozen, metadata
            # contents are not) so subsequent polls keep this bind. Never pin
            # onto adapter instance state — a shared adapter serving two plans
            # would otherwise hand plan B the session id pinned for plan A.
            metadata[_META_LIVENESS_SESSION_ID] = discovered_id
        return paths

    def _bound_liveness_session_id(self, metadata: dict[str, object]) -> str | None:
        """Return resume or pinned liveness session id from plan metadata only.

        Instance-level bind is intentionally absent: a shared adapter can
        poll multiple plans, and an instance pin contaminates unpinned peers
        (#6935 FAIL delta).
        """
        for key in (_META_RESUME_SESSION_ID, _META_LIVENESS_SESSION_ID):
            raw = metadata.get(key)
            if isinstance(raw, str) and raw:
                return raw
        return None

    def _snapshot_paths_for_plan(self, plan: InvocationPlan) -> set[Path]:
        """Resolve the build-time session-dir snapshot for this plan.

        Prefer ``plan.metadata`` so a fresh adapter instance can still exclude
        pre-existing same-cwd peers; fall back to instance state for callers
        that have not yet stamped the plan.
        """
        metadata = plan.metadata if isinstance(plan.metadata, dict) else {}
        raw = metadata.get(_META_LIVENESS_SNAPSHOT)
        if isinstance(raw, (list, tuple)):
            grok_home = resolve_grok_home(env=plan.env_overrides or {})
            sessions_root = grok_cwd_sessions_dir(grok_home, plan.cwd)
            names = [name for name in raw if isinstance(name, str) and name]
            return {sessions_root / name for name in names}
        return set(getattr(self, "_session_dir_snapshot", set()) or set())

    def _reset_per_invocation_state(
        self,
        *,
        cwd: Path,
        env_overrides: dict[str, str],
    ) -> set[Path]:
        """Snapshot pre-existing cwd-scoped session dirs before launch."""
        self._session_dir_snapshot = self._snapshot_preexisting_session_dirs(cwd, env_overrides=env_overrides)
        return self._session_dir_snapshot

    def _snapshot_preexisting_session_dirs(
        self,
        cwd: Path,
        *,
        env_overrides: dict[str, str],
    ) -> set[Path]:
        sessions_root = grok_cwd_sessions_dir(resolve_grok_home(env=env_overrides), cwd)
        try:
            if not sessions_root.is_dir():
                return set()
            return {path for path in sessions_root.iterdir() if path.is_dir()}
        except OSError:
            return set()

    def _liveness_paths_for_cwd(
        self,
        cwd: Path,
        *,
        bound_session_id: str | None = None,
        snapshot: set[Path] | None = None,
        env_overrides: dict[str, str] | None = None,
    ) -> tuple[tuple[Path, ...], str | None]:
        """Return ``(liveness_paths, newly_discovered_session_id_or_None)``.

        When ``bound_session_id`` is set (resume or a prior #6935 pin), watch
        only that session dir + ``events.jsonl``. Otherwise watch
        ``sessions_root`` as a startup signal and, once a post-snapshot child
        appears, bind the newest one — the caller must pin that id onto
        ``plan.metadata`` so a later same-cwd sibling cannot steal it.
        """
        overrides = env_overrides or {}
        grok_home = resolve_grok_home(env=overrides)
        sessions_root = grok_cwd_sessions_dir(grok_home, cwd)

        if bound_session_id:
            session_dir = grok_session_dir(grok_home, cwd, bound_session_id)
            return (session_dir, session_dir / "events.jsonl"), None

        # Startup signal: a new child session directory bumps this parent.
        # Never return ``grok_home`` itself — that is the #6933 contamination
        # channel (logs/, active_sessions.json, peer sessions, …).
        # Until the child mkdir, an already-existing sessions_root is a
        # stale-only signal against the stall timer (#6935 startup window).
        paths: list[Path] = [sessions_root]

        known: set[Path] = (
            set(snapshot) if snapshot is not None else (set(getattr(self, "_session_dir_snapshot", set()) or set()))
        )
        try:
            children = [path for path in sessions_root.iterdir() if path.is_dir()] if sessions_root.is_dir() else []
        except OSError:
            children = []

        new_sessions = [path for path in children if path not in known]
        discovered_id: str | None = None
        if new_sessions:

            def _mtime(path: Path) -> float:
                try:
                    return path.stat().st_mtime
                except OSError:
                    return 0.0

            newest = max(new_sessions, key=_mtime)
            paths.append(newest)
            paths.append(newest / "events.jsonl")
            discovered_id = newest.name

        # Preserve order while dropping duplicates.
        return tuple(dict.fromkeys(paths)), discovered_id


def _translate_mcp_prefix_for_grok_build(prompt: str) -> str:
    """Rewrite canonical MCP names to native grok-build tool names."""
    return prompt.replace("mcp__sources__", "sources__")


def _adapt_prompt_for_grok_build_mcp(prompt: str) -> str:
    """Adapt canonical MCP review prompts for native grok-build headless."""
    translated = _translate_mcp_prefix_for_grok_build(prompt)
    return (
        translated + "\n\n## Native grok-build headless compatibility\n\n"
        "You are running in native grok-build single-turn headless mode. "
        "Do not call abstract `search_tool` or `use_tool` protocols, do not "
        "call `read_file`, and do not describe a plan. The article text and "
        "instructions above are sufficient for this review. Return the final "
        "JSON object now, starting with `{` and ending with `}`.\n"
    )


# streaming-messages-json (Anthropic Messages) and its partial-message framing.
# `type:error` is excluded: a lone error object stays on the legacy JSON path.
_GROK_MESSAGE_STREAM_TYPES = frozenset(
    {
        "system",
        "assistant",
        "user",
        "result",
        "message_start",
        "content_block_start",
        "content_block_delta",
        "content_block_stop",
        "message_delta",
        "message_stop",
    }
)
# streaming-json: one ACP-derived session update per line. `usage` is the
# per-response boundary. `end` carries the turn's stop reason.
_GROK_UPDATE_STREAM_TYPES = frozenset(
    {
        "thought",
        "tool_call",
        "tool_call_update",
        "text",
        "usage",
        "plan",
        "available_commands",
        "end",
    }
)


def _grok_stream_marker(obj: dict) -> bool:
    kind = obj.get("type")
    if not isinstance(kind, str) or kind == "error":
        return False
    if kind in _GROK_MESSAGE_STREAM_TYPES or kind in _GROK_UPDATE_STREAM_TYPES:
        return True
    return kind == "max_turns_reached" or kind.startswith("auto_compact")


def _complete_json_objects(stdout: str) -> list[dict]:
    """Return JSON objects that occupy one physical line.

    Records split at LF only, so U+0085, U+2028 and U+2029 inside a JSON
    string stay in that record. Pretty-printed single objects and log noise
    are not stream events. A line that does not parse as one object is left
    for the legacy parser.
    """
    objects: list[dict] = []
    for line in jsonl_lines(stdout):
        stripped = line.strip()
        if not stripped.startswith("{"):
            continue
        try:
            value = json.loads(stripped)
        except ValueError:
            continue
        if isinstance(value, dict):
            objects.append(value)
    return objects


def _remember_session(obj: dict, session_id: str | None) -> str | None:
    for key in ("sessionId", "session_id"):
        value = obj.get(key)
        if isinstance(value, str) and value:
            return value
    return session_id


def _frame_stop_reason(obj: dict) -> str | None:
    """Return this frame's stop reason when the field is a string.

    JSON null and a missing field are both absent. An empty string is present.
    """
    stop = obj.get("stopReason")
    if not isinstance(stop, str):
        stop = obj.get("stop_reason")
    return stop if isinstance(stop, str) else None


def _remember_terminal(
    obj: dict,
    *,
    stop_reason: str | None,
    session_id: str | None,
    model_usage: dict | None,
) -> tuple[str | None, str | None, dict | None]:
    stop = _frame_stop_reason(obj)
    if stop is not None:
        stop_reason = stop
    session_id = _remember_session(obj, session_id)
    usage = obj.get("modelUsage")
    if isinstance(usage, dict):
        model_usage = usage
    return stop_reason, session_id, model_usage


def _stream_error_message(obj: dict) -> str:
    for key in ("message", "error"):
        value = obj.get(key)
        if isinstance(value, str) and value:
            return value
    return "grok stream error"


def _result_is_error(obj: dict) -> bool:
    if obj.get("is_error") is True:
        return True
    subtype = obj.get("subtype")
    return isinstance(subtype, str) and subtype.startswith("error")


def _result_error_detail(obj: dict) -> str | None:
    """Return ``errors[0]`` when it is a non-empty string.

    With a stop reason the caller stores this as diagnostic detail. With a
    null or missing stop reason it is the provider error message.
    """
    errors = obj.get("errors")
    if not isinstance(errors, list) or not errors:
        return None
    first = errors[0]
    if isinstance(first, str) and first.strip():
        return first
    return None


def _message_text_blocks(message: dict) -> str:
    """Concatenate text blocks of one assistant message. Tool blocks are not text."""
    content = message.get("content")
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text" and isinstance(block.get("text"), str):
            parts.append(block["text"])
    return "".join(parts)


def _join_messages(parts: list[str]) -> str:
    """Join separate messages with a newline. Empty messages add no blank line."""
    return "\n".join(part for part in parts if part)


def _stream_envelope(
    *,
    text: str,
    stop_reason: str | None,
    session_id: str | None,
    model_usage: dict | None,
    error_message: str | None,
    detail_message: str | None = None,
) -> dict:
    if error_message is not None:
        envelope: dict = {"type": "error", "message": error_message, "text": text}
    else:
        envelope = {"text": text}
        # Detail from a result frame's errors[0]. Presence of message does not
        # make the envelope a provider failure; only type=error does.
        if detail_message:
            envelope["message"] = detail_message
    if stop_reason is not None:
        envelope["stopReason"] = stop_reason
    if session_id is not None:
        envelope["sessionId"] = session_id
    if model_usage is not None:
        envelope["modelUsage"] = model_usage
    return envelope


def _messages_stream_envelope(objects: list[dict]) -> dict:
    """Assemble streaming-messages-json from assistant frames and text deltas.

    Text blocks and ``text_delta`` chunks of one message concatenate. Separate
    assistant messages join with a newline. A flushed assistant frame for an
    id replaces that id's deltas so partial framing is not counted twice.
    ``result.result`` is only the last message and is used when no assistant
    text was assembled. An error-subtype ``result`` that carries a
    ``stop_reason`` stays this ordinary envelope: ``stopReason`` is the turn's
    reason and ``errors[0]`` is diagnostic ``message``. An error-subtype
    ``result`` whose ``stop_reason`` is null or missing is the new-format
    equivalent of ``type:error``: ``errors[0]`` is the provider message, so
    typed codes classify from it (#10005).
    """
    slots: dict[str, dict] = {}
    order: list[str] = []
    anon = 0
    current_partial: str | None = None
    result_text: str | None = None
    stop_reason: str | None = None
    session_id: str | None = None
    model_usage: dict | None = None
    error_message: str | None = None
    detail_message: str | None = None

    def fresh_id() -> str:
        nonlocal anon
        anon += 1
        return f"anon:{anon}"

    def slot(message_id: str) -> dict:
        found = slots.get(message_id)
        if found is None:
            found = {"frame": "", "deltas": [], "saw_frame": False}
            slots[message_id] = found
            order.append(message_id)
        return found

    for obj in objects:
        kind = obj.get("type")
        session_id = _remember_session(obj, session_id)
        if kind == "message_start":
            message = obj.get("message") if isinstance(obj.get("message"), dict) else {}
            message_id = message.get("id")
            if not isinstance(message_id, str) or not message_id:
                message_id = fresh_id()
            current_partial = message_id
            slot(message_id)
        elif kind == "content_block_delta":
            delta = obj.get("delta")
            if isinstance(delta, dict) and delta.get("type") == "text_delta" and isinstance(delta.get("text"), str):
                if current_partial is None:
                    current_partial = fresh_id()
                slot(current_partial)["deltas"].append(delta["text"])
        elif kind == "message_stop":
            current_partial = None
        elif kind == "assistant":
            message = obj.get("message") if isinstance(obj.get("message"), dict) else {}
            message_id = message.get("id")
            if not isinstance(message_id, str) or not message_id:
                message_id = fresh_id()
            rec = slot(message_id)
            rec["saw_frame"] = True
            rec["frame"] = _message_text_blocks(message)
        elif kind == "result":
            stop_reason, session_id, model_usage = _remember_terminal(
                obj, stop_reason=stop_reason, session_id=session_id, model_usage=model_usage
            )
            # A named stop_reason keeps cancelled and max-turns turns on the
            # ordinary final path (#9987). Null or missing stop_reason is the
            # streaming-messages-json form of type=error (#10005).
            if _result_is_error(obj) and _frame_stop_reason(obj) is None:
                if error_message is None:
                    error_message = _result_error_detail(obj) or "grok stream error"
            elif _result_is_error(obj):
                if detail_message is None:
                    detail_message = _result_error_detail(obj)
            elif isinstance(obj.get("result"), str):
                result_text = obj["result"]
        elif kind == "error" and error_message is None:
            error_message = _stream_error_message(obj)
            stop_reason, session_id, model_usage = _remember_terminal(
                obj, stop_reason=stop_reason, session_id=session_id, model_usage=model_usage
            )

    parts = [rec["frame"] if rec["saw_frame"] else "".join(rec["deltas"]) for rec in (slots[mid] for mid in order)]
    text = _join_messages(parts)
    if not text and isinstance(result_text, str):
        text = result_text
    return _stream_envelope(
        text=text,
        stop_reason=stop_reason,
        session_id=session_id,
        model_usage=model_usage,
        error_message=error_message,
        detail_message=None if error_message is not None else detail_message,
    )


def _updates_stream_envelope(objects: list[dict]) -> dict:
    """Assemble streaming-json. ``text`` events are chunks of the current message.

    A ``usage`` event, or a changed ``messageId``, ends that message. The next
    message is joined with a newline. Tool calls do not split a message.
    ``end`` supplies the turn stop reason, session id, and model usage.
    """
    chunks: list[str] = []
    parts: list[str] = []
    open_id: str | None = None
    stop_reason: str | None = None
    session_id: str | None = None
    model_usage: dict | None = None
    error_message: str | None = None

    def flush() -> None:
        nonlocal open_id
        text = "".join(chunks)
        chunks.clear()
        open_id = None
        if text:
            parts.append(text)

    for obj in objects:
        kind = obj.get("type")
        if kind == "text":
            message_id = obj.get("messageId")
            message_id = message_id if isinstance(message_id, str) and message_id else None
            if chunks and message_id is not None and open_id is not None and message_id != open_id:
                flush()
            if message_id is not None:
                open_id = message_id
            data = obj.get("data")
            if isinstance(data, str):
                chunks.append(data)
        elif kind == "usage":
            flush()
        elif kind == "end":
            stop_reason, session_id, model_usage = _remember_terminal(
                obj, stop_reason=stop_reason, session_id=session_id, model_usage=model_usage
            )
        elif kind == "error" and error_message is None:
            error_message = _stream_error_message(obj)
            stop_reason, session_id, model_usage = _remember_terminal(
                obj, stop_reason=stop_reason, session_id=session_id, model_usage=model_usage
            )
    flush()
    return _stream_envelope(
        text=_join_messages(parts),
        stop_reason=stop_reason,
        session_id=session_id,
        model_usage=model_usage,
        error_message=error_message,
    )


def _grok_stream_envelope(stdout: str) -> dict | None:
    """Return a legacy ``{text, stopReason, sessionId, modelUsage}`` envelope.

    Returns None when stdout is not a message stream, including a lone
    ``{"type":"error",...}`` object. The caller then uses the single-object
    parser. Separate assistant messages are joined with a newline; chunks of
    one message are concatenated.
    """
    objects = _complete_json_objects(stdout)
    if not any(_grok_stream_marker(obj) for obj in objects):
        return None
    if any(obj.get("type") in _GROK_MESSAGE_STREAM_TYPES for obj in objects):
        return _messages_stream_envelope(objects)
    return _updates_stream_envelope(objects)


def _parse_json_object(stdout: str) -> dict | None:
    """Parse the single JSON object grok emits in --output-format json.

    Tolerant of leading/trailing log noise: tries a strict parse first, then
    extracts the outermost ``{...}`` span.
    """
    text = (stdout or "").strip()
    if not text:
        return None
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else None
    except ValueError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        try:
            value = json.loads(text[start : end + 1])
            return value if isinstance(value, dict) else None
        except ValueError:
            return None
    return None
