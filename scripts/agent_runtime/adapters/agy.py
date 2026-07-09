"""AgyAdapter — wraps the Antigravity (`agy`) CLI for the agent runtime.

Ported from `kubedojo/scripts/agent_runtime/adapters/agy.py` for the
2026-05-20 seminar-writer evaluation. `agy` ships Gemini Flash 3.5
("gemini-3.5-flash-high") on a separate meter from gemini-cli; the
seminar-track writer ADR at
`docs/decisions/pending/2026-05-20-seminar-track-writer-assignment.md`
adds it as candidate D pending empirical testing.

Known behavioral facts as of agy 1.0.0 (verified locally 2026-05-20):

- Headless prompt mode is ``agy -p "<prompt>"``. Stdin prompts are ignored.
- Resume/new conversation is ``--conversation=<uuid>``.
- Write-capable modes use ``--dangerously-skip-permissions``. Read-only
  hangs on interactive permission prompts; callers must force
  ``mode="danger"`` for headless dispatch (mirrors the codex protection).
- Print-mode stdout is the final answer only. Tool-call telemetry is stored
  in Antigravity's per-conversation JSONL transcript, located via a unique
  ``--log-file`` path for each invocation.
- Per-invocation model is ``--model "<Display Name>"`` where the display name
  is one of the strings printed by ``agy models`` (e.g. ``Gemini 3.1 Pro
  (High)``). The runtime slug (``gemini-3.1-pro-high``) and the display string
  normalize to the same key (see ``_normalize_model``), so callers may pass
  either; unrecognized/empty falls back to ``default_model``. ``--model``
  OVERRIDES the TUI selection (empirically verified 2026-06-05). The bare slug
  is NOT accepted by ``--model`` — agy wants the display label; mapping
  slug→label is the whole fix.
- ``agy plugin`` only exposes ``import gemini|claude``, ``install``,
  ``enable``, ``disable``. There is no plugin-marketplace browse surface,
  and ``import gemini`` is a no-op in a default install.

MCP enablement is managed by agy's global Antigravity configuration at
``~/.gemini/antigravity-cli/mcp_config.json`` using ``httpUrl``
streamable-HTTP server entries. Verified locally on 2026-06-13:
``agy -p`` invoked ``mcp__sources__verify_word`` through that global config.
The adapter still does not pass a per-invocation MCP flag because agy has
none; ``tool_config["mcp_server_names"]`` is accepted for API parity and
observability, while the global config is the source of truth.

Differences from the kubedojo source:

- ``effort: str | None = None`` parameter added on ``build_invocation``
  to match this repo's ``AgentAdapter`` protocol; treated as a no-op with
  a debug log (mirrors the Gemini adapter; follow-up #1396).
"""

from __future__ import annotations

import contextlib
import json
import logging
import os
import re
import shutil
import tempfile
import urllib.parse
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ..result import ParseResult
from ..tool_calls import summarize_tool_output
from .base import InvocationPlan

_logger = logging.getLogger(__name__)

