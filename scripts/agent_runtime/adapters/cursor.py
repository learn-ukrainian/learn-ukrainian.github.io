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

import json
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
    default_model: str = "auto"
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
            session_id: Session ID to resume (passed by runner or derived).
            tool_config: Config overrides. Supported keys:
                - ``cursor_workspace``: overrides the ``--workspace`` path.
                - ``approve_mcps``: bool, toggles ``--approve-mcps``.
                - ``cursor_mode``: "plan" | "ask", toggles ``--mode``.
                - ``sandbox``: "enabled" | "disabled", toggles ``--sandbox``.
            effort: Logged and ignored (no cursor equivalent today).
        """
        if effort:
            _logger.debug("cursor adapter ignoring effort=%s (not supported by CLI)", effort)

        # Resolve binary. shutil.which handles PATH lookup.
        cursor_bin = shutil.which("agent") or shutil.which("cursor-agent") or "agent"

        config = tool_config or {}

        # Workspace resolution
        workspace = config.get("cursor_workspace") or str(cwd)

        # Snapshot pre-existing transcripts to detect a new one generated during this run
        self._workspace = workspace
        self._transcripts_snapshot = self._snapshot_preexisting_transcripts(workspace)

        # Resolve session ID to resume
        resolved_session_id = session_id
        if not resolved_session_id and task_id:
            resolved_session_id = self._find_session_id_by_task_id(task_id)
            if not resolved_session_id:
                resolved_session_id = self._find_session_id_on_disk(workspace)

        # Base argv common to all paths.
        #
        # NOTE on prompt delivery: cursor-agent's `-p`/`--print` is a boolean
        # toggle for non-interactive mode; passing a literal "-" after it
        # is parsed as the POSITIONAL prompt argument (the literal "-"
        # string), NOT a stdin marker. The previous adapter shipped with
        # `"-p", "-"` and silently fed cursor the single-character prompt
        # "-" while our 14KB brief sat unread on stdin — manifest as
        # `output_chars=0` + spurious rate_limited classification when the
        # `_RATE_LIMIT_RE` regex matched a token inside cursor's empty-
        # prompt thinking trace. Pass the prompt via stdin alone (cursor
        # reads stdin in print-mode when no positional prompt is given).
        cmd: list[str] = [
            cursor_bin,
            "-p",  # Non-interactive print mode; prompt arrives via stdin.
            "--model", model or self.default_model,
            "--output-format", config.get("output_format", "stream-json"),
            "--trust",  # Headless workspace-trust bypass
        ]

        if resolved_session_id:
            cmd.extend(["--resume", resolved_session_id])

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
            # Danger mode: no --mode flag (cursor-agent default allows edits;
            # --mode plan blocks edits, --mode ask is read-only Q&A — neither
            # matches "danger" intent). Sandbox + approve-mcps kept on for
            # MCP discipline + shell-side guard; --yolo deliberately omitted
            # so shell tools still need explicit approval (matches the
            # "no --yolo in any path" Phase 2 spec §2 boundary).
            #
            # Use sparingly — most delegate calls should use workspace-write
            # (which blocks edits via --mode plan).
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

    def _encode_workspace_path(self, workspace_path: str) -> str:
        """Encode workspace path into the encoded folder name used by Cursor."""
        cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", workspace_path)
        return cleaned.strip("-")

    def _snapshot_preexisting_transcripts(self, workspace_path: str) -> set[str]:
        """Snapshot the transcript directories that exist before the run starts."""
        encoded = self._encode_workspace_path(workspace_path)
        path = Path.home() / ".cursor" / "projects" / encoded / "agent-transcripts"
        preexisting: set[str] = set()
        if path.exists():
            try:
                for entry in path.iterdir():
                    if entry.is_dir():
                        preexisting.add(entry.name)
            except OSError:
                pass
        return preexisting

    def _find_session_id_by_task_id(self, task_id: str) -> str | None:
        """Scan api_usage files for a session_id matching the given task_id."""
        repo_root = Path(__file__).resolve().parents[3]
        usage_dir = repo_root / "batch_state" / "api_usage"
        if not usage_dir.exists():
            return None

        last_session_id = None
        try:
            # Sort files so we check the most recent ones first
            for file_path in sorted(usage_dir.glob("usage_cursor-*.jsonl"), reverse=True):
                try:
                    with open(file_path, encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                record = json.loads(line)
                            except json.JSONDecodeError:
                                continue
                            if record.get("task_id") == task_id:
                                sid = record.get("session_id")
                                if sid:
                                    last_session_id = sid
                except OSError:
                    continue
        except Exception:
            pass
        return last_session_id

    def _find_session_id_on_disk(self, workspace_path: str) -> str | None:
        """Find the newest session directory on disk for this workspace."""
        encoded = self._encode_workspace_path(workspace_path)
        path = Path.home() / ".cursor" / "projects" / encoded / "agent-transcripts"
        if not path.exists():
            return None
        try:
            entries = []
            for entry in path.iterdir():
                if entry.is_dir():
                    entries.append(entry)
            if entries:
                newest = max(entries, key=lambda p: p.stat().st_mtime)
                return newest.name
        except OSError:
            pass
        return None

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

        # Detect the session ID of the current run
        session_id = None
        for event in events:
            if "sessionId" in event or "session_id" in event:
                session_id = str(event.get("sessionId") or event.get("session_id"))
                break

        # If not found in stdout events, scan the filesystem for a new transcript
        if not session_id and getattr(self, "_workspace", None):
            encoded = self._encode_workspace_path(self._workspace)
            path = Path.home() / ".cursor" / "projects" / encoded / "agent-transcripts"
            if path.exists():
                try:
                    snapshot = getattr(self, "_transcripts_snapshot", None) or set()
                    candidates = []
                    for entry in path.iterdir():
                        if entry.is_dir() and entry.name not in snapshot:
                            candidates.append(entry)
                    if candidates:
                        newest = max(candidates, key=lambda p: p.stat().st_mtime)
                        session_id = newest.name
                except OSError:
                    pass

        # If still not found, check the disk generally for the newest one
        if not session_id and getattr(self, "_workspace", None):
            session_id = self._find_session_id_on_disk(self._workspace)

        # The final response is usually the last 'content' or 'text' event
        # in the stream. parse_json_events + normalize_tool_calls handles
        # most of this, but we need to extract the assistant's final prose.
        response_parts: list[str] = []
        stream_chunks: list[str] = []

        def flush_stream_chunks() -> None:
            if stream_chunks:
                response_parts.append("".join(stream_chunks))
                stream_chunks.clear()

        def append_message_content(content: object) -> None:
            text = _extract_text_content(content)
            if not text:
                return
            flush_stream_chunks()
            response_parts.append(text)

        for event in events:
            # Typical cursor event shape: {"type": "text", "content": "..."}
            # or {"type": "message", "role": "assistant", "content": "..."}
            if event.get("type") == "text":
                stream_chunks.append(str(event.get("content", "")))
            elif event.get("type") == "message" and event.get("role") == "assistant":
                append_message_content(event.get("content", ""))
            elif event.get("role") == "assistant" and isinstance(event.get("message"), dict):
                # Cursor Agent v2026.05.27+ transcript shape:
                # {"role": "assistant", "message": {"content": [{"type": "text", ...}]}}
                append_message_content(event["message"].get("content", ""))

        flush_stream_chunks()
        response = "\n\n".join(part.strip() for part in response_parts if part.strip())

        ok = returncode == 0 and bool(response) and not rate_limited

        stderr_excerpt = None
        if not ok:
            stderr_excerpt = (stderr or stdout).strip()[:500]

        return ParseResult(
            ok=ok,
            response=response,
            stderr_excerpt=stderr_excerpt,
            rate_limited=rate_limited,
            session_id=session_id,
            tool_calls=tool_calls,
        )

    def liveness_signal_paths(self, plan: InvocationPlan) -> tuple[Path, ...]:
        """Cursor writes to stdout; no separate liveness files."""
        _ = plan
        return ()


def _extract_text_content(content: object) -> str:
    """Extract assistant prose from cursor content, ignoring tool_use blocks."""
    if isinstance(content, list):
        chunks: list[str] = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                chunks.append(str(part.get("text", "")))
        return "".join(chunks)
    if isinstance(content, str):
        return content
    return ""
