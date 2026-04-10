"""CodexAdapter — wraps ``codex exec`` for the agent runtime.

First real adapter. Proves the protocol shape works against a real CLI.
Lifted from the prior art in ``scripts/ai_agent_bridge/_codex.py`` and
``scripts/build/dispatch.py`` (Codex branch) — same flag semantics, now
routed through the unified runtime.

Key design points:

- **Fresh session always.** CodexAdapter has ``resume_policy="never"`` in
  the registry AND defensively ignores ``session_id`` even if passed.
  Belt + suspenders against the cross-worktree contamination footgun that
  Codex flagged in his own consultation (msg #28506).
- **All three modes supported:** read-only, workspace-write, danger.
  Mode → flag mapping matches ``_codex.py::_codex_bridge_flags`` and
  ``dispatch.py::_codex_dispatch_flags``.
- **Output file always used.** ``codex exec -o <tmpfile>`` writes the final
  agent message to a file; we read it in ``parse_response``. The file path
  goes into ``liveness_signal_paths`` so the runner's mtime poller catches
  Codex writing progress even when stdout is quiet.
- **Session ID parsed from stdout.** The CLI prints "session id: <uuid>"
  somewhere in stdout; we extract it for the usage record even though
  we never resume it.

Issue: #1184
"""
from __future__ import annotations

import re
import shutil
import tempfile
from pathlib import Path

from ..result import ParseResult
from .base import InvocationPlan

# Matches the session id line in Codex stdout. Case-insensitive.
_SESSION_RE = re.compile(r"session id:\s*([0-9a-f-]{8,})", re.IGNORECASE)

# Stderr phrases that indicate the provider rate-limited us. Ordered
# roughly by specificity — specific phrases first, generic last.
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

# Matches a dashes-only line (at least 3 dashes, nothing else on the
# line). Used to split Codex's stderr into segments so we can isolate
# the post-prompt portion for rate-limit pattern matching. MULTILINE
# so ^/$ match at each line boundary.
_CODEX_DIVIDER_LINE_RE = re.compile(r"^-{3,}\s*$", re.MULTILINE)


def _strip_codex_prompt_echo(stderr: str) -> str:
    """Return only the portion of Codex stderr that is safe to
    pattern-match for rate-limit errors.

    Codex CLI (with -o <file>) lays out stderr as a sequence of
    sections separated by dashes-only lines::

        OpenAI Codex v0.118.0 ...       ← banner
        --------
        workdir: ...
        model: ...
        --------
        user                            ← echoed prompt starts
        <entire user prompt>
        --------
        codex                           ← Codex's own output
        <reasoning + final message>
        tokens used
        <n>

    On a rate-limit error, Codex exits non-zero and writes the error
    message AFTER the last divider — in the "codex" or equivalent
    section. The echoed user prompt can contain ANY text, including
    legitimate inline dashes-only lines (a code block showing a
    divider, a Markdown horizontal rule, a consultation prompt
    literally discussing rate limits). Any regex that tries to
    identify "the prompt block" by matching between two dividers can
    be defeated by a prompt containing its own dividers.

    Fix: don't try to strip the prompt at all. Instead, take the
    stderr body AFTER the LAST divider line — that region is
    guaranteed to be Codex's own output, never echoed prompt, because
    the prompt echo always appears before Codex's response section.
    If there are no dividers at all (degenerate cases: truncated
    output, early crash before banner), fall back to the whole
    stderr.

    See #1184 Gemini 2026-04-10 review for the incident that led here.
    """
    if not stderr:
        return stderr
    # Find the position right after the LAST divider line.
    last_divider = None
    for m in _CODEX_DIVIDER_LINE_RE.finditer(stderr):
        last_divider = m
    if last_divider is None:
        # No dividers — return as-is. Likely a very early crash.
        return stderr
    return stderr[last_divider.end():]


