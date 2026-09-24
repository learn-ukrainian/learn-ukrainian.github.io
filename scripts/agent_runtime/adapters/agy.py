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
  ``--log-file`` path for each invocation: the conversation id that log names
  is the only binding (no fallback; see ``_transcript_path_from_plan``).
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
import dataclasses
import functools
import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
import urllib.parse
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import Any, NamedTuple

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

# Background-task handling (#8502/#8503). AGY's ``run_command`` tool caps
# ``WaitMsBeforeAsync`` at 10000 ms, so any command running longer than ten
# seconds is moved to a background task — no flag or prompt can force it into
# the foreground. agy <= 1.2.8 cancelled those tasks about 5s after the agent
# went idle and exited 0 with the agent's interim "Waiting for task-220 to
# complete." reply. agy 1.2.9 fixed that upstream (changelog: "runs now wait for
# background tasks until the --print-timeout deadline"), and the agent resumes
# when the task-finished system message arrives (live probe, agy 1.2.10,
# 2026-09-24: a 45s command finished, the agent replied with its output).
#
# The adapter therefore (1) refuses to invoke an agy older than
# ``_AGY_MIN_BACKGROUND_WAIT_VERSION`` — that build cannot finish a long command
# headlessly, so detection alone would only turn every such run into a failure
# — and (2) accepts an exit-0 run only with positive completion evidence from
# THIS invocation's slice of its conversation transcript: the events appended
# after the transcript size recorded at build time (0 for a fresh
# conversation), so a resumed conversation never credits an earlier run's
# finish or reply (#8502 r5). The guarantee is STRUCTURAL (#8502 r8): the slice
# is read in one order — file position — and every piece of work it started
# (a background command, a timer, a tool step still RUNNING, a subagent) needs
# its own finish event positioned before the final reply, which must be the
# last model event (see ``_slice_completion_gap``). A task that ends any other
# way — canceled, and by the same rule timed out or failed — never finished its
# command, so the run fails as ``AGY_BACKGROUND_TASK_CANCELED`` (#8502 r10). What the reply SAYS never
# decides the run (#8502 r9): pending-work wording in a structurally complete
# run is recorded as a warning, not a failure. Ambiguous evidence is unconfirmed
# (#8502 r7): a slice line that does not parse fails the run, it is never
# skipped. The evidence is read from the transcript bound to this invocation
# (see ``_transcript_path_from_plan``) and never from stderr alone: agy prints
# its idle-wait diagnostic only on some paths, so its absence proves nothing
# (#8502 r3). A run whose transcript cannot be bound has no evidence and fails
# as unconfirmed. Failures lead ``stderr_excerpt`` with a reason code (the
# dispatch's machine-readable ``last_error``); ``delegate.py`` keys on these
# codes to refuse auto-finalizing the run as ``done``. A passing run whose
# final reply still reads as pending leads ``stderr_excerpt`` with
# ``AGY_INTERIM_LANGUAGE_WARNING`` instead — a diagnostic, never a failure.
AGY_BACKGROUND_TASK_ABANDONED = "agy_background_task_abandoned"
AGY_BACKGROUND_TASK_UNCONFIRMED = "agy_background_task_unconfirmed"
AGY_BACKGROUND_TASK_CANCELED = "agy_background_task_canceled"
AGY_PRINT_TIMEOUT_PARTIAL = "agy_print_timeout_partial"
AGY_TRANSCRIPT_UNBOUND = "agy_transcript_unbound"
AGY_TRANSCRIPT_UNREADABLE = "agy_transcript_unreadable"
AGY_INCOMPLETE_RUN_REASONS: tuple[str, ...] = (
    AGY_BACKGROUND_TASK_ABANDONED,
    AGY_BACKGROUND_TASK_UNCONFIRMED,
    AGY_BACKGROUND_TASK_CANCELED,
    AGY_PRINT_TIMEOUT_PARTIAL,
    AGY_TRANSCRIPT_UNBOUND,
    AGY_TRANSCRIPT_UNREADABLE,
)
AGY_INTERIM_LANGUAGE_WARNING = "agy_interim_language_warning"
_AGY_MIN_BACKGROUND_WAIT_VERSION: tuple[int, int, int] = (1, 2, 9)
_AGY_VERSION_RE = re.compile(r"\b(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)\b")
_AGY_VERSION_PROBE_TIMEOUT_S = 15
_BACKGROUND_TERMINATED_RE = re.compile(r"terminating (?P<count>\d+) background task\(s\)")
_PRINT_TIMEOUT_PARTIAL_RE = re.compile(r"print timeout after \S+ with turn in progress")
_IDLE_BACKGROUND_WAIT_RE = re.compile(r"root agent idle; waiting up to \S+ for (?P<count>\d+) background task\(s\)")
# Structural transcript evidence (#8502 r8). Surveyed on every AGY transcript
# on the operator host (560 conversations; 87 with events from agy >= 1.2.9,
# 11,543 tool calls): every tool result is either DONE/ERROR/INVALID
# (synchronous) or RUNNING, and every RUNNING result either carries the
# background-task start line (748) or is an interim "Step is still running"
# event followed by a start for the same step (2). Every per-task system
# message came from a task whose start is in the same conversation. A command
# task ends with a ``Task id "<id>" <outcome> with result:`` message from
# ``sender=<id>``; the only outcomes on the host are ``finished`` (2,375, each
# with the command's exit code) and ``was canceled`` (338, "Tool execution was
# canceled"). Only ``finished`` is a finish: any other outcome — canceled, or a
# timeout or error agy may report the same way — ends the task without its
# command completing (#8502 r10). A ``schedule`` timer (``Task Description: Timer:``) ends
# when it fires, as a message from its sender carrying its prompt. A subagent
# (``invoke_subagent``) has no structured finish: its messages to the parent
# are free text, so a slice that invokes one is never confirmed.
#
# A lifecycle event is read ONLY from the header agy writes at the start of its
# own event, never from text a task produced (#8502 r11): a command's output,
# a viewed log or a grepped transcript can quote any header verbatim. On the
# host, all 3,491 per-task system messages open with agy's one-line preamble, a
# blank line, ``<SYSTEM_MESSAGE>`` and one ``[Message] timestamp=… sender=<id>
# priority=… content=`` line; everything after ``content=`` is the task's text
# and is opaque, apart from its first line, which on a task's end is exactly
# ``Task id "<sender>" <outcome> with result:`` (2,715 of 2,715). All 3,671
# background-task starts are a RUNNING tool result whose second line is the
# start line and whose third is ``Task Description:`` (``Timer:`` for the 895
# timers); the rest is the command text. A RUNNING result without that header
# stays open work (a "Step is still running" step), so a header this pattern
# misses fails the run closed instead of hiding a task.
_BACKGROUND_START_HEADER_RE = re.compile(
    r"\ACreated At: [^\n]*\nTool is running as a background task with task id: (?P<id>\S+)"
    r"(?:\nTask Description: (?P<timer>Timer:))?"
)
_TASK_MESSAGE_HEADER_RE = re.compile(
    r"\A[^\n]*\n\n<SYSTEM_MESSAGE>\n\[Message\] timestamp=\S+ sender=(?P<sender>\S+) priority=\S+ "
    r"content=(?P<first_line>[^\n]*)"
)
_TASK_ENDED_RE = re.compile(r'\ATask id "(?P<id>[^"]+)" (?P<outcome>[^\n]*?) with result:\Z')
_TASK_FINISHED_OUTCOME = "finished"
_SUBAGENT_TOOL = "invoke_subagent"
_MODEL_EVENT_TYPES = frozenset({"PLANNER_RESPONSE", "GENERIC", "MCP_TOOL"})
# DIAGNOSTIC ONLY, NEVER A GATE (#8502 r9). Natural language is unbounded, so
# no vocabulary can prove a run finished or unfinished; the structural check in
# ``_slice_completion_gap`` is the whole gate. The survey above makes it
# complete on supported builds (agy >= 1.2.9: 87 conversations, 11,543 tool
# calls): 748 of 750 RUNNING results carry the background-task start line and
# the other 2 are followed by one for the same step, and every task message came
# from a task started in the same conversation. Background work therefore
# always leaves a start event in the slice, so a reply that speaks of async or
# background work while the slice started no task describes work that is not
# running — no start event, no background work. As a rejection rule this vocabulary failed 10 of the 76
# real single-prompt runs (~13%) that passed the structural check, almost all
# finished reviews ("VERDICT: APPROVE" … "PR awaiting CI", "Spec pending")
# that then returned an empty result, with no safety gain. A match on a
# structurally complete run is therefore only recorded as
# ``AGY_INTERIM_LANGUAGE_WARNING`` (see ``_interim_language``). Each
# alternative is one way agy's models phrase pending work; every one is pinned
# by a test. Past-tense reports ("the background job finished", "I waited for
# it") do not match.
_APOSTROPHE = "['\u2019]"
_PENDING_WORK_RE = re.compile(
    "|".join(
        (
            r"^\W*wait\b",  # "Wait for task-220."
            r"\bwaiting\b",  # "I am waiting for it", "still waiting on task-2"
            rf"(?:\bwill|{_APOSTROPHE}ll|\bgoing to|\blet me|\bneed to)\s+(?:now\s+|then\s+)?wait\b",
            r"\b(?:still|currently)\s+(?:running|executing|in progress|working)\b",
            r"\b(?:is|are)\s+(?:now\s+)?(?:running|executing|in progress)\b",
            r"\b(?:launched|started|kicked off|running|spawned)\b[^.!?\n]*\bin the background\b",
            r"\b(?:once|when|until|after)\s+(?:it|they|this|that|the\s+(?:\w+\s+)?(?:command|tests?|suite|run|job|task"
            r"|build|process))\s+(?:finish(?:es)?|complete[sd]?|ends?|exits?|(?:is|are)\s+(?:done|finished|complete))\b",
            rf"\b(?:has|have|is|are)(?:n{_APOSTROPHE}t|\s+not)\s+(?:yet\s+)?(?:finished|completed|complete|done)\b",
            rf"(?:\bwill|{_APOSTROPHE}ll)\s+(?:report back|check back|follow up|let you know|update you)\b",
            r"\basynchronously\b",  # "I started pytest asynchronously" (#8502 r8)
            r"\bawaiting\b",  # "awaiting results"
            r"\bin progress\b",  # "the run is in progress"
            r"\bpending\b",  # "results pending"
        )
    ),
    re.IGNORECASE,
)
# A reply that speaks of background work although the slice recorded no task
# start (warned, not failed: see above).
_BACKGROUND_LANGUAGE_RE = re.compile(
    r"\bbackground(?:ed)?\s+(?:tasks?|jobs?|process(?:es)?|commands?|runs?)\b|\bin the background\b|\bbackgrounded\b",
    re.IGNORECASE,
)
_REPLY_TASK_REF_RE = re.compile(r"\btask-\d+\b")
# Plan metadata: this invocation's conversation and the size its transcript had
# when the invocation was built (see ``_transcript_baseline``).
_TRANSCRIPT_BASELINE_KEY = "agy_transcript_baseline"
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
        _require_background_wait_support(agy_bin)
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
        baseline = (
            {_TRANSCRIPT_BASELINE_KEY: _transcript_baseline(_agy_app_data(env_overrides), session_id)}
            if session_id and not review_isolation
            else {}
        )

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
                **baseline,
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
        language_warning: str | None = None
        if incomplete_reason is None and returncode == 0:
            # A non-zero exit already fails the run; only an apparent success
            # needs proof that the work actually finished.
            incomplete_reason, language_warning = _completion_gap(stderr_text, plan)
        if incomplete_reason is not None:
            # A reply written before the agent's own command finished is an
            # interim status, never a result — even when agy exits 0.
            return ParseResult(
                ok=False,
                response="",
                stderr_excerpt=f"{incomplete_reason}\n{stderr_text or stdout_response}"[:500],
                rate_limited=bool(_RATE_LIMIT_RE.search(f"{stdout_response}\n{stderr_text}")),
                tool_calls=_parse_transcript_tool_calls(plan)
                or _parse_stdout_marker_tool_calls(f"{stdout_response}\n{stderr_text}"),
            )
        output_schema = plan_output_schema(plan)
        if output_schema is not None:
            # https://antigravity.google/docs/cli/headless/ specifies the
            # terminal JSON envelope. Free-text response is never a substitute.
            envelope = json_value(stdout_response)
            envelope = envelope if isinstance(envelope, dict) else {}
            structured = structured_result(
                envelope.get("structured_output"), output_schema, returncode=returncode,
                terminal_ok=("structured_output" in envelope and envelope.get("status") == "SUCCESS"
                             and not envelope.get("error")),
                session_id=envelope.get("conversation_id"),
                tool_calls=_parse_transcript_tool_calls(plan),
            )
            if structured.ok and language_warning is not None:
                structured = dataclasses.replace(
                    structured, stderr_excerpt=_with_language_warning(language_warning, structured.stderr_excerpt)
                )
            return structured
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
        if ok and language_warning is not None:
            stderr_excerpt = _with_language_warning(language_warning, stderr_text)

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