# Defensive defaults borrowed from Gemini CLI. Agy is new enough that these
# may need adjustment once we see real Antigravity rate-limit errors.
_RATE_LIMIT_PATTERNS = (
    r"RESOURCE_EXHAUSTED",
    r"usage limit reached",
    r"quota exceeded",
    r"daily.{0,10}limit.{0,10}exceeded",
)
_RATE_LIMIT_RE = re.compile("|".join(_RATE_LIMIT_PATTERNS), re.IGNORECASE)
_AGY_LOG_ENV = "AGY_RUNTIME_LOG_FILE"
_AGY_APP_DATA_ENV = "AGY_APP_DATA_DIR"
_AGY_CONVERSATION_RE = re.compile(r"\b(?:conversation=|Created conversation\s+)(?P<id>[0-9a-fA-F-]{36})\b")
_STDOUT_MARKER_RE = re.compile(r"^\s*●\s+(?P<tool>mcp_sources_[A-Za-z0-9_]+)\((?P<args>.*)\)\s*$")
_STDOUT_RESULT_PREFIX = "⎿"
_SAVED_OUTPUT_POINTER_RE = re.compile(
    r"The output was large and was saved to:\s*"
    r"(?P<uri>file://[^\s)]+)",
    re.IGNORECASE,
)
_MAX_INLINE_TOOL_RESULT_BYTES = 1_000_000
# Delegate's default hard_timeout is 7200s. Agy's print-mode default is 5m0s,
# which is tighter than the runner guards; keep the CLI's own print wait aligned
# with the delegate default until build_invocation can receive the actual
# per-dispatch hard_timeout. TODO(#4441): plumb hard_timeout through the adapter
# ABI if a future shared contract revision carries runner guard values.
_AGY_PRINT_TIMEOUT = "120m"

# Canonical model display strings accepted by ``agy --model`` (verbatim from
# ``agy models``). A caller may pass a slug (``gemini-3.1-pro-high``) or the
# display string; ``_normalize_model`` collapses both to the same key so either
# form resolves here. Empirically (2026-06-05 probe) passing the display label
# to ``agy -p --model`` OVERRIDES the TUI selection: the log emits a benign
# ``resolver.go ... defaulting to CCPA`` line, then ``Propagating selected model
# override to backend: label="<name>"`` with the requested model. The bare slug
# is NOT accepted by ``--model`` (the real #2731 bug), so we always map to the
# display string before passing it.
_AGY_MODEL_NAMES: tuple[str, ...] = (
    "Gemini 3.5 Flash (Medium)",
    "Gemini 3.5 Flash (High)",
    "Gemini 3.5 Flash (Low)",
    "Gemini 3.1 Pro (Low)",
    "Gemini 3.1 Pro (High)",
    "Claude Sonnet 4.6 (Thinking)",
    "Claude Opus 4.6 (Thinking)",
    "GPT-OSS 120B (Medium)",
)


def _normalize_model(value: str) -> str:
    """Collapse a model identifier to its alphanumeric-lowercase form so a slug
    (``gemini-3.1-pro-high``) and the CLI display string (``Gemini 3.1 Pro
    (High)``) map to the same key."""
    return re.sub(r"[^a-z0-9]", "", value.lower())


# normalized identifier -> canonical ``agy --model`` display string
_AGY_MODEL_BY_NORMALIZED: dict[str, str] = {_normalize_model(name): name for name in _AGY_MODEL_NAMES}