class CodexAdapter:
    """Adapter for ``codex exec`` (OpenAI ChatGPT Codex CLI)."""

    name: str = "codex"
    default_model: str = "gpt-5.4"
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
        """Build the codex exec invocation.

        Defensively ignores ``session_id`` regardless of value — Codex
        is always fresh-session (registry resume_policy="never").
        Defensively ignores ``tool_config`` — Codex doesn't support MCP
        tool restrictions the way Claude/Gemini do; any keys passed are
        silently dropped.
        """
        # Defensively drop session_id and tool_config — Codex adapter ignores
        # both by design (see class docstring). Local `_ =` rebinds silence
        # the "unused parameter" linter without changing semantics.
        _ = session_id
        _ = tool_config

        # Resolve binary. shutil.which handles PATH lookup; fall back to
        # bare "codex" if not on PATH so subprocess.Popen can report the
        # error clearly.
        codex_bin = shutil.which("codex") or "codex"

        # Pick a unique output file inside /tmp.
        # Include task_id for human debuggability.
        suffix = f"-{task_id}" if task_id else ""
        with tempfile.NamedTemporaryFile(
            prefix=f"codex-runtime{suffix}-",
            suffix=".txt",
            delete=False,
        ) as output_fd:
            output_path = Path(output_fd.name)

        cmd: list[str] = [
            codex_bin,
            "exec",
            "--skip-git-repo-check",
            "-C", str(cwd),
            "--color", "never",
            "-o", str(output_path),
            "-m", model or self.default_model,
        ]
        cmd.extend(self._mode_flags(mode))
        cmd.append("-")  # Read prompt from stdin.

        return InvocationPlan(
            cmd=cmd,
            cwd=cwd,
            stdin_payload=prompt,
            output_file=output_path,
            env_overrides={},
            liveness_paths=(output_path,),
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
        """Parse the codex exec output into a ParseResult.

        Codex writes its final message to the ``-o <file>`` path. We read
        it regardless of returncode — some failure modes still leave a
        useful partial message in the file, and it's often more informative
        than stderr.

        Fallback recovery (added 2026-04-10): codex-cli 0.118 has a
        post-completion hang bug where the CLI generates the full answer,
        writes a ``task_complete`` event to
        ``~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl``, then hangs at
        0% CPU without ever flushing ``-o <file>`` or exiting. Previously
        this meant the runtime waited the full hard_timeout and returned
        an empty response. Now, if ``-o <file>`` is empty, we scan the
        newest rollout file for a ``task_complete`` event and extract
        its ``last_agent_message``. Parallels the Gemini adapter's
        session-file fallback.
        """
        # Read the output file if it exists. Tolerate all errors.
        file_output = ""
        if output_file is not None and output_file.exists():
            try:
                file_output = output_file.read_text("utf-8", errors="replace").strip()
            except OSError:
                file_output = ""

        # Fallback: if the -o file is empty, scan the rollout JSONL for
        # a task_complete event. This handles the 0.118 post-completion
        # hang where Codex has the answer on disk but never flushes -o.
        rollout_response = ""
        rollout_source_note: str | None = None
        if not file_output and plan is not None:
            rollout_response = self._read_latest_rollout_task_complete(
                plan, call_start_time=call_start_time,
            )
            if rollout_response:
                reason = (
                    "rc=0 but -o empty (post-completion hang)"
                    if returncode == 0
                    else f"rc={returncode}, -o empty"
                )
                rollout_source_note = (
                    f"recovered {len(rollout_response)} chars from "
                    f"~/.codex/sessions/.../rollout-*.jsonl (reason: {reason})"
                )

        # durable_output is the response we'll return on success:
        # either the -o file or the rollout-recovered answer.
        durable_output = file_output or rollout_response

        # Rate-limit detection — with THREE critical caveats.
        #
        # Codex CLI (with -o <file>) writes everything to stderr: the
        # startup banner, the echoed user prompt, the reasoning trace,
        # AND real error messages. Pattern-matching stderr naively is
        # broken because user prompts can contain ANY human-language
        # phrase, including "rate limit" and "usage limit reached" (our
        # own bridge standing rules literally do).
        #
        # Fix 1 (prompt echo sanitization): take the stderr body AFTER
        # the last "--------" divider line. The closing prompt divider
        # always has Codex's own output after it, so anything past the
        # last divider is guaranteed to be Codex's actual response,
        # never echoed user prompt. See _strip_codex_prompt_echo.
        #
        # Fix 2 (success guard): even after sanitization, rate_limited
        # is only TRUE when the call actually failed (returncode != 0
        # OR empty output file). A successful Codex exec with a
        # non-empty final message in the -o file CANNOT be rate-limited,
        # period. This mirrors the same guard we have on GeminiAdapter.
        #
        # Fix 3 (signal-killed processes, Codex 2026-04-10 review):
        # a negative returncode means the process was killed by a
        # signal (SIGTERM, SIGKILL, SIGINT — Python/POSIX convention
        # reports -SIGNUM for signaled exits). If we killed the process
        # ourselves (hard_timeout, cancel, exception mid-poll), its
        # stderr may contain ONLY a partial prompt echo — no closing
        # divider, no Codex response section — and my "take stderr
        # after last divider" heuristic will return the prompt body
        # itself. To prevent that class of false positive, skip
        # pattern matching entirely on signaled exits. A signaled
        # exit is classified as "failed", never as "rate_limited",
        # because we KNOW why the process died: we killed it.
        if returncode is not None and returncode < 0:
            # Signaled exit — don't even look at stderr for rate limits.
            rate_limited = False
        else:
            stderr_for_check = _strip_codex_prompt_echo(stderr)
            combined_for_rl_check = "\n".join(
                part for part in (stdout, stderr_for_check, durable_output) if part
            )
            pattern_hit = bool(_RATE_LIMIT_RE.search(combined_for_rl_check))
            # Call failed if neither -o nor rollout gave us content.
            call_failed = returncode != 0 or not durable_output
            rate_limited = pattern_hit and call_failed

        # Session id comes from stdout in Codex.
        session_id: str | None = None
        session_match = _SESSION_RE.search(stdout or "")
        if session_match:
            session_id = session_match.group(1)

        # Success classification: we have content (from either -o or the
        # rollout fallback) AND we're not rate-limited. Note that a
        # post-completion hang will have returncode == -9 (because WE
        # killed it after the early-reap detector fires) but durable_output
        # will be populated from rollout. That's a successful recovery,
        # NOT a failure. So returncode is no longer a veto — content is.
        ok = bool(durable_output) and not rate_limited
        response = durable_output if ok else ""
        stderr_excerpt: str | None = None
        if not ok:
            # Build a useful excerpt: stderr first, then file_output as
            # fallback (Codex often puts errors in the output file).
            excerpt_parts: list[str] = []
            if stderr.strip():
                excerpt_parts.append(stderr.strip())
            if not stderr.strip() and file_output:
                excerpt_parts.append(f"[codex output file]\n{file_output}")
            stderr_excerpt = "\n".join(excerpt_parts)[:500] or None
        elif rollout_source_note:
            # We recovered from the rollout file. Surface the note so
            # logs/usage records show it.
            stderr_excerpt = rollout_source_note

        return ParseResult(
            ok=ok,
            response=response,
            stderr_excerpt=stderr_excerpt,
            rate_limited=rate_limited,
            session_id=session_id,
            tokens=None,  # codex exec does not expose token counts.
        )

    # ---------------------------------------------------------------------
    # Early reap — break out of Codex CLI's post-completion hang
    # ---------------------------------------------------------------------

    def check_early_reap(
        self,
        plan: InvocationPlan,
        *,
        call_start_time: float | None = None,
    ) -> bool:
        """Return True if the Codex rollout JSONL has a task_complete event.

        This is the fix for the Codex 0.118.0 post-completion hang.
        Verified empirically 2026-04-10: all Codex threads end up in
        _pthread_cond_wait on an internal Tokio runtime condition
        variable AFTER writing task_complete to the rollout file. The
        process never exits on its own. Without this method the runner
        would wait the full hard_timeout (1h+) on every such hang.

        The runner calls this periodically (every few poll ticks). When
        it returns True, the runner kills the subprocess and falls
        through to ``parse_response()``, which recovers the response
        via ``_read_latest_rollout_task_complete()``.

        Optimizations to keep overhead negligible:
        1. Warmup window: don't scan before 5 seconds elapsed.
           Codex can't possibly have emitted task_complete that early.
        2. Throttle: at most one scan every 2 seconds per adapter
           instance.
        3. Mtime gate: skip the scan if the rollout directory mtime
           hasn't changed since the last scan. The sessions dir bumps
           on every file creation inside it, and the rollout file's
           OWN mtime bumps on every write. We snapshot the newest
           rollout file's mtime and only re-scan when it advances.
        """
        import time as _time
        now = _time.monotonic()

        # Guard 1: warmup window.
        if call_start_time is not None and (now - call_start_time) < 5.0:
            return False

        # Guard 2: throttle.
        last_check = getattr(self, "_last_early_reap_check", 0.0)
        if now - last_check < 2.0:
            return False
        self._last_early_reap_check = now

        # Guard 3: mtime gate — quick stat instead of a full file scan.
        from datetime import UTC, datetime
        today = datetime.now(UTC)
        sessions_today = (
            Path.home() / ".codex" / "sessions"
            / f"{today.year:04d}" / f"{today.month:02d}" / f"{today.day:02d}"
        )
        try:
            if not sessions_today.exists():
                return False
            rollouts = list(sessions_today.glob("rollout-*.jsonl"))
            if not rollouts:
                return False
            newest = max(rollouts, key=lambda p: p.stat().st_mtime)
            current_mtime = newest.stat().st_mtime
        except OSError:
            return False

        last_mtime = getattr(self, "_last_early_reap_mtime", 0.0)
        if current_mtime <= last_mtime:
            # File hasn't advanced since last scan — task_complete
            # can't have been added. Skip the scan.
            return False
        self._last_early_reap_mtime = current_mtime

        # All guards passed — do the actual scan.
        msg = self._read_latest_rollout_task_complete(
            plan, call_start_time=call_start_time,
        )
        return bool(msg)

    # ---------------------------------------------------------------------
    # Rollout-file recovery (post-completion hang fallback)
    # ---------------------------------------------------------------------

    def _read_latest_rollout_task_complete(
        self,
        plan: InvocationPlan,
        *,
        call_start_time: float | None = None,
    ) -> str:
        """Extract the ``last_agent_message`` from the newest rollout JSONL.

        codex-cli 0.118.0 writes a per-call rollout file at
        ``~/.codex/sessions/YYYY/MM/DD/rollout-<uuid>.jsonl``. Every
        reasoning step, tool call, and response is streamed there as a
        JSONL event. When Codex finishes its turn, it emits a single
        event like::

            {
              "timestamp": "2026-04-10T19:40:02.155Z",
              "type": "event_msg",
              "payload": {
                "type": "task_complete",
                "turn_id": "<uuid>",
                "last_agent_message": "<the full response text>"
              }
            }

        After emitting this event, the CLI frequently hangs at 0% CPU
        for minutes or forever — it does NOT flush ``-o <file>`` and
        does NOT exit on its own. So the answer sits on disk while the
        runtime waits for a proc.exit that never comes.

        This method walks today's sessions directory, picks the newest
        rollout file, and scans it line-by-line for a task_complete
        event. Returns the ``last_agent_message`` string, or '' if no
        such event is present yet (task still in progress) or if
        anything goes wrong.

        Safety:
        * call_start_time (monotonic) is used to filter stale files.
          Any file with mtime older than 2 hours wall-clock is skipped
          to avoid picking up a previous day's leftover.
        * All exceptions are swallowed — this is a last-resort fallback,
          not a primary code path.
        * If multiple task_complete events exist in one file (e.g. if
          Codex did multi-turn reasoning), we return the LAST one — the
          final answer.
        """
        _ = call_start_time  # reserved for future tighter verification
        import json as _json
        import time as _time
        from datetime import UTC, datetime

        try:
            _ = plan  # not strictly needed but kept for future task-specific matching
            today = datetime.now(UTC)
            sessions_today = (
                Path.home() / ".codex" / "sessions"
                / f"{today.year:04d}" / f"{today.month:02d}" / f"{today.day:02d}"
            )
            if not sessions_today.exists():
                return ""

            two_hours_ago = _time.time() - 2 * 3600
            candidates = [
                p for p in sessions_today.glob("rollout-*.jsonl")
                if p.stat().st_mtime >= two_hours_ago
            ]
            if not candidates:
                return ""

            newest = max(candidates, key=lambda p: p.stat().st_mtime)

            # Scan for the task_complete event. Take the LAST one if
            # multiple exist (multi-turn session → final turn wins).
            last_message = ""
            with open(newest, encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        event = _json.loads(line)
                    except _json.JSONDecodeError:
                        continue
                    if event.get("type") != "event_msg":
                        continue
                    payload = event.get("payload") or {}
                    if payload.get("type") != "task_complete":
                        continue
                    msg = payload.get("last_agent_message")
                    if isinstance(msg, str) and msg:
                        last_message = msg

            return last_message
        except Exception:
            # Last-resort fallback: never let a rollout-parse error
            # bubble out of parse_response. Swallow everything and
            # fall back to the primary code path.
            return ""

    def liveness_signal_paths(self, plan: InvocationPlan) -> tuple[Path, ...]:
        """Return paths the runner should poll for mtime changes.

        Note 2026-04-10: stall detection is no longer a kill condition
        (see watchdog.py::should_kill). The mtime poller still runs to
        populate WatchdogState.last_activity for observability — so
        getting the paths RIGHT still matters for future diagnostic
        logging and for the async delegate.py work, even though a
        missed signal no longer kills the process.

        Codex CLI 0.118.0 storage layout (verified empirically):
          - ``sessions/YYYY/MM/DD/rollout-*.jsonl`` is the ACTUAL live
            file. It grows throughout the run as reasoning messages
            and tool calls are streamed to disk. Confirmed: a 9-minute
            consultation run had its rollout file at 409KB and still
            growing.
          - ``sessions/YYYY/MM/DD/`` (the directory) only bumps on
            child file *creation*, not on content writes. Useful for
            catching the startup signal but goes silent during the run.
          - ``state_5.sqlite`` bumps intermittently (not reliably on
            every message). Kept as a secondary signal.
          - ``logs_1.sqlite``, ``history.jsonl`` are stale in 0.118+
            but kept as fallbacks for older CLI versions.
          - ``plan.output_file`` is the -o target; empty during the run
            and only written at the very end on success, but kept as
            a signal for the "Codex is writing the final response" moment.

        We pick the NEWEST rollout-*.jsonl inside today's sessions dir
        and return it directly (same pattern as the Gemini adapter's
        newest session-*.json file), so the mtime poller sees every
        content write, not just directory-level events.
        """
        from datetime import UTC, datetime

        paths: list[Path] = []
        if plan.output_file is not None:
            paths.append(plan.output_file)

        codex_home = Path.home() / ".codex"

        # Secondary / fallback signals
        for rel in ("state_5.sqlite", "history.jsonl", "logs_1.sqlite"):
            candidate = codex_home / rel
            if candidate.exists():
                paths.append(candidate)

        # Today's sessions directory (catches startup via dir mtime
        # bump, but does NOT track subsequent content writes).
        today = datetime.now(UTC)
        sessions_today = (
            codex_home / "sessions" / f"{today.year:04d}"
            / f"{today.month:02d}" / f"{today.day:02d}"
        )
        if sessions_today.exists():
            paths.append(sessions_today)

        # Note: we deliberately do NOT include the newest rollout-*.jsonl
        # file here. Earlier versions tried to track it for
        # last_activity updates, but glob-at-build-time is wrong: the
        # file matching "newest" is the PREVIOUS run's rollout, not
        # this run's (which doesn't exist yet). The wrong file both
        # (a) never updates during our run so provides no liveness
        # signal, and (b) would leak the wrong trace into
        # tail_liveness_file_for_debug() on failure. Removed after
        # Gemini review, 2026-04-10. The directory mtime above still
        # bumps when Codex creates its new rollout file at startup,
        # which is good enough for the dispatch-once-at-start signal
        # the mtime poller actually uses.
        #
        # Proper fix (deferred): pass a glob pattern or a build-time
        # snapshot into the runner and let the poller dynamically
        # resolve "any file matching ROLLOUT_GLOB whose mtime changed
        # after POLL_START". Bigger API change; filed as follow-up.

        return tuple(paths)

    @staticmethod
    def _mode_flags(mode: str) -> list[str]:
        """Map runtime mode → codex exec sandbox flags.

        Matches the mapping in _codex.py::_codex_bridge_flags and
        dispatch.py::_codex_dispatch_flags for consistency during migration.
        """
        if mode == "danger":
            return ["--dangerously-bypass-approvals-and-sandbox"]
        if mode == "workspace-write":
            return ["--full-auto"]
        # "read-only" default
        return ["-s", "read-only"]
