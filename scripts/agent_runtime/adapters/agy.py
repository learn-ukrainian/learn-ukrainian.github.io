"""AgyAdapter — wraps the Antigravity (`agy`) CLI for the agent runtime.

Ported from `kubedojo/scripts/agent_runtime/adapters/agy.py` for the
2026-05-20 seminar-writer evaluation. `agy` ships Gemini Flash
("gemini-3.8-flash-high" default; was 3.7 Flash) on a separate meter from gemini-cli; the
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
  ``--log-file`` path for each invocation (fallback: the recent brain
  conversation whose ``USER_INPUT`` opens with this invocation's prompt).
  Tool results are ``type: GENERIC`` events (agy 2026-09) or legacy
  ``MCP_TOOL`` events; both shapes are paired with planner intents.
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

MCP enablement is managed by agy's Antigravity configuration under ``$HOME``
(``~/.gemini/config/mcp_config.json``, the file ``agy mcp add`` writes; ``agy -p``
does not load ``~/.gemini/antigravity-cli/mcp_config.json``). The
CLI's HTTP field is ``serverUrl``; a Claude-format ``httpUrl`` entry is listed
by ``agy mcp list`` as a dead ``stdio`` server and ``agy -p`` then sees no
``mcp__sources__*`` tools (#7994, 2026-09-19 — this supersedes the 2026-06-13
note that ``httpUrl`` was sufficient). The adapter does not pass a
per-invocation MCP flag because agy has none; ``tool_config["mcp_server_names"]``
is accepted for API parity and observability. Writer dispatch registers and
verifies the catalog via ``tool_config.ensure_agy_mcp_catalog`` before spawning.

A receipt-recording review attempt (#8617) is the one exception to "global config
only": ``tool_config["agy_home_override"]`` points at a per-attempt scoped home
(built by ``review_mcp.prepare_review_attempt``) and the invocation's env overrides
set ``HOME`` to it and ``AGY_APP_DATA_DIR`` to ``<home>/.gemini/antigravity-cli``.
The CLI then loads the scoped ``config/mcp_config.json`` (one stdio ``sources``
server) and the transcript reader follows ``AGY_APP_DATA_DIR`` to the scoped app
data. Without the key nothing changes.

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
import time
import urllib.parse
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ..result import ParseResult
from ..tool_calls import summarize_tool_output
from ._output_schema import json_value, load_output_schema, plan_output_schema, schema_metadata, structured_result
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

# Incomplete-run detection (#8502/#8503). AGY's ``run_command`` tool caps
# ``WaitMsBeforeAsync`` at 10000 ms, so any command running longer than ten
# seconds is moved to a background task — no flag or prompt can force it into
# the foreground. Since agy 1.2.9 print mode keeps the run alive while those
# tasks finish (bounded by ``--print-timeout``) and the agent resumes when they
# complete; earlier builds waited only 5s. When the wait budget runs out, agy
# kills the tasks and still exits 0 with whatever the agent last said
# ("Waiting for task-220 to complete."). Both stderr lines below are that
# terminal signal; the benign "root agent idle; waiting up to …" line is not.
# The reason code leads ``stderr_excerpt`` so it becomes the dispatch's
# machine-readable ``last_error``; ``delegate.py`` keys on these codes to refuse
# auto-finalizing an interrupted run as ``done``.
AGY_BACKGROUND_TASK_ABANDONED = "agy_background_task_abandoned"
AGY_PRINT_TIMEOUT_PARTIAL = "agy_print_timeout_partial"
AGY_INCOMPLETE_RUN_REASONS: tuple[str, ...] = (AGY_BACKGROUND_TASK_ABANDONED, AGY_PRINT_TIMEOUT_PARTIAL)
_BACKGROUND_TERMINATED_RE = re.compile(r"terminating (?P<count>\d+) background task\(s\)")
_PRINT_TIMEOUT_PARTIAL_RE = re.compile(r"print timeout after \S+ with turn in progress")
_AGY_LOG_ENV = "AGY_RUNTIME_LOG_FILE"
_AGY_APP_DATA_ENV = "AGY_APP_DATA_DIR"
_AGY_UUID = r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}"
_AGY_CONVERSATION_RE = re.compile(
    r"(?:\bconversation=|\bcascade_id:|\b(?:Created|found|to) conversation\s+"
    r"|\bconversation update stream for\s+)(?P<id>" + _AGY_UUID + r")\b"
)
# agy 2026-09 writes every tool result (MCP or builtin) as ``type: GENERIC``;
# older builds used the dedicated ``MCP_TOOL`` type.
_LEGACY_MCP_RESULT_TYPE = "MCP_TOOL"
_GENERIC_RESULT_TYPE = "GENERIC"
_PROMPT_MATCH_CHARS = 200
_BRAIN_FALLBACK_MAX_AGE_S = 6 * 60 * 60
_STDOUT_MARKER_RE = re.compile(r"^\s*●\s+(?P<tool>mcp_sources_[A-Za-z0-9_]+)\((?P<args>.*)\)\s*$")
_STDOUT_RESULT_PREFIX = "⎿"
_SAVED_OUTPUT_POINTER_RE = re.compile(
    r"The output was large and was saved to:\s*"
    r"(?P<uri>file://[^\s)]+)",
    re.IGNORECASE,
)
_MAX_INLINE_TOOL_RESULT_BYTES = 1_000_000
# Delegate's default hard_timeout is 7200s. Keep the CLI's own print wait —
# which also bounds how long print mode waits for backgrounded commands
# (stderr: "root agent idle; waiting up to 2h0m0s …", live probe 2026-09-24,
# agy 1.2.10) — aligned with the delegate default until build_invocation can
# receive the actual per-dispatch hard_timeout. TODO(#4441): plumb hard_timeout through the adapter
# ABI if a future shared contract revision carries runner guard values.
_AGY_PRINT_TIMEOUT = "120m"

# Canonical ``agy --model`` values (verbatim from ``agy models`` as of
# 2026-09-13). Callers may pass a slug (``gemini-3.8-flash-high``) or a legacy
# display string (``Gemini 3.8 Flash (High)``); ``_normalize_model`` collapses
# both to the same key. We always emit the slug form because ``agy models``
# now lists slugs and headless ``--model <slug>`` is the proven path.
#
# Historical note: earlier AGY builds wanted display labels (#2731 slug bug).
# Live probe 2026-09-13: 3.8/3.7/3.6 Flash are listed; 3.5 is retired.
_AGY_MODEL_SLUGS: tuple[str, ...] = (
    "gemini-3.8-flash-high",
    "gemini-3.8-flash-medium",
    "gemini-3.8-flash-low",
    "gemini-3.7-flash-high",
    "gemini-3.7-flash-medium",
    "gemini-3.7-flash-low",
    "gemini-3.6-flash-high",
    "gemini-3.6-flash-medium",
    "gemini-3.6-flash-low",
    "gemini-3.1-pro-high",
    "gemini-3.1-pro-low",
    "claude-sonnet-4-6",
    "claude-opus-4-6-thinking",
    "gpt-oss-120b-medium",
)

# Legacy display labels still accepted as input (normalize → same key as slug).
_AGY_MODEL_LEGACY_LABELS: tuple[str, ...] = (
    "Gemini 3.8 Flash (High)",
    "Gemini 3.8 Flash (Medium)",
    "Gemini 3.8 Flash (Low)",
    "Gemini 3.7 Flash (High)",
    "Gemini 3.7 Flash (Medium)",
    "Gemini 3.7 Flash (Low)",
    "Gemini 3.6 Flash (High)",
    "Gemini 3.6 Flash (Medium)",
    "Gemini 3.6 Flash (Low)",
    "Gemini 3.5 Flash (High)",
    "Gemini 3.5 Flash (Medium)",
    "Gemini 3.5 Flash (Low)",
    "Gemini 3.1 Pro (High)",
    "Gemini 3.1 Pro (Low)",
    # Legacy API model names map to their supported AGY model tier.
    "gemini-3.1-pro-preview",
    "gemini-3-flash-preview",
    "gemini-3.0-flash-preview",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-2.0-flash",
    "Claude Sonnet 4.6 (Thinking)",
    "Claude Opus 4.6 (Thinking)",
    "GPT-OSS 120B (Medium)",
)


def _normalize_model(value: str) -> str:
    """Collapse a model identifier to its alphanumeric-lowercase form so a slug
    (``gemini-3.8-flash-high``) and the CLI display string (``Gemini 3.8 Flash
    (High)``) map to the same key."""
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _build_agy_model_map() -> dict[str, str]:
    """normalized key → slug passed to ``agy --model``."""
    out: dict[str, str] = {}
    for slug in _AGY_MODEL_SLUGS:
        out[_normalize_model(slug)] = slug
    # Retired 3.5 aliases preserve their tier on 3.8, including display labels.
    for tier in ("high", "medium", "low"):
        out[_normalize_model(f"gemini-3.5-flash-{tier}")] = f"gemini-3.8-flash-{tier}"
    # Legacy labels that share a normalize key with a slug resolve automatically.
    # Claude/GPT-OSS thinking labels normalize differently — map them explicitly.
    legacy_to_slug = {
        "Claude Sonnet 4.6 (Thinking)": "claude-sonnet-4-6",
        "Claude Opus 4.6 (Thinking)": "claude-opus-4-6-thinking",
        "GPT-OSS 120B (Medium)": "gpt-oss-120b-medium",
        "gemini-3.1-pro-preview": "gemini-3.1-pro-high",
        "gemini-3-flash-preview": "gemini-3.8-flash-high",
        "gemini-3.0-flash-preview": "gemini-3.8-flash-high",
        "gemini-3.6-flash": "gemini-3.6-flash-high",
        "gemini-3.7-flash": "gemini-3.7-flash-high",
        "gemini-2.0-flash": "gemini-3.8-flash-high",
    }
    for label in _AGY_MODEL_LEGACY_LABELS:
        key = _normalize_model(label)
        if key not in out:
            out[key] = legacy_to_slug.get(label, label)
    return out


# normalized identifier -> canonical ``agy --model`` slug
_AGY_MODEL_BY_NORMALIZED: dict[str, str] = _build_agy_model_map()


def unknown_model_suggestion(model: str) -> str:
    """Return safe guidance for an unknown AGY model identifier."""
    if "pro" in model.casefold():
        return "For Gemini Pro, use `--model gemini-3.1-pro-high`."
    accepted_ids = ", ".join(f"`{slug}`" for slug in _AGY_MODEL_SLUGS)
    return f"Accepted AGY model ids: {accepted_ids}."


class AgyAdapter:
    """Adapter for the ``agy`` Antigravity CLI."""

    name: str = "agy"
    default_model: str = os.environ.get("LEARN_UK_AGY_MODEL", "gemini-3.8-flash-high")
    supported_modes: frozenset[str] = frozenset({"read-only", "workspace-write", "danger"})

    @staticmethod
    def resolve_model_slug(model: str) -> str | None:
        """Return the canonical AGY model for a known slug or legacy alias."""
        return _AGY_MODEL_BY_NORMALIZED.get(_normalize_model(model))

    @staticmethod
    def model_ids_match(left: str, right: str) -> bool:
        """Compare model IDs ignoring punctuation and case."""
        return _normalize_model(left) == _normalize_model(right)

    @staticmethod
    def is_legacy_model_alias(model: str) -> bool:
        """Return whether an ID is listed as a supported legacy alias."""
        normalized = _normalize_model(model)
        return any(_normalize_model(label) == normalized for label in _AGY_MODEL_LEGACY_LABELS)

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

        tc = tool_config or {}
        review_isolation = bool(tc.get("review_isolation"))
        if review_isolation:
            raise ValueError(
                "agy_isolated_review_unsupported: AGY cannot yet prove native "
                "project-instruction, MCP, hook, and nested-reviewer suppression"
            )

        agy_bin = shutil.which("agy") or str(Path.home() / ".local/bin/agy")
        # Prefer absolute binary for isolation policy / sandbox argv0 rules.
        with contextlib.suppress(OSError):
            agy_bin = str(Path(agy_bin).resolve())
        if review_isolation and tc.get("review_write_root"):
            log_dir = Path(str(tc["review_write_root"])) / "tmp"
            log_dir.mkdir(parents=True, exist_ok=True)
            safe_task = "".join(c if c.isalnum() or c in "-_." else "_" for c in (task_id or "review"))[:48]
            log_path = log_dir / f"agy-runtime-{safe_task}-{os.getpid()}.log"
        else:
            log_path = _build_log_path(task_id)

        # Non-review: `--dangerously-skip-permissions` is unconditional so
        # headless tool use does not hang on interactive prompts.
        # Review (#5285): never skip permissions; require OS sandbox (runner)
        # plus AGY `--sandbox` when available. Fail closed if review asks for
        # skip-permissions explicitly.
        if review_isolation and tc.get("agy_skip_permissions"):
            raise ValueError(
                "AgyAdapter: review_isolation forbids agy_skip_permissions / --dangerously-skip-permissions"
            )

        cmd: list[str] = [
            agy_bin,
            "-p",
            prompt,
        ]
        if review_isolation:
            # Isolation path: no --dangerously-skip-permissions.
            if tc.get("agy_review_sandbox", True):
                cmd.append("--sandbox")
        else:
            cmd.append("--dangerously-skip-permissions")
        cmd.extend(
            [
                "--print-timeout",
                _AGY_PRINT_TIMEOUT,
                "--log-file",
                str(log_path),
            ]
        )

        resolved_model = self._resolve_model_flag(model)
        if resolved_model:
            cmd += ["--model", resolved_model]

        if session_id and not review_isolation:
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
        if tc.get("bridge_repo_read") or review_isolation:
            add_dir = tc.get("repo_read_root") or tc.get("review_snapshot_root") or str(cwd)
            cmd += ["--add-dir", str(add_dir)]

        output_schema = load_output_schema(tc)
        if output_schema is not None:
            cmd.extend(["--output-format", "json", "--json-schema", json.dumps(output_schema, separators=(",", ":"))])

        env_overrides = {_AGY_LOG_ENV: str(log_path)}
        agy_home = tc.get("agy_home_override")
        if agy_home:
            # Per-attempt scoped home (#8617): agy reads its MCP config from
            # $HOME/.gemini/config and keeps transcripts under AGY_APP_DATA_DIR.
            env_overrides["HOME"] = str(agy_home)
            env_overrides[_AGY_APP_DATA_ENV] = str(Path(agy_home) / ".gemini" / "antigravity-cli")

        return InvocationPlan(
            cmd=cmd,
            cwd=cwd,
            stdin_payload="",
            output_file=None,
            env_overrides=env_overrides,
            env_unsets=(),
            liveness_paths=(log_path,),
            metadata={
                **schema_metadata(output_schema),
                "entire_fleet": {
                    "requested_model": model or self.default_model,
                    "actual_model": resolved_model or model or self.default_model,
                }
            },
            host_harness="agy",
        )

    def _resolve_model_flag(self, model: str | None) -> str | None:
        """Map a runtime model slug (or display string) to the canonical
        ``agy --model`` slug (from ``agy models``).

        An absent model uses the configured default. An explicit unknown model
        is rejected so a request can never silently run on a different model.
        """
        if not model:
            model = self.default_model
        if not model:
            return None
        resolved = self.resolve_model_slug(model)
        if resolved:
            return resolved
        raise ValueError(
            f"Unsupported AGY model {model!r}. {unknown_model_suggestion(model)}"
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
        """Parse ``agy -p`` output.

        Stdout is the canonical final response. Tool-call telemetry is parsed
        from either optional stdout markers or Antigravity's JSONL transcript.
        """
        _ = output_file
        _ = call_start_time

        stdout_response = (stdout or "").strip()
        stderr_text = (stderr or "").strip()
        incomplete_reason = _incomplete_run_reason(stderr_text)
        if incomplete_reason is not None:
            # A reply written before agy killed the agent's own command is an
            # interim status, never a result — even when agy exits 0.
            return ParseResult(
                ok=False,
                response="",
                stderr_excerpt=f"{incomplete_reason}\n{stderr_text or stdout_response}"[:500],
                rate_limited=bool(_RATE_LIMIT_RE.search(f"{stdout_response}\n{stderr_text}")),
                tool_calls=_parse_transcript_tool_calls(plan),
            )
        output_schema = plan_output_schema(plan)
        if output_schema is not None:
            # https://antigravity.google/docs/cli/headless/ specifies the
            # terminal JSON envelope. Free-text response is never a substitute.
            envelope = json_value(stdout_response)
            envelope = envelope if isinstance(envelope, dict) else {}
            return structured_result(
                envelope.get("structured_output"), output_schema, returncode=returncode,
                terminal_ok=("structured_output" in envelope and envelope.get("status") == "SUCCESS"
                             and not envelope.get("error")),
                session_id=envelope.get("conversation_id"),
                tool_calls=_parse_transcript_tool_calls(plan),
            )
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


def _incomplete_run_reason(stderr_text: str) -> str | None:
    """Return the reason code when agy ended the run before its work finished."""
    for match in _BACKGROUND_TERMINATED_RE.finditer(stderr_text):
        if int(match.group("count")) > 0:
            return AGY_BACKGROUND_TASK_ABANDONED
    if _PRINT_TIMEOUT_PARTIAL_RE.search(stderr_text):
        return AGY_PRINT_TIMEOUT_PARTIAL
    return None


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
    if not any(event.get("type") == _LEGACY_MCP_RESULT_TYPE for event in events):
        return _pair_transcript_generic_results(events, transcript_path=transcript_path)
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


def _pair_transcript_generic_results(
    events: list[dict[str, Any]],
    *,
    transcript_path: Path,
) -> list[dict[str, Any]]:
    """Pair planner intents with ``GENERIC`` results (agy 2026-09 transcript shape).

    Current agy emits one ``GENERIC`` event per executed tool — MCP and builtin
    (``view_file``, ``run_command``…) alike — right after the planner step that
    requested it. Every planner tool call therefore holds a FIFO slot, and only
    slots that are ``sources`` MCP calls become telemetry; a builtin's result must
    never be credited to an MCP intent. Matching on ``MCP_TOOL`` alone reported
    zero calls for writers that did ground (#7994).
    """
    ordered = sorted(
        enumerate(events),
        key=lambda item: (
            _event_step_index(item[1]) if _event_step_index(item[1]) is not None else 10**9,
            item[0],
        ),
    )

    calls: list[dict[str, Any]] = []
    pending: list[tuple[str, dict[str, Any] | None]] = []
    for _, event in ordered:
        raw_calls = event.get("tool_calls")
        if isinstance(raw_calls, list):
            for raw_call in raw_calls:
                if not isinstance(raw_call, Mapping):
                    continue
                key = json.dumps(raw_call, sort_keys=True, ensure_ascii=False, default=str)
                if any(key == pending_key for pending_key, _ in pending):
                    continue  # re-emitted still-pending intent
                extracted = _extract_transcript_tool_calls({**event, "tool_calls": [raw_call]})
                pending.append((key, extracted[0] if extracted else None))
        if event.get("type") != _GENERIC_RESULT_TYPE or not pending:
            continue
        _, call = pending.pop(0)
        if call is not None:
            calls.append(
                _attach_tool_result(
                    call,
                    _mcp_result_text(event, transcript_path=transcript_path),
                )
            )
    return calls


def _transcript_path_from_plan(plan: InvocationPlan | None) -> Path | None:
    if plan is None:
        return None
    app_data = Path(
        plan.env_overrides.get(
            _AGY_APP_DATA_ENV,
            str(Path.home() / ".gemini" / "antigravity-cli"),
        )
    )
    log_file = plan.env_overrides.get(_AGY_LOG_ENV)
    conversation_id = _conversation_id_from_log(Path(log_file)) if log_file else None
    if conversation_id:
        transcript = _brain_transcript_path(app_data, conversation_id)
        if transcript.exists():
            return transcript
    fallback = _transcript_path_from_brain(plan, app_data)
    if fallback is not None:
        _logger.warning(
            "agy runtime log did not identify the conversation; matched brain transcript %s by prompt",
            fallback,
        )
        return fallback
    return _brain_transcript_path(app_data, conversation_id) if conversation_id else None


def _brain_transcript_path(app_data: Path, conversation_id: str) -> Path:
    return app_data / "brain" / conversation_id / ".system_generated" / "logs" / "transcript.jsonl"


def _prompt_from_plan(plan: InvocationPlan) -> str:
    cmd = list(plan.cmd)
    with contextlib.suppress(ValueError, IndexError):
        return str(cmd[cmd.index("-p") + 1])
    return ""


def _transcript_path_from_brain(plan: InvocationPlan, app_data: Path) -> Path | None:
    """Find this invocation's transcript when the runtime log names no conversation.

    Only a recent conversation whose first ``USER_INPUT`` opens with this
    invocation's own prompt qualifies, so an unrelated conversation is never
    credited. Identical prompts (a retry) resolve to the newest transcript, which
    is the one that just finished.
    """
    prompt_head = _prompt_from_plan(plan).strip()[:_PROMPT_MATCH_CHARS]
    if not prompt_head:
        return None
    needle = "<USER_REQUEST>\n" + prompt_head
    cutoff = time.time() - _BRAIN_FALLBACK_MAX_AGE_S
    candidates: list[tuple[float, Path]] = []
    try:
        conversation_dirs = list((app_data / "brain").iterdir())
    except OSError:
        return None
    for conversation_dir in conversation_dirs:
        transcript = _brain_transcript_path(app_data, conversation_dir.name)
        try:
            mtime = transcript.stat().st_mtime
        except OSError:
            continue
        if mtime >= cutoff:
            candidates.append((mtime, transcript))
    for _, transcript in sorted(candidates, reverse=True):
        if _transcript_opens_with(transcript, needle):
            return transcript
    return None


def _transcript_opens_with(transcript: Path, needle: str) -> bool:
    try:
        with transcript.open(encoding="utf-8", errors="replace") as handle:
            for raw_line in handle:
                if not raw_line.strip():
                    continue
                event = json.loads(raw_line)
                if isinstance(event, dict) and event.get("type") == "USER_INPUT":
                    return str(event.get("content") or "").lstrip().startswith(needle)
    except (OSError, json.JSONDecodeError):
        return False
    return False


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