class AgyAdapter:
    """Adapter for the ``agy`` Antigravity CLI."""

    name: str = "agy"
    default_model: str = os.environ.get("LEARN_UK_AGY_MODEL", "gemini-3.5-flash-high")
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
        """Build the ``agy`` print-mode invocation.

        ``model`` is mapped to ``agy --model "<Display Name>"`` via
        :func:`_resolve_model_flag` (slug or display string both accepted). This
        OVERRIDES the operator's TUI selection, making per-dispatch model choice
        deterministic. An unrecognized/empty value falls back to
        ``default_model``; if even that is unmappable the flag is omitted and agy
        uses its TUI-selected model. ``effort`` remains a no-op (#1396).

        Root cause of the #2731 saga (corrected 2026-06-05): #2731 passed the
        bare slug ``gemini-3.1-pro-high`` to ``--model``, which agy does not
        accept; the #2735 revert then misread the benign ``resolver.go ...
        defaulting to CCPA`` log line as proof the display label fails too. A
        direct probe (TUI on Pro, ``--model "Gemini 3.5 Flash (High)"``) showed
        agy propagated Flash to the backend — the label works; only the slug
        format was ever the problem.
        """
        if mode not in self.supported_modes:
            raise ValueError(f"AgyAdapter: unsupported mode {mode!r}")

        max_budget_usd = (tool_config or {}).get("max_budget_usd")
        if max_budget_usd is not None:
            _logger.warning(
                "non-claude adapter %s ignoring max_budget_usd=%s; use hard-timeout/silence-timeout instead",
                self.name,
                max_budget_usd,
            )

        if effort is not None:
            _logger.debug(
                "agy effort %r not yet wired through CLI — using TUI-selected model default (#1396 follow-up)",
                effort,
            )

        agy_bin = shutil.which("agy") or str(Path.home() / ".local/bin/agy")
        log_path = _build_log_path(task_id)
        # `--dangerously-skip-permissions` is unconditional: any tool-using
        # prompt (file read, shell call) triggers an interactive permission
        # prompt that would hang a headless dispatch waiting for human input.
        # AGY exposes only an opt-in ``--sandbox`` flag (no ``--no-sandbox``
        # counterpart), so callers that need repository reads intentionally
        # omit it. The `mode` field is retained for runtime accounting +
        # adapter-API parity; bridge calls use ``danger`` to report that
        # unsandboxed state honestly. Callers (delegate.py/dispatch_smart.py)
        # should force mode=danger for --agent agy to avoid accidental routes
        # around this.
        cmd: list[str] = [
            agy_bin,
            "-p",
            prompt,
            "--dangerously-skip-permissions",
            "--print-timeout",
            _AGY_PRINT_TIMEOUT,
            "--log-file",
            str(log_path),
        ]

        resolved_model = self._resolve_model_flag(model)
        if resolved_model:
            cmd += ["--model", resolved_model]

        if session_id:
            cmd.append(f"--conversation={session_id}")

        # ``--add-dir`` is AGY's documented way to include a directory in its
        # workspace.  A bridge invocation names the repository root via
        # ``repo_read_root`` so precise file-reading questions can be answered
        # without relying on whatever project AGY last selected interactively.
        # The root is passed EXPLICITLY (not derived from cwd) because bridge
        # asks spawn from an out-of-tree scratch cwd — the runner's worktree
        # containment guard (#4444) refuses write-capable spawns whose cwd is
        # the protected primary checkout.  Permission scope remains AGY's
        # full-trust headless mode, therefore the bridge prompt supplies the
        # no-write guard.
        if (tool_config or {}).get("bridge_repo_read"):
            add_dir = (tool_config or {}).get("repo_read_root") or str(cwd)
            cmd += ["--add-dir", str(add_dir)]

        # agy reads MCP servers from its global Antigravity config. There is
        # no per-invocation MCP CLI flag to pass here; tool_config is retained
        # for adapter API parity and resolver diagnostics.
        _ = tool_config

        return InvocationPlan(
            cmd=cmd,
            cwd=cwd,
            stdin_payload="",
            output_file=None,
            env_overrides={_AGY_LOG_ENV: str(log_path)},
            env_unsets=(),
            liveness_paths=(log_path,),
        )

    def _resolve_model_flag(self, model: str | None) -> str | None:
        """Map a runtime model slug (or display string) to the canonical
        ``agy --model`` display value.

        Tries the caller's ``model`` first, then ``default_model``, so a stale
        placeholder or an empty value degrades to the adapter default rather
        than passing an invalid flag. Returns ``None`` only when neither maps,
        leaving the flag unset so agy uses its TUI-selected model.
        """
        for candidate in (model, self.default_model):
            if candidate:
                resolved = _AGY_MODEL_BY_NORMALIZED.get(_normalize_model(candidate))
                if resolved:
                    return resolved
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
        """Parse ``agy -p`` output.

        Stdout is the canonical final response. Tool-call telemetry is parsed
        from either optional stdout markers or Antigravity's JSONL transcript.
        """
        _ = output_file
        _ = call_start_time

        stdout_response = (stdout or "").strip()
        stderr_text = (stderr or "").strip()
        combined = f"{stdout_response}\n{stderr_text}"
        hard_limit_hit = bool(_RATE_LIMIT_RE.search(combined))
        call_failed = returncode != 0 or not bool(stdout_response)
        rate_limited = hard_limit_hit and call_failed

        ok = returncode == 0 and bool(stdout_response) and not rate_limited
        response = stdout_response if ok else ""

        # `stderr_excerpt` follows the documented convention in result.py:
        # populated only when there's diagnostic stderr or the call failed.
        # The model hint is informational and lives in the JSONL audit row
        # via env_overrides, not in stderr_excerpt (which is also used as
        # an error-presence signal by some callers).
        stderr_excerpt: str | None = None
        if not ok:
            excerpt_source = stderr_text or stdout_response
            stderr_excerpt = excerpt_source[:500] or None
        elif stderr_text:
            stderr_excerpt = stderr_text[:500]

        tool_calls = _parse_transcript_tool_calls(plan)
        if not tool_calls:
            tool_calls = _parse_stdout_marker_tool_calls(combined)

        return ParseResult(
            ok=ok,
            response=response,
            stderr_excerpt=stderr_excerpt,
            rate_limited=rate_limited,
            session_id=None,
            tokens=None,
            tool_calls=tool_calls,
        )

    def liveness_signal_paths(self, plan: InvocationPlan) -> tuple[Path, ...]:
        """Agy writes a per-invocation log that advances during print mode."""
        return tuple(plan.liveness_paths)

    def cleanup_invocation(self, plan: InvocationPlan) -> None:
        """Remove the per-invocation log file after ``parse_response`` reads it."""
        raw_path = plan.env_overrides.get(_AGY_LOG_ENV)
        if not raw_path:
            return
        path = Path(raw_path)
        if not _is_temp_path(path):
            return
        with contextlib.suppress(FileNotFoundError):
            path.unlink()


