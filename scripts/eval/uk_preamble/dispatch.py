"""Dispatch read-only evaluation tasks through ``scripts/delegate.py``.

Going through the delegate keeps every answer attributable: the task record
holds the launched agent and model, any substitution, and the result digest.
Tests substitute a fake that implements the same ``Dispatcher`` protocol.

Executed conditions. Only the preamble may differ between paired arms. The
harness renders the rules core into every prompt and dispatches read-only
with a fixed ``--cwd`` and ``--rules-seat core``. The only research flag is
``--research-task-family``, taken from the task kind (review and judge:
``ukrainian-review``; writing: ``ukrainian-authoring``) for every seat. That
classifies the task, so a Ukrainian review or writing dispatch is not refused
as a bounded fallback. ``--worktree``, ``--lifecycle-file``, ``--advisory-task``
and the pointer-selecting research flags are not passed: those pointers are
resolved per dispatch from a changing registry. Delegate still wraps the
prompt: when ``--cwd`` lies in a registered worktree it adds its worktree
block (whose sparse-checkout note depends on paths the prompt names) and then
the rules core again in front of it. ``DelegateComposer`` computes that
composition with delegate's own functions, without spawning anything, so every
task has an expected effective prompt hash, prompt blocks, cwd and worktree
path. ``condition_problems`` accepts a task record only when it matches, and
refuses one whose ``research`` field is set, so a live registry that attaches
pointers because the family flag is present cannot add context to an accepted
answer. The run freezes the frame around the prompt (see ``composition_frame``)
and the argument hashes (see ``dispatch_args_frame``) and refuses a plan whose
arms would be framed differently or whose arguments differ from the freeze.
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from scripts.lib.rules_core import RulesCoreError

from .common import Seat, sha256_bytes, sha256_text

TERMINAL_STATUSES = frozenset(
    {
        "done",
        "failed",
        "timeout",
        "rate_limited",
        "cancelled",
        "crashed",
        "dry_run",
        "needs_finalize",
        "no_deliverable",
        "blocked",
    }
)
CONTROL_TIMEOUT = 120  # seconds for status calls
SPAWN_TIMEOUT = 900  # seconds for dispatch, which may create a read-only worktree
WAIT_MARGIN = 900  # seconds a wait may outlast the worker's hard timeout
RULES_SEAT = "core"
READ_ONLY = "read-only"
# Classification is a property of the task kind, not the seat. Judge compares Ukrainian writing, so it is review.
TASK_FAMILIES = {
    "review": "ukrainian-review",
    "writing": "ukrainian-authoring",
    "judge": "ukrainian-review",
}
# Task-record fields that define what the worker ran under, besides the seat and the prompt.
CONDITION_FIELDS = (
    "effective_prompt_sha256",
    "prompt_blocks",
    "dispatch_args_sha256",
    "cwd",
    "mode",
    "worktree_path",
    "research",
    "effort",
    "cli_version",
    "harness",
    "resolved_model",
    "output_schema_sha256",
)
# The parts of a composition that do not depend on the prompt: equal across a frozen plan's tasks.
FRAME_FIELDS = ("cwd", "worktree_path", "prompt_blocks", "prefix_sha256", "suffix_sha256")
# Of the condition fields, the ones paired arms must share (the rest are per task by construction).
PAIRED_FIELDS = tuple(f for f in CONDITION_FIELDS if f not in {"effective_prompt_sha256", "dispatch_args_sha256"})
# Instruction and tool-configuration files a seat reads from its working directory.
WORKSPACE_FILES = (
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    ".mcp.json",
    ".claude/settings.json",
    ".claude/settings.local.json",
    ".codex/config.toml",
    ".gemini/settings.json",
    ".cursor/mcp.json",
)


@dataclass(frozen=True)
class TaskOutcome:
    task_id: str
    status: str
    agent: str | None
    model: str | None
    substitution: Any
    response_text: str | None
    result_sha256: str | None
    run_nonce: str | None
    prompt_sha256: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)
    conditions: dict[str, Any] = field(default_factory=dict)

    def identity_problem(self, seat: Seat, prompt_sha256: str) -> str | None:
        """Why the answer cannot be attributed to ``seat`` answering exactly this prompt (None when it can)."""
        if self.prompt_sha256 != prompt_sha256:
            return f"task ran prompt {self.prompt_sha256!r}, not the planned {prompt_sha256!r}"
        if self.agent != seat.agent:
            return f"launched agent {self.agent!r} is not {seat.agent!r}"
        if self.model != seat.model:
            return f"launched model {self.model!r} is not {seat.model!r}"
        if self.substitution:
            return f"route was substituted: {self.substitution!r}"
        return None


class DispatchError(Exception):
    """The dispatcher refused or failed to start a task."""


def task_family(kind: str) -> str:
    """The ``--research-task-family`` for ``kind``. An unknown kind is refused, never dispatched unclassified."""
    try:
        return TASK_FAMILIES[kind]
    except KeyError:
        raise DispatchError(f"task kind {kind!r} has no Ukrainian task family") from None


def frame(composition: dict[str, Any]) -> dict[str, Any]:
    """The prompt-independent part of an expected composition."""
    return {key: composition.get(key) for key in FRAME_FIELDS}


def _same_path(recorded: Any, expected: str | None) -> bool:
    if expected is None or recorded is None:
        return recorded is None and expected is None
    return isinstance(recorded, str) and Path(recorded).resolve() == Path(expected).resolve()


def condition_problems(conditions: dict[str, Any], *, expected: dict[str, Any], args_sha256: str) -> list[str]:
    """Why the recorded conditions are not the expected composition of the rendered prompt (empty when they are)."""
    problems = []
    if conditions.get("effective_prompt_sha256") != expected["effective_prompt_sha256"]:
        problems.append(
            f"worker received effective prompt {conditions.get('effective_prompt_sha256')!r}, "
            "not delegate's composition of the rendered prompt"
        )
    if conditions.get("prompt_blocks") != list(expected["prompt_blocks"]):
        problems.append(
            f"delegate appended prompt blocks {conditions.get('prompt_blocks')!r}, "
            f"not the expected {list(expected['prompt_blocks'])!r}"
        )
    if conditions.get("research") is not None:
        problems.append("research context was injected")
    if conditions.get("mode") != READ_ONLY:
        problems.append(f"mode {conditions.get('mode')!r} is not {READ_ONLY!r}")
    if not _same_path(conditions.get("worktree_path"), expected["worktree_path"]):
        problems.append(
            f"worker worktree {conditions.get('worktree_path')!r} is not the expected {expected['worktree_path']!r}"
        )
    if not _same_path(conditions.get("cwd"), expected["cwd"]):
        problems.append(f"worker cwd {conditions.get('cwd')!r} is not the expected {expected['cwd']!r}")
    if conditions.get("dispatch_args_sha256") != args_sha256:
        problems.append("dispatch arguments differ from the ones the harness built")
    return problems


def composition_of(composed: str, prompt: str, *, cwd: str, worktree_path: str | None, blocks: list[str]) -> dict:
    """An expected composition: the record fields delegate would write and the frame around ``prompt``."""
    at = composed.find(prompt)
    if at < 0:
        raise DispatchError("delegate's composition does not contain the rendered prompt")
    return {
        "cwd": cwd,
        "worktree_path": worktree_path,
        "prompt_blocks": list(blocks),
        "prefix_sha256": sha256_text(composed[:at]),
        "suffix_sha256": sha256_text(composed[at + len(prompt) :]),
        "effective_prompt_sha256": sha256_text(composed),
    }


class DelegateComposer:
    """Delegate's composition of a read-only ``--cwd`` dispatch, computed in-process without spawning anything.

    Mirrors ``cmd_dispatch`` for this harness's flags: the cwd is validated and
    resolved as delegate does; a cwd inside a registered worktree gets the
    worktree block, with the sparse-checkout exclusions delegate would apply
    there (computed from ``git ls-tree`` without changing the checkout); then
    ``_compose_dispatch_prompt`` builds the final prompt. A record that departs
    from this is refused, so any drift fails closed.
    """

    def __init__(self, delegate: Any, cwd: Path, rules_seat: str = RULES_SEAT) -> None:
        validated, error = delegate._validate_caller_path("--cwd", str(cwd), resolve=delegate._resolve_cwd_path)
        if validated is None:
            raise DispatchError(error or f"--cwd {cwd} refused")
        self.delegate = delegate
        self.rules_seat = rules_seat
        self.worktree: Path | None = delegate._resolve_verified_worktree_path(validated)
        self.cwd = str(self.worktree or validated)

    def _sparse(self, prompt: str) -> dict[str, Any]:
        """The sparse-checkout telemetry delegate's worktree block reads (exclusions only; nothing applied)."""
        d, worktree = self.delegate, self.worktree
        includes = d._infer_sparse_include(None, owned_paths=None, prompt_text=prompt)
        exclude = set(d._DISPATCH_SPARSE_EXCLUDE_DEFAULT) - set(d._normalize_sparse_include(includes))
        top = d._list_worktree_top_dirs(worktree)
        data = d._list_worktree_dirs(worktree, "data/") if "data" in top else []
        registry = d._list_worktree_dirs(worktree, "registry/") if "registry" in top else []
        _, excluded = d._dispatch_sparse_cone_dirs(top, data, exclude, registry)
        return {"full_checkout": False, "excluded": excluded}

    def compose(self, prompt: str) -> dict[str, Any]:
        d = self.delegate
        blocks: list[str] = []
        try:
            composed = d._compose_dispatch_prompt(
                prompt,
                worktree_path=self.worktree,
                mode=READ_ONLY,
                sparse_telemetry=self._sparse(prompt) if self.worktree is not None else None,
                delegate_commits=False,  # only read by write modes
                research_block="",
                advisory_block="",
                advisory_block_kind=None,
                rules_seat=self.rules_seat,
                blocks=blocks,
            )
        except (OSError, RuntimeError, ValueError, RulesCoreError) as exc:
            raise DispatchError(f"cannot compute delegate's composition: {exc}") from exc
        worktree = str(self.worktree) if self.worktree is not None else None
        return composition_of(composed, prompt, cwd=self.cwd, worktree_path=worktree, blocks=blocks)


