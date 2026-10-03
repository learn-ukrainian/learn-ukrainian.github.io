"""Dispatch read-only evaluation tasks through ``scripts/delegate.py``.

Going through the delegate keeps every answer attributable: the task record
holds the launched agent and model, any substitution, and the result digest.
Tests substitute a fake that implements the same ``Dispatcher`` protocol.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from .common import Seat, sha256_text

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
TASK_FAMILIES = {"review": "ukrainian-review", "writing": "ukrainian-authoring", "judge": "ukrainian-review"}


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


class Dispatcher(Protocol):
    def known(self, task_id: str) -> bool:
        """True when a task record with this id already exists."""

    def dispatch(self, task_id: str, seat: Seat, kind: str, prompt_path: Path, *, force_new: bool) -> str | None:
        """Start the task; returns the run nonce."""

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
        cwd: Path | None = None,
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

    def _dispatch_args(self, task_id: str, seat: Seat, kind: str, prompt_path: Path) -> list[str]:
        args = ["dispatch", "--agent", seat.agent, "--model", seat.model, "--task-id", task_id]
        args += ["--prompt-file", str(prompt_path), "--mode", "read-only", "--language-lane"]
        args += ["--research-task-family", TASK_FAMILIES[kind], "--hard-timeout", str(self.hard_timeout)]
        if seat.effort:
            args += ["--effort", seat.effort]
        if self.cwd is not None:
            args += ["--cwd", str(self.cwd)]
        return args

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
        proc = self._run(*self._dispatch_args(task_id, seat, kind, prompt_path), "--dry-run", timeout=SPAWN_TIMEOUT)
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
        detail = {key: state.get(key) for key in ("cli_version", "effort", "duration_s", "returncode", "last_error")}
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
        )