def _build_log_path(task_id: str | None) -> Path:
    safe_task = re.sub(r"[^A-Za-z0-9_.-]+", "-", task_id or "call").strip("-")
    if not safe_task:
        safe_task = "call"
    return Path(tempfile.gettempdir()) / f"agy-runtime-{safe_task[:48]}-{os.getpid()}-{uuid.uuid4().hex[:12]}.log"


def _is_temp_path(path: Path) -> bool:
    try:
        return str(path).startswith(str(Path(tempfile.gettempdir())) + "/")
    except Exception:
        return str(path).startswith(("/tmp/", "/private/tmp/"))


def _parse_stdout_marker_tool_calls(text: str) -> list[dict[str, Any]]:
    """Parse optional agy ``● ...`` / ``⎿ ...`` MCP markers.

    The 2026-05-21 live print-mode probe did not expose these on stdout, but
    earlier agy captures suggested this shape may appear in other modes. Keep
    the parser narrow: only synthesize telemetry for ``mcp_sources_*`` calls.
    """
    calls: list[dict[str, Any]] = []
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        match = _STDOUT_MARKER_RE.match(lines[index])
        if not match:
            index += 1
            continue

        tool = match.group("tool")
        args = _coerce_args(match.group("args"))
        index += 1

        result_lines: list[str] = []
        while index < len(lines):
            line = lines[index]
            if _STDOUT_MARKER_RE.match(line):
                break
            if not result_lines and line.lstrip().startswith(_STDOUT_RESULT_PREFIX):
                result_lines.append(line.split(_STDOUT_RESULT_PREFIX, 1)[1].strip())
                index += 1
                continue
            if result_lines and not line.strip():
                break
            if result_lines:
                result_lines.append(line)
            index += 1

        result_text = "\n".join(result_lines).strip()
        calls.append(_build_tool_call(tool, args, result_text))
    return calls