def _git(cwd: Path, *args: str) -> str | None:
    try:
        proc = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, check=False, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return proc.stdout if proc.returncode == 0 else None


def workspace_fingerprint(cwd: Path) -> dict[str, Any]:
    """The worker checkout's commit, tracked changes and instruction/tool-configuration files."""
    head = _git(cwd, "rev-parse", "HEAD")
    status = _git(cwd, "status", "--porcelain=v1", "--untracked-files=no")
    files = {}
    for rel in WORKSPACE_FILES:
        path = cwd / rel
        files[rel] = sha256_bytes(path.read_bytes()) if path.is_file() else None
    return {
        "head": head.strip() if head is not None else None,
        "tracked_changes_sha256": sha256_text(status) if status is not None else None,
        "files": files,
    }


def workspace_probe(cwd: Path) -> Callable[[], dict[str, Any]]:
    return lambda: workspace_fingerprint(cwd)


class Dispatcher(Protocol):
    def known(self, task_id: str) -> bool:
        """True when a task record with this id already exists."""

    def dispatch(self, task_id: str, seat: Seat, kind: str, prompt_path: Path, *, force_new: bool) -> str | None:
        """Start the task; returns the run nonce."""

    def expected_args_sha256(self, task_id: str, seat: Seat, kind: str, prompt_path: Path) -> str:
        """The ``dispatch_args_sha256`` the task record must carry for the dispatch this dispatcher builds."""

    def compose(self, prompt: str) -> dict[str, Any]:
        """The expected composition of ``prompt`` (see ``composition_of``); raises ``DispatchError``."""

    def preflight(self, task_id: str, seat: Seat, kind: str, prompt_path: Path) -> None:
        """Validate a dispatch without spawning a worker."""

    def wait(self, task_id: str, run_nonce: str | None) -> TaskOutcome:
        """Block until the task is terminal and return its attributed outcome."""