def _completion_gap(stderr_text: str, plan: InvocationPlan | None) -> tuple[str | None, str | None]:
    """Return (reason code unless THIS invocation's slice proves its work finished, language warning).

    Only the events this invocation appended count (``_invocation_transcript``):
    a resumed conversation already holds earlier runs' finishes and replies,
    which prove nothing about this one (#8502 r5). Ambiguous evidence is
    unconfirmed: a slice line that does not parse may be the very finish or
    reply in question, so it fails the run as unreadable rather than being
    skipped. The readable slice is judged by ``_slice_completion_gap``; only a
    slice that passes is checked for pending-work wording (``_interim_language``),
    which is a diagnostic and never turns a pass into a failure (#8502 r9).
    """
    bound = _invocation_transcript(plan)
    if bound is None:
        return AGY_TRANSCRIPT_UNBOUND, None
    if bound.unreadable_lines:
        return AGY_TRANSCRIPT_UNREADABLE, None
    gap = _slice_completion_gap(bound.events, stderr_text)
    if gap is not None:
        return gap, None
    return None, _interim_language(bound.events)


def _slice_completion_gap(events: list[dict[str, Any]], stderr_text: str) -> str | None:
    """Return a reason code unless the slice structurally proves its work finished (#8502 r8).

    The slice is read in ONE order, its file position; ``step_index`` never
    orders anything (it only names the tool step an interim RUNNING event
    belongs to). It must hold exactly one USER_INPUT — this invocation's
    prompt; none means the run never reached the model, several mean the slice
    reaches into an earlier run. The last model event after it must be a
    PLANNER_RESPONSE with text and no tool calls: the final reply. Everything
    the run started before that reply must be closed by its own finish event,
    also positioned before it (``_open_work``); a finish written after the
    reply means the reply was written while the work still ran. A task that
    ended without finishing (canceled, timed out, failed) never completed its
    command, whatever the reply says next: ``AGY_BACKGROUND_TASK_CANCELED``
    (#8502 r10), a reason that never auto-finalizes the run. This is the
    whole gate: what the reply says is never consulted (#8502 r9). stderr
    cannot stand in for the transcript: agy's "root agent idle; waiting up to
    … for N background task(s)" line is absent on some paths, so it can only
    add doubt (agy itself waited on a task the slice never started), never
    remove it.
    """
    prompts = [position for position, event in enumerate(events) if event.get("type") == "USER_INPUT"]
    if len(prompts) != 1:
        return AGY_BACKGROUND_TASK_UNCONFIRMED
    work = events[prompts[0] + 1 :]
    model_events = [position for position, event in enumerate(work) if _is_model_event(event)]
    if not model_events or work[model_events[-1]].get("type") != "PLANNER_RESPONSE":
        return AGY_BACKGROUND_TASK_UNCONFIRMED
    final_reply = work[model_events[-1]]
    if final_reply.get("tool_calls") or not str(final_reply.get("content") or "").strip():
        return AGY_BACKGROUND_TASK_UNCONFIRMED
    started, _finished, unfinished, still_open = _open_work(work[: model_events[-1]])
    if unfinished:
        return AGY_BACKGROUND_TASK_CANCELED
    if still_open:
        return AGY_BACKGROUND_TASK_UNCONFIRMED
    idle_wait_claimed = any(int(match.group("count")) > 0 for match in _IDLE_BACKGROUND_WAIT_RE.finditer(stderr_text))
    if idle_wait_claimed and not started:
        return AGY_BACKGROUND_TASK_UNCONFIRMED
    return None