def _parse_transcript_tool_calls(plan: InvocationPlan | None) -> list[dict[str, Any]]:
    transcript_path = _transcript_path_from_plan(plan)
    if transcript_path is None or not transcript_path.exists():
        return []

    try:
        lines = transcript_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []

    events: list[dict[str, Any]] = []
    for raw_line in lines:
        if not raw_line.strip():
            continue
        try:
            event = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            events.append(event)

    if not events:
        return []

    has_step_index = any(_event_step_index(event) is not None for event in events)
    if has_step_index:
        return _pair_transcript_by_step_index(events, transcript_path=transcript_path)
    return _pair_transcript_fifo(events, transcript_path=transcript_path)


def _event_step_index(event: Mapping[str, Any]) -> int | None:
    raw = event.get("step_index")
    if raw is None:
        return None
    if isinstance(raw, bool):
        return None
    if isinstance(raw, int):
        return raw
    if isinstance(raw, float) and raw.is_integer():
        return int(raw)
    if isinstance(raw, str) and raw.strip().isdigit():
        return int(raw.strip())
    return None


def _canonical_tool_arguments(args: Mapping[str, Any]) -> dict[str, Any]:
    canonical: dict[str, Any] = {}
    for raw_key, raw_value in args.items():
        key = str(raw_key)
        value = raw_value
        if isinstance(value, bool):
            canonical[key] = value
            continue
        if isinstance(value, float) and value.is_integer():
            value = int(value)
        if isinstance(value, int):
            canonical[key] = str(value)
            continue
        if isinstance(value, str):
            canonical[key] = value
            continue
        if isinstance(value, Mapping):
            canonical[key] = _canonical_tool_arguments(value)
            continue
        if isinstance(value, list):
            canonical[key] = [
                str(item) if isinstance(item, (int, float)) and not isinstance(item, bool) else item for item in value
            ]
            continue
        canonical[key] = value
    return canonical


def _intent_dedupe_key(call: Mapping[str, Any]) -> str:
    args = call.get("arguments")
    if not isinstance(args, Mapping):
        args = {}
    return json.dumps(
        [str(call.get("name") or ""), _canonical_tool_arguments(args)],
        sort_keys=True,
        ensure_ascii=False,
    )


def _attach_tool_result(call: dict[str, Any], result_text: str) -> dict[str, Any]:
    result = [{"type": "text", "text": result_text}]
    call["output_summary"] = summarize_tool_output(result)
    call["result"] = result
    return call


def _mcp_result_text(event: Mapping[str, Any], *, transcript_path: Path) -> str:
    result_text = _strip_agy_task_metadata(str(event.get("content") or ""))
    return _inline_saved_tool_result_pointer(
        result_text,
        transcript_path=transcript_path,
    )


def _pair_transcript_fifo(
    events: list[dict[str, Any]],
    *,
    transcript_path: Path,
) -> list[dict[str, Any]]:
    """Legacy pairing: file order FIFO between planner intents and MCP results."""
    calls: list[dict[str, Any]] = []
    pending: list[dict[str, Any]] = []
    for event in events:
        pending.extend(_extract_transcript_tool_calls(event))
        if event.get("type") != "MCP_TOOL" or not pending:
            continue
        call = pending.pop(0)
        calls.append(
            _attach_tool_result(
                call,
                _mcp_result_text(event, transcript_path=transcript_path),
            )
        )
    calls.extend(pending)
    return calls


def _result_only_call() -> dict[str, Any]:
    """Placeholder for an MCP result with no captured planner intent.

    agy occasionally executes a tool whose planner intent failed to serialize
    (``ToolName: null``, filtered by ``_extract_transcript_tool_calls``). The tool
    still ran and returned output, so we keep the result under an empty tool name:
    ``tool_call_count`` stays truthful (a real call happened) while the grounding
    gate's canonical tool comparison never credits an empty name, so no grounding is
    falsely admitted (#4761).
    """
    return {"name": "", "arguments": {}, "output_summary": "", "timestamp": ""}