class DelegateDispatcher:
    """Real dispatcher: ``delegate.py dispatch`` + ``wait`` + ``status`` (read-only mode)."""

    def __init__(
        self,
        *,
        python: str,
        delegate: Path,
        cwd: Path,
        hard_timeout: int = 3600,
    ) -> None:
        self.python = python
        self.delegate = delegate
        self.cwd = cwd
        self.hard_timeout = hard_timeout
        self.wait_timeout = hard_timeout + WAIT_MARGIN
        self._composer: DelegateComposer | None = None

    def _run(self, *args: str, timeout: int = CONTROL_TIMEOUT) -> subprocess.CompletedProcess[str]:
        """Run one delegate subcommand; a timeout is a DispatchError (pending markers survive for resume)."""
        try:
            return subprocess.run(
                [self.python, str(self.delegate), *args], capture_output=True, text=True, check=False, timeout=timeout
            )
        except subprocess.TimeoutExpired as exc:
            raise DispatchError(
                f"delegate {args[0]} {args[1] if len(args) > 1 else ''} timed out after {timeout}s"
            ) from exc

    def _dispatch_args(self, task_id: str, seat: Seat, kind: str, prompt_path: Path) -> list[str]:
        args = ["dispatch", "--agent", seat.agent, "--model", seat.model, "--task-id", task_id]
        args += ["--prompt-file", str(prompt_path), "--mode", READ_ONLY, "--language-lane"]
        args += ["--cwd", str(self.cwd), "--rules-seat", RULES_SEAT, "--hard-timeout", str(self.hard_timeout)]
        args += ["--research-task-family", task_family(kind)]
        if seat.effort:
            args += ["--effort", seat.effort]
        return args

    def expected_args_sha256(self, task_id: str, seat: Seat, kind: str, prompt_path: Path) -> str:
        """Hash the arguments as delegate's own parser reads them (``--force-new`` is excluded by delegate)."""
        delegate = _delegate_module(self.delegate)
        parsed = delegate.build_parser().parse_args(self._dispatch_args(task_id, seat, kind, prompt_path))
        return delegate.dispatch_args_sha256(parsed)

    def compose(self, prompt: str) -> dict[str, Any]:
        if self._composer is None:
            self._composer = DelegateComposer(_delegate_module(self.delegate), self.cwd)
        return self._composer.compose(prompt)

    def known(self, task_id: str) -> bool:
        return self._run("status", task_id).returncode == 0

    def dispatch(self, task_id: str, seat: Seat, kind: str, prompt_path: Path, *, force_new: bool) -> str | None:
        args = self._dispatch_args(task_id, seat, kind, prompt_path)
        if force_new:
            args.append("--force-new")
        proc = self._run(*args, timeout=SPAWN_TIMEOUT)
        if proc.returncode != 0:
            raise DispatchError(f"delegate dispatch {task_id} exited {proc.returncode}: {proc.stderr.strip()[-800:]}")
        lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
        return lines[-1] if len(lines) >= 2 else None

    def preflight(self, task_id: str, seat: Seat, kind: str, prompt_path: Path) -> None:
        """Validate the dispatch with ``--dry-run``.

        A dry run leaves a terminal ``dry_run`` record, and that record does not
        store ``dispatch_args_sha256`` (delegate returns before the hash is
        written), so a later dry run cannot tell from the record that the
        arguments are the same. ``--force-new`` re-validates the current
        arguments and archives only the caller's own terminal record; delegate
        excludes it from the argument hash. A real dispatch does not pass it,
        and still refuses to reuse an existing task id.
        """
        args = [*self._dispatch_args(task_id, seat, kind, prompt_path), "--dry-run", "--force-new"]
        proc = self._run(*args, timeout=SPAWN_TIMEOUT)
        if proc.returncode != 0:
            raise DispatchError(f"delegate dry-run {task_id} exited {proc.returncode}: {proc.stderr.strip()[-800:]}")

    def _status(self, task_id: str) -> dict[str, Any]:
        proc = self._run("status", task_id)
        try:
            state = json.loads(proc.stdout)
        except ValueError as exc:
            raise DispatchError(f"delegate status {task_id}: unreadable output ({exc})") from exc
        if proc.returncode != 0 or not isinstance(state, dict) or "error" in state:
            raise DispatchError(f"delegate status {task_id}: {proc.stdout.strip()[-400:]}")
        return state

    def wait(self, task_id: str, run_nonce: str | None) -> TaskOutcome:
        args = ["wait", task_id, "--timeout", str(self.wait_timeout)]
        if run_nonce:
            args += ["--run-nonce", run_nonce]
        # The exit code reflects the task status; the record read below is authoritative.
        self._run(*args, timeout=self.wait_timeout + CONTROL_TIMEOUT)
        state = self._status(task_id)
        status = str(state.get("status") or "unknown")
        if status not in TERMINAL_STATUSES:
            raise DispatchError(f"task {task_id} is still {status!r} after wait")
        response, digest = None, state.get("result_sha256")
        result_file = state.get("result_file")
        if result_file and Path(result_file).is_file():
            response = Path(result_file).read_text(encoding="utf-8")
            if digest and sha256_text(response) != digest:
                raise DispatchError(f"task {task_id}: result file does not match its recorded digest")
        detail = {key: state.get(key) for key in ("duration_s", "returncode", "last_error")}
        return TaskOutcome(
            task_id=task_id,
            status=status,
            agent=state.get("agent"),
            model=state.get("model"),
            substitution=state.get("substitution"),
            response_text=response,
            result_sha256=digest,
            run_nonce=state.get("run_nonce"),
            prompt_sha256=state.get("prompt_sha256"),
            detail=detail,
            conditions={key: state.get(key) for key in CONDITION_FIELDS},
        )


def _delegate_module(delegate_path: Path) -> Any:
    """Import the delegate lazily on the ``sys.path`` it needs (as ``scripts/review/seeds/adjudicate.py`` does)."""
    scripts_dir = str(delegate_path.resolve().parent)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from scripts import delegate

    return delegate