def _is_model_event(event: Mapping[str, Any]) -> bool:
    return event.get("type") in _MODEL_EVENT_TYPES or event.get("source") == "MODEL"


def _open_work(events: list[dict[str, Any]]) -> tuple[set[str], set[str], set[str], set[str]]:
    """Walk ``events`` in file order; return (tasks started, finished, ended unfinished, work still open).

    Events are read only by the header agy wrote for them (#8502 r11): a start
    only from a RUNNING result's header, a task message only from its own
    ``[Message]`` header line; a task's output quoting either is text.

    Work opens with a background-task start (a command, or a ``schedule``
    timer), any other RUNNING tool result (agy's interim "Step is still
    running"), or an ``invoke_subagent`` call. It closes only with its
    own end event: a command or timer with a ``Task id "<id>" <outcome> with
    result:`` message from ``sender=<id>`` — a finish when the outcome is
    ``finished``, otherwise (``was canceled``, a timeout, an error) an end
    without finishing; a timer also finishes with any other message from its
    sender (it fires once); an interim step with a later event of the same
    tool step. A subagent never closes — agy writes no structured subagent
    finish — and neither does an interim step that names no step.
    """
    started: set[str] = set()
    finished: set[str] = set()
    unfinished: set[str] = set()
    open_work: dict[str, str] = {}
    for position, event in enumerate(events):
        content = str(event.get("content") or "")
        if event.get("type") == "SYSTEM_MESSAGE":
            if message := _TASK_MESSAGE_HEADER_RE.match(content):
                sender = message.group("sender")
                kind = open_work.get(sender)
                ended_match = _TASK_ENDED_RE.match(message.group("first_line"))
                own_end = ended_match is not None and ended_match.group("id") == sender
                if kind == "timer" or (kind == "command" and own_end):
                    del open_work[sender]
                    finishes = not own_end or ended_match.group("outcome") == _TASK_FINISHED_OUTCOME
                    (finished if finishes else unfinished).add(sender)
            continue
        raw_calls = event.get("tool_calls")
        if isinstance(raw_calls, list) and any(
            isinstance(call, Mapping) and call.get("name") == _SUBAGENT_TOOL for call in raw_calls
        ):
            open_work[f"subagent@{position}"] = "subagent"
        step = _event_step_index(event)
        if step is not None:
            open_work.pop(f"step:{step}", None)
        if event.get("status") != "RUNNING":
            continue
        if start := _BACKGROUND_START_HEADER_RE.match(content):
            started.add(start.group("id"))
            open_work[start.group("id")] = "timer" if start.group("timer") else "command"
        else:
            open_work[f"step:{step}" if step is not None else f"step@{position}"] = "step"
    return started, finished, unfinished, set(open_work)