def _pair_transcript_by_step_index(
    events: list[dict[str, Any]],
    *,
    transcript_path: Path,
) -> list[dict[str, Any]]:
    """Pair planner intents with MCP results in ``step_index`` (FIFO) order.

    agy re-emits still-pending planner intents on every turn, so an intent is
    deduped ONLY against calls not yet resolved by an MCP result: a re-listed
    pending intent is ignored, while an identical call issued again AFTER its result
    already landed opens a fresh pending intent (a genuine repeat). Each MCP result
    pops the oldest pending intent. A result with no pending intent is preserved as a
    result-only call so a real tool output is never dropped — the previous
    dedupe-then-zip collapsed genuine repeats and silently discarded surplus results,
    undercounting ``tool_call_count`` (#4761, Finding 3).
    """
    ordered = sorted(
        enumerate(events),
        key=lambda item: (
            _event_step_index(item[1]) if _event_step_index(item[1]) is not None else 10**9,
            item[0],
        ),
    )

    calls: list[dict[str, Any]] = []
    pending: list[dict[str, Any]] = []
    pending_keys: set[str] = set()
    orphan_results = 0
    for _, event in ordered:
        for call in _extract_transcript_tool_calls(event):
            key = _intent_dedupe_key(call)
            if key in pending_keys:
                continue
            pending.append(dict(call))
            pending_keys.add(key)
        if event.get("type") != "MCP_TOOL":
            continue
        result_text = _mcp_result_text(event, transcript_path=transcript_path)
        if pending:
            call = pending.pop(0)
            pending_keys.discard(_intent_dedupe_key(call))
            calls.append(_attach_tool_result(call, result_text))
        else:
            orphan_results += 1
            calls.append(_attach_tool_result(_result_only_call(), result_text))

    if orphan_results:
        _logger.warning(
            "agy transcript: %s MCP result(s) had no matching planner intent; preserved as result-only tool calls",
            orphan_results,
        )
    # Planner intents still pending at end (re-emitted but never producing an MCP
    # result) are omitted: they have no captured output to ground against.
    return calls


def _transcript_path_from_plan(plan: InvocationPlan | None) -> Path | None:
    if plan is None:
        return None
    log_file = plan.env_overrides.get(_AGY_LOG_ENV)
    if not log_file:
        return None
    conversation_id = _conversation_id_from_log(Path(log_file))
    if not conversation_id:
        return None
    app_data = Path(
        plan.env_overrides.get(
            _AGY_APP_DATA_ENV,
            str(Path.home() / ".gemini" / "antigravity-cli"),
        )
    )
    return app_data / "brain" / conversation_id / ".system_generated" / "logs" / "transcript.jsonl"


def _conversation_id_from_log(log_file: Path) -> str | None:
    latest: str | None = None
    try:
        with log_file.open(encoding="utf-8", errors="replace") as handle:
            for line in handle:
                match = _AGY_CONVERSATION_RE.search(line)
                if match:
                    latest = match.group("id")
    except OSError:
        return None
    return latest


