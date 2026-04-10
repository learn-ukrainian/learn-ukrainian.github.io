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

# Codex CLI (with -o <file>) wraps the echoed user prompt between
# "--------\nuser\n" and the next "--------" marker in stderr. When we
# classify errors, we must strip this block first — user prompts can
# contain any human-language phrase, including "rate limit", and matching
# against them would misclassify every failed call whose prompt mentions
# rate limits as a real rate limit. The regex is multiline/dotall so the
# content between markers can span any number of lines.
_CODEX_PROMPT_ECHO_RE = re.compile(
    r"-{3,}\s*\nuser\n.*?\n-{3,}",
    re.DOTALL,
)


def _strip_codex_prompt_echo(stderr: str) -> str:
    """Remove the echoed user prompt block from Codex CLI stderr.

    Codex writes the full user prompt back to stderr between two
    "--------" dividers when invoked with ``-o <file>``. We strip that
    block before running rate-limit pattern matching to prevent user
    prompt text from poisoning error classification. See #1184.
    """
    if not stderr:
        return stderr
    return _CODEX_PROMPT_ECHO_RE.sub("[user prompt echo stripped]", stderr)


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
    ) -> ParseResult:
        """Parse the codex exec output into a ParseResult.

        Codex writes its final message to the ``-o <file>`` path. We read
        it regardless of returncode — some failure modes still leave a
        useful partial message in the file, and it's often more informative
        than stderr.
        """
        # Read the output file if it exists. Tolerate all errors.
        file_output = ""
        if output_file is not None and output_file.exists():
            try:
                file_output = output_file.read_text("utf-8", errors="replace").strip()
            except OSError:
                file_output = ""

        # Rate-limit detection — with two CRITICAL caveats.
        #
        # Codex CLI (with -o <file>) writes everything to stderr: the
        # startup banner, the echoed user prompt, the reasoning trace,
        # AND real error messages. Pattern-matching stderr naively is
        # broken because user prompts can contain ANY human-language
        # phrase, including "rate limit" and "usage limit reached" (our
        # own bridge standing rules literally do).
        #
        # Fix 1 (prompt echo sanitization): strip the echoed user prompt
        # section from stderr before pattern matching. The Codex CLI
        # wraps the prompt between "--------\nuser\n" and the next
        # "--------" marker. We remove the entire block so its content
        # cannot poison classification.
        #
        # Fix 2 (success guard): even after sanitization, rate_limited
        # is only TRUE when the call actually failed (returncode != 0
        # OR empty output file). A successful Codex exec with a
        # non-empty final message in the -o file CANNOT be rate-limited,
        # period. This mirrors the same guard we have on GeminiAdapter.
        stderr_for_check = _strip_codex_prompt_echo(stderr)
        combined_for_rl_check = "\n".join(
            part for part in (stdout, stderr_for_check, file_output) if part
        )
        pattern_hit = bool(_RATE_LIMIT_RE.search(combined_for_rl_check))
        call_failed = returncode != 0 or not file_output
        rate_limited = pattern_hit and call_failed

        # Session id comes from stdout in Codex.
        session_id: str | None = None
        session_match = _SESSION_RE.search(stdout or "")
        if session_match:
            session_id = session_match.group(1)

        # Success classification.
        ok = returncode == 0 and bool(file_output) and not rate_limited
        response = file_output if ok else ""
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

        return ParseResult(
            ok=ok,
            response=response,
            stderr_excerpt=stderr_excerpt,
            rate_limited=rate_limited,
            session_id=session_id,
            tokens=None,  # codex exec does not expose token counts.
        )

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

            # Primary live signal: the newest rollout-*.jsonl inside
            # today's sessions dir. Codex writes every reasoning line
            # and tool-call event here during exec. Picking at plan
            # build time means we may miss a rollout file created
            # AFTER our call starts (possible if we're slow to start
            # the poller) — the dir mtime signal above catches that
            # creation event as a fallback.
            try:
                rollouts = sorted(
                    sessions_today.glob("rollout-*.jsonl"),
                    key=lambda p: p.stat().st_mtime,
                    reverse=True,
                )
                if rollouts:
                    paths.append(rollouts[0])
            except OSError:
                pass

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