def _interim_language(events: list[dict[str, Any]]) -> str | None:
    """Describe pending-work wording in a structurally complete slice's final reply, if any.

    DIAGNOSTIC ONLY (#8502 r9): the caller has already accepted the slice, so
    this never fails a run. It flags a final reply that says work is still
    pending (``_PENDING_WORK_RE``), speaks of background work although the
    slice started no task, or names a task this invocation did not see finish
    (``task-2`` of an earlier run of a resumed conversation). With no start
    event there was no background work (see ``_BACKGROUND_START_HEADER_RE``), so
    such a reply is odd wording worth a look, not unfinished work.
    """
    prompt = next(position for position, event in enumerate(events) if event.get("type") == "USER_INPUT")
    work = events[prompt + 1 :]
    reply_position = max(position for position, event in enumerate(work) if _is_model_event(event))
    content = str(work[reply_position].get("content") or "")
    started, finished, _unfinished, _still_open = _open_work(work[:reply_position])
    if pending := _PENDING_WORK_RE.search(content):
        return f"pending-work wording: {pending.group(0).strip()!r}"
    if not started and (background := _BACKGROUND_LANGUAGE_RE.search(content)):
        return f"background wording with no task started: {background.group(0)!r}"
    finished_tasks = {task_id.rsplit("/", 1)[-1] for task_id in finished}
    unfinished = [ref for ref in _REPLY_TASK_REF_RE.findall(content) if ref not in finished_tasks]
    if unfinished:
        return f"names a task this run did not see finish: {unfinished[0]!r}"
    return None