def _extract_transcript_tool_calls(event: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw_calls = event.get("tool_calls")
    if not isinstance(raw_calls, list):
        return []

    calls: list[dict[str, Any]] = []
    for raw_call in raw_calls:
        if not isinstance(raw_call, Mapping):
            continue
        if raw_call.get("name") != "call_mcp_tool":
            continue
        raw_args = raw_call.get("args")
        if not isinstance(raw_args, Mapping):
            continue

        server = _decode_jsonish(raw_args.get("ServerName"))
        tool_name = _decode_jsonish(raw_args.get("ToolName"))
        if server != "sources" or not isinstance(tool_name, str) or not tool_name:
            continue

        args = _coerce_args(raw_args.get("Arguments"))
        calls.append(
            {
                "name": f"mcp__sources__{tool_name}",
                "arguments": args,
                "output_summary": "",
                "timestamp": str(event.get("created_at") or ""),
            }
        )
    return calls


def _build_tool_call(tool_name: str, args: dict[str, Any], result_text: str) -> dict[str, Any]:
    canonical_name = tool_name
    if canonical_name.startswith("mcp_sources_"):
        canonical_name = "mcp__sources__" + canonical_name.removeprefix("mcp_sources_")
    result = [{"type": "text", "text": result_text}] if result_text else None
    call: dict[str, Any] = {
        "name": canonical_name,
        "arguments": args,
        "output_summary": summarize_tool_output(result),
        "timestamp": "",
    }
    if result is not None:
        call["result"] = result
    return call


def _inline_saved_tool_result_pointer(text: str, *, transcript_path: Path) -> str:
    """Inline agy's safe ``file://.../steps/.../output.txt`` tool-result pointer."""
    match = _SAVED_OUTPUT_POINTER_RE.search(text)
    if not match:
        return text

    parsed = urllib.parse.urlparse(match.group("uri"))
    if parsed.scheme != "file" or not parsed.path:
        return text

    path = Path(urllib.parse.unquote(parsed.path))
    try:
        resolved_path = path.resolve(strict=True)
    except OSError:
        _logger.warning("agy tool result pointer missing: %s", path)
        return text

    allowed_roots = _allowed_tool_result_roots(transcript_path)
    if not any(_is_relative_to(resolved_path, root) for root in allowed_roots):
        _logger.warning("agy refused unsafe tool result pointer: %s", resolved_path)
        return text

    try:
        size = resolved_path.stat().st_size
        with resolved_path.open("rb") as handle:
            raw = handle.read(_MAX_INLINE_TOOL_RESULT_BYTES + 1)
    except OSError:
        _logger.warning("agy failed to read tool result pointer: %s", resolved_path)
        return text

    truncated = len(raw) > _MAX_INLINE_TOOL_RESULT_BYTES
    if truncated:
        raw = raw[:_MAX_INLINE_TOOL_RESULT_BYTES]
    inline = raw.decode("utf-8", errors="replace")
    if truncated:
        inline = inline.rstrip() + f"\n\n[agy tool result truncated at {_MAX_INLINE_TOOL_RESULT_BYTES} bytes]"
        _logger.warning(
            "agy inlined truncated tool result pointer %s (%s bytes)",
            resolved_path,
            size,
        )
    else:
        _logger.info(
            "agy inlined tool result pointer %s (%s bytes)",
            resolved_path,
            size,
        )
    return text[: match.start()] + inline + text[match.end() :]


def _allowed_tool_result_roots(transcript_path: Path) -> tuple[Path, ...]:
    # transcript.jsonl lives at:
    #   <app-data>/brain/<conversation>/.system_generated/logs/transcript.jsonl
    # Only follow pointers inside that conversation's steps dirs.
    conversation_root = transcript_path.parent.parent.parent
    candidates = (
        conversation_root / "steps",
        conversation_root / ".system_generated" / "steps",
    )
    roots: list[Path] = []
    for candidate in candidates:
        with contextlib.suppress(OSError):
            roots.append(candidate.resolve())
    return tuple(roots)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _coerce_args(value: Any) -> dict[str, Any]:
    decoded = _decode_jsonish(value)
    if isinstance(decoded, Mapping):
        return {str(key): nested for key, nested in decoded.items()}
    if decoded in (None, ""):
        return {}
    return {"_raw": summarize_tool_output(decoded)}


def _decode_jsonish(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    stripped = value.strip()
    if not stripped:
        return ""
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return stripped.strip('"')


def _strip_agy_task_metadata(content: str) -> str:
    lines = content.splitlines()
    if len(lines) >= 2 and lines[0].startswith("Created At:") and lines[1].startswith("Completed At:"):
        lines = lines[2:]
        if lines and not lines[0].strip():
            lines = lines[1:]
    return "\n".join(lines).strip()
