"""Dispatch read-only evaluation tasks through ``scripts/delegate.py``.

Going through the delegate keeps every answer attributable: the task record
holds the launched agent and model, any substitution, and the result digest.
Tests substitute a fake that implements the same ``Dispatcher`` protocol.

Executed conditions. Only the preamble may differ between paired arms, so the
worker must receive exactly the prompt the harness rendered. The harness
renders the rules core itself and dispatches read-only with a fixed ``--cwd``,
``--rules-seat core`` and no ``--worktree``, ``--lifecycle-file`` or
``--research-*`` flags, so delegate appends no block (the pattern of
``scripts/review/seeds/adjudicate.py``). Research pointers are deliberately
not requested: they are resolved per dispatch from a changing registry and
would add context outside the hashed prompt. The task record then attests the
effective prompt hash, the appended blocks (none), cwd, mode and the hash of
the parsed dispatch arguments; ``condition_problems`` checks them.
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

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
# Of those, the ones paired arms must share (the rest are per task by construction).
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


def condition_problems(conditions: dict[str, Any], *, prompt_sha256: str, cwd: Path, args_sha256: str) -> list[str]:
    """Why the recorded conditions are not the planned ones: the worker must have received exactly the prompt."""
    problems = []
    if conditions.get("effective_prompt_sha256") != prompt_sha256:
        problems.append(
            f"worker received effective prompt {conditions.get('effective_prompt_sha256')!r}, not the rendered prompt"
        )
    if conditions.get("prompt_blocks") != []:
        problems.append(f"delegate appended prompt blocks {conditions.get('prompt_blocks')!r}")
    if conditions.get("research") is not None:
        problems.append("research context was injected")
    if conditions.get("mode") != READ_ONLY:
        problems.append(f"mode {conditions.get('mode')!r} is not {READ_ONLY!r}")
    if conditions.get("worktree_path") is not None:
        problems.append(f"worker ran in worktree {conditions.get('worktree_path')!r}")
    recorded_cwd = conditions.get("cwd")
    if not isinstance(recorded_cwd, str) or Path(recorded_cwd).resolve() != cwd.resolve():
        problems.append(f"worker cwd {recorded_cwd!r} is not the frozen {str(cwd)!r}")
    if conditions.get("dispatch_args_sha256") != args_sha256:
        problems.append("dispatch arguments differ from the ones the harness built")
    return problems


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


class DispatchError(Exception):
    """The dispatcher refused or failed to start a task."""


class Dispatcher(Protocol):
    def known(self, task_id: str) -> bool:
        """True when a task record with this id already exists."""

    def dispatch(self, task_id: str, seat: Seat, kind: str, prompt_path: Path, *, force_new: bool) -> str | None:
        """Start the task; returns the run nonce."""

    def expected_args_sha256(self, task_id: str, seat: Seat, prompt_path: Path) -> str:
        """The ``dispatch_args_sha256`` the task record must carry for the dispatch this dispatcher builds."""

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

    def _dispatch_args(self, task_id: str, seat: Seat, prompt_path: Path) -> list[str]:
        args = ["dispatch", "--agent", seat.agent, "--model", seat.model, "--task-id", task_id]
        args += ["--prompt-file", str(prompt_path), "--mode", READ_ONLY, "--language-lane"]
        args += ["--cwd", str(self.cwd), "--rules-seat", RULES_SEAT, "--hard-timeout", str(self.hard_timeout)]
        if seat.effort:
            args += ["--effort", seat.effort]
        return args

    def expected_args_sha256(self, task_id: str, seat: Seat, prompt_path: Path) -> str:
        """Hash the arguments as delegate's own parser reads them (``--force-new`` is excluded by delegate)."""
        delegate = _delegate_module(self.delegate)
        parsed = delegate.build_parser().parse_args(self._dispatch_args(task_id, seat, prompt_path))
        return delegate.dispatch_args_sha256(parsed)

    def known(self, task_id: str) -> bool:
        return self._run("status", task_id).returncode == 0

    def dispatch(self, task_id: str, seat: Seat, kind: str, prompt_path: Path, *, force_new: bool) -> str | None:
        args = self._dispatch_args(task_id, seat, prompt_path)
        if force_new:
            args.append("--force-new")
        proc = self._run(*args, timeout=SPAWN_TIMEOUT)
        if proc.returncode != 0:
            raise DispatchError(f"delegate dispatch {task_id} exited {proc.returncode}: {proc.stderr.strip()[-800:]}")
        lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
        return lines[-1] if len(lines) >= 2 else None

    def preflight(self, task_id: str, seat: Seat, kind: str, prompt_path: Path) -> None:
        proc = self._run(*self._dispatch_args(task_id, seat, prompt_path), "--dry-run", timeout=SPAWN_TIMEOUT)
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
