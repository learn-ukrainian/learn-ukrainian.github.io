"""GrokBuildAdapter — wraps the native ``grok`` CLI headless.

Registry seat id is canonical ``grok`` (historical alias ``grok-build``).
DISTINCT from the Hermes-backed ``grok-hermes`` agent (``HermesGrokAdapter``,
a banned/demoted route pinned to its own legacy model, via the Hermes OAuth
API path). This adapter drives
the local ``grok`` CLI binary (``~/.local/bin/grok``) in
single-turn headless mode:

    grok -p "<prompt>" --output-format json [-m MODEL] [--effort LEVEL] \
         --permission-mode <mode> --cwd <dir> --no-alt-screen

Headless JSON output is a single object: ``{text, stopReason, sessionId, ...}``.
The CLI uses its own stored auth under ``~/.grok`` (OAuth), so no API key is
injected — HOME (already allow-listed by env_sanitize) is sufficient.

Mode → ``--permission-mode``:
- ``read-only``       → ``auto`` + fail-closed ``--deny`` on write tools and ``Bash``
  (Read/Grep/Glob still run; no shell — prefix deny lists are not a closed allowlist under ``auto``)
- ``workspace-write`` → ``auto`` + ``--always-approve``
  (unattended tool execution and file edits within the dispatch worktree)
- ``danger``          → ``bypassPermissions`` + ``--always-approve``
  (unattended full autonomy within the dispatch worktree)

Issue #7583: On native Grok 1.0.x CLI, ``acceptEdits --always-approve`` still prompts
for approval on shell commands and terminates headless turns (``stopReason=cancelled``),
while ``plan`` blocks all tool calls outright. Write dispatches map to execution-capable
``auto``/``bypassPermissions`` with ``--always-approve``. Ordinary ``read-only`` also
maps to ``auto`` so non-shell read tools can run, but must deny ``Bash`` and write tools
fail-closed (same posture as sealed ``review_isolation`` Bash denial).

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
import shutil
import tempfile
from pathlib import Path
from urllib.parse import quote

from ..result import ParseResult
from ..trail_isolation import (
    GROK_TRAIL_DENY_TOOLS,
    GROK_TRAIL_TOOLS,
    TrailIsolationError,
    assert_trail_isolation_config,
    trail_isolation_requested,
)
from .base import InvocationPlan

_logger = logging.getLogger(__name__)

_RATE_LIMIT_RE = re.compile(
    r"rate limit|rate_limit|usage limit|quota exceeded|too many requests|\b429\b",
    re.IGNORECASE,
)

# Runtime mode → grok CLI --permission-mode value.
# Issue #7583: on grok 1.0.x, acceptEdits does not cover shell headlessly (turn
# cancels), while plan blocks all tool calls. We map workspace-write to auto
# (with --always-approve) and read-only to auto with fail-closed Bash/write denies.
_MODE_PERMISSION: dict[str, str] = {
    "read-only": "auto",
    "workspace-write": "auto",
    "danger": "bypassPermissions",
}

# Non-isolated write-capable dispatches grant --always-approve so tool executions
# run without a human approval prompt.
_UNATTENDED_WRITE_MODES: frozenset[str] = frozenset({"workspace-write", "danger"})

# Deny rules for ordinary read-only (issue #7583 / PR #7594 CF): grok
# --permission-mode auto may approve unnamed commands, and prefix Bash denies
# are not fail-closed (gh api, git -C … push, tee, sed -i, …). Deny Bash and
# write tools wholesale — same fail-closed shell posture as review_isolation.
_READ_ONLY_DENY_RULES: tuple[str, ...] = (
    "Write",
    "Edit",
    "MultiEdit",
    "NotebookEdit",
    "search_replace",
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
    "MultiEdit",
    "NotebookEdit",
    "search_replace",
    "Bash",
)
# Operator order 2026-08-16 (issue #6865): grok is at 4.6; retire the 4.5 pin.
GROK_ALLOWED_MODELS: frozenset[str] = frozenset({"grok-4.6"})
GROK_SUPPORTED_EFFORTS: frozenset[str] = frozenset({"low", "medium", "high"})
GROK_BUILD_DEFAULT_MODEL = "grok-4.6"
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

        cmd.extend(["--output-format", "json", "--no-alt-screen"])
        # Issue #7583 / #7594: ordinary read-only maps to grok `auto` so non-shell
        # read tools can run, with fail-closed `--deny` on Bash + write tools.
        # Prefix-only Bash denies are not a closed allowlist under `auto`.
        # MCP-grounded reviews execute tool calls (e.g. sources__verify_words)
        # under bypassPermissions with MCP deny rules.
        mcp_servers_requested = set(tc.get("mcp_server_names") or [])
        mcp_read_only = bool(mcp_servers_requested) and mcp_servers_requested <= _READ_ONLY_MCP_SERVERS
        # Review isolation (#5285): expose only built-in read tools. The
        # parent-owned OS sandbox limits them to the sealed view; explicit deny
        # rules remove shell/write/nested execution even though headless tool
        # calls require an execution-capable permission mode.
        if trail_isolation:
            permission_mode = "default"
        elif review_isolation:
            permission_mode = str(tc.get("permission_mode") or "bypassPermissions")
        else:
            permission_mode = "bypassPermissions" if mcp_read_only else _MODE_PERMISSION[mode]
        cmd.extend(["--permission-mode", permission_mode])
        cmd.extend(["--cwd", str(execution_cwd)])
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
            deny_rules = tc.get("review_deny_tools") or list(_MCP_REVIEW_DENY_RULES)
            if isinstance(deny_rules, (list, tuple)):
                for rule in deny_rules:
                    if rule:
                        cmd.extend(["--deny", str(rule)])

        effective_effort = validate_grok_effort(effort or self.default_effort)
        cmd.extend(["-m", requested_model])
        if effective_effort:
            # The native Grok CLI accepts only low|medium|high.
            cmd.extend(["--effort", effective_effort])

        disallowed = tc.get("disallowed_tools")
        if disallowed:
            cmd.extend(["--disallowed-tools", str(disallowed)])
        allowed = tc.get("allowed_tools")
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
            _MODE_PERMISSION[mode],
            requested_model,
            effective_effort,
        )

        snapshot = self._reset_per_invocation_state(
            cwd=execution_cwd,
            env_overrides={},
        )
        metadata: dict[str, object] = {
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
            env_overrides={},
            liveness_paths=liveness_paths,
            metadata=metadata,
            host_harness="grok",
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
        _ = (output_file, plan, call_start_time)  # grok -p flushes to stdout

        obj = _parse_json_object(stdout)
        if obj is not None:
            text = str(obj.get("text") or "").strip()
            sid = obj.get("sessionId") or obj.get("session_id")
            session_id = sid if isinstance(sid, str) and sid else None
        else:
            # Fallback: --output-format plain, or noise before the JSON.
            text = (stdout or "").strip()
            session_id = None

        usable = bool(text)
        failed = returncode != 0 or not usable
        rate_limited = failed and bool(_RATE_LIMIT_RE.search(f"{stderr or ''}\n{stdout or ''}"))
        ok = returncode == 0 and usable and not rate_limited

        stderr_excerpt: str | None = None
        if not ok:
            source = (stderr or "").strip() or (stdout or "").strip() or ""
            stderr_excerpt = source[:500] or None

        return ParseResult(
            ok=ok,
            response=text if ok else "",
            stderr_excerpt=stderr_excerpt,
            rate_limited=rate_limited,
            session_id=session_id,
            tokens=None,  # grok JSON does not report token counts
            tool_calls=[],
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