def _with_language_warning(detail: str, stderr_text: str | None) -> str:
    """Lead a PASSING run's ``stderr_excerpt`` with the interim-language warning.

    The code sits alone on the first line, like the failure reason codes, so
    task records and usage rows carry it; it is not in
    ``AGY_INCOMPLETE_RUN_REASONS``, so ``delegate.py`` still settles the run.
    """
    _logger.warning("%s: %s", AGY_INTERIM_LANGUAGE_WARNING, detail)
    return "\n".join(part for part in (AGY_INTERIM_LANGUAGE_WARNING, detail, stderr_text) if part)[:500]


@functools.lru_cache(maxsize=8)
def _agy_version(agy_bin: str) -> tuple[int, int, int] | None:
    """Return the ``agy --version`` triple, or ``None`` when it cannot be read."""
    try:
        completed = subprocess.run(
            [agy_bin, "--version"],
            capture_output=True,
            text=True,
            timeout=_AGY_VERSION_PROBE_TIMEOUT_S,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    match = _AGY_VERSION_RE.search(completed.stdout or "")
    if completed.returncode != 0 or match is None:
        return None
    return (int(match.group("major")), int(match.group("minor")), int(match.group("patch")))


def _require_background_wait_support(agy_bin: str) -> None:
    """Fail closed on an agy build that cannot finish a long command headlessly.

    A missing binary is left to the spawn, which reports it as unavailable.
    """
    if not Path(agy_bin).is_file():
        return
    version = _agy_version(agy_bin)
    minimum = ".".join(map(str, _AGY_MIN_BACKGROUND_WAIT_VERSION))
    if version is None:
        raise ValueError(
            f"agy_version_unverified: `{agy_bin} --version` did not report a version; "
            f"agy >= {minimum} is required so headless runs wait for backgrounded commands (#8502)"
        )
    if version < _AGY_MIN_BACKGROUND_WAIT_VERSION:
        found = ".".join(map(str, version))
        raise ValueError(
            f"agy_version_unsupported: agy {found} at {agy_bin} cancels backgrounded commands about 5s "
            f"after the agent goes idle, so long tests never finish (#8502); run `agy update` "
            f"to reach >= {minimum}"
        )


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
    bound = _invocation_transcript(plan)
    if bound is None:
        return []
    transcript_path, events = bound.path, bound.events

    has_step_index = any(_event_step_index(event) is not None for event in events)
    if not any(event.get("type") == _LEGACY_MCP_RESULT_TYPE for event in events):
        return _pair_transcript_generic_results(events, transcript_path=transcript_path)
    if has_step_index:
        return _pair_transcript_by_step_index(events, transcript_path=transcript_path)
    return _pair_transcript_fifo(events, transcript_path=transcript_path)


class _TranscriptSlice(NamedTuple):
    path: Path
    events: list[dict[str, Any]]
    unreadable_lines: int


def _read_transcript_events(transcript_path: Path, *, offset: int = 0) -> tuple[list[dict[str, Any]], int] | None:
    """Parse the transcript's JSONL events from byte ``offset`` onward.

    Returns the events and the count of non-blank lines that are not a JSON
    object (invalid UTF-8, truncated or corrupt JSON, a bare scalar), or
    ``None`` when the file cannot be read. Callers decide what an unreadable
    line means; nothing is silently dropped.
    """
    try:
        with transcript_path.open("rb") as handle:
            handle.seek(offset)
            raw_lines = handle.read().splitlines()
    except OSError:
        return None

    events: list[dict[str, Any]] = []
    unreadable = 0
    for raw_line in raw_lines:
        if not raw_line.strip():
            continue
        try:
            event = json.loads(raw_line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            unreadable += 1
            continue
        if isinstance(event, dict):
            events.append(event)
        else:
            unreadable += 1
    return events, unreadable


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
    """Return the transcript of THIS invocation's conversation, or ``None``.

    The per-invocation runtime log is the only binding: agy truncates it on
    open and logs the conversation it created or resumed before the first
    model turn (``Created conversation <id>`` / ``found conversation <id>``;
    every log from agy 1.1.24 through 1.2.10 names one, #8502 r4). A log that
    names no conversation, or names one whose transcript is missing, binds
    nothing — matching brain/ by prompt and timestamp could credit an earlier
    run of the same prompt opened within the same second, so there is no
    fallback.
    """
    bound = _bound_conversation(plan)
    return bound[1] if bound is not None else None


def _bound_conversation(plan: InvocationPlan | None) -> tuple[str, Path] | None:
    """Return (conversation id, transcript path) the invocation's log binds."""
    if plan is None:
        return None
    log_file = plan.env_overrides.get(_AGY_LOG_ENV)
    conversation_id = _conversation_id_from_log(Path(log_file)) if log_file else None
    if not conversation_id:
        return None
    transcript = _brain_transcript_path(_agy_app_data(plan.env_overrides), conversation_id)
    return (conversation_id, transcript) if transcript.exists() else None


def _invocation_transcript(plan: InvocationPlan | None) -> _TranscriptSlice | None:
    """Return the bound transcript and only the events THIS invocation appended.

    A resumed conversation starts at the size recorded in the plan when the
    invocation was built; any other conversation the log names was not resumed
    on purpose, so it is read from the start and ``_slice_completion_gap``'s single
    USER_INPUT rule rejects it if it holds an earlier run. An unknown or no
    longer valid baseline (unreadable at build time, or a transcript shorter
    than it now) binds nothing.
    """
    bound = _bound_conversation(plan)
    if bound is None:
        return None
    conversation_id, transcript = bound
    offset: int | None = 0
    baseline = plan.metadata.get(_TRANSCRIPT_BASELINE_KEY) if plan is not None else None
    if isinstance(baseline, Mapping) and baseline.get("conversation_id") == conversation_id:
        raw_offset = baseline.get("offset")
        offset = raw_offset if isinstance(raw_offset, int) and raw_offset >= 0 else None
    if offset is None:
        return None
    try:
        if transcript.stat().st_size < offset:
            return None
    except OSError:
        return None
    parsed = _read_transcript_events(transcript, offset=offset)
    if parsed is None:
        return None
    events, unreadable = parsed
    return _TranscriptSlice(transcript, events, unreadable) if events or unreadable else None


def _transcript_baseline(app_data: Path, session_id: str) -> dict[str, Any]:
    """Record where a resumed conversation's transcript ends before this invocation.

    A fresh conversation records nothing (nothing precedes this run). An absent
    transcript is offset 0; one that cannot be sized, or a session id that is
    not a conversation UUID, records ``offset: None`` so the run binds nothing
    rather than crediting earlier events.
    """
    offset: int | None = None
    if re.fullmatch(_AGY_UUID, session_id):
        try:
            offset = _brain_transcript_path(app_data, session_id).stat().st_size
        except FileNotFoundError:
            offset = 0
        except OSError:
            offset = None
    return {"conversation_id": session_id, "offset": offset}


def _agy_app_data(env_overrides: Mapping[str, str]) -> Path:
    return Path(env_overrides.get(_AGY_APP_DATA_ENV, str(Path.home() / ".gemini" / "antigravity-cli")))


def _brain_transcript_path(app_data: Path, conversation_id: str) -> Path:
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
