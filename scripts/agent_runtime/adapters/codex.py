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

        # Combine stdout + stderr + file output for rate-limit pattern
        # matching. The pattern could appear anywhere.
        combined_for_rl_check = "\n".join(
            part for part in (stdout, stderr, file_output) if part
        )
        rate_limited = bool(_RATE_LIMIT_RE.search(combined_for_rl_check))

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

        Codex writes its output file progressively AND also writes to
        several state files in ``~/.codex/`` during exec. We return every
        candidate that exists so the mtime poller has multiple independent
        liveness signals. Fixed 2026-04-10: the old primary signal
        ``logs_1.sqlite`` went stale (Codex stopped writing there in a
        recent version bump), which caused spurious "Codex stalled" errors
        in the bridge because the stdout streamer was the only remaining
        signal and stdout is nearly silent when -o <file> is used.

        Current live candidates (verified against codex-cli 0.118.0):
          - plan.output_file: the -o target file (per-call, grows as
            Codex emits the final message)
          - ~/.codex/state_5.sqlite: live runtime state (bumps during exec)
          - ~/.codex/sessions/{YYYY}/{MM}/{DD}/: directory mtime bumps
            when Codex creates a new rollout-*.jsonl file at the start
            of exec — catches the startup signal even before state_5
            updates

        Legacy paths (kept for backward compat with older CLI versions):
          - ~/.codex/logs_1.sqlite: pre-0.118 primary log
          - ~/.codex/history.jsonl: older history file, some versions
            still update it
        """
        from datetime import UTC, datetime

        paths: list[Path] = []
        if plan.output_file is not None:
            paths.append(plan.output_file)

        codex_home = Path.home() / ".codex"

        # Current live signals
        for rel in ("state_5.sqlite", "history.jsonl", "logs_1.sqlite"):
            candidate = codex_home / rel
            if candidate.exists():
                paths.append(candidate)

        # Today's sessions directory — mtime bumps when new rollout
        # file is created at the start of a codex exec call.
        today = datetime.now(UTC)
        sessions_today = (
            codex_home / "sessions" / f"{today.year:04d}"
            / f"{today.month:02d}" / f"{today.day:02d}"
        )
        if sessions_today.exists():
            paths.append(sessions_today)

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
