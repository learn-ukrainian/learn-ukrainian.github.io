"""Typed values shared by the TrailSpec runner ledger and executor.

The runner's persistence boundary deliberately stores JSON documents as well as
the small typed records below.  The JSON is the durable, schema-bound evidence;
these records keep state transitions explicit at the Python boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Any


class ExitClass(IntEnum):
    """Public CLI exit classes fixed by the Trail runner contract."""

    OK = 0
    STOP_PARKED = 20
    BLOCKED_PARKED = 21
    DEVIATION_REFUSED = 22
    INVALID = 23
    INDETERMINATE = 24


@dataclass(frozen=True, slots=True)
class TrailRun:
    """One pinned TrailSpec run as read from the authoritative SQLite ledger."""

    run_id: str
    trail_id: str
    trail_version: str | int
    trail_hash: str
    spec: dict[str, Any]
    seat: str
    task_family: str
    params: dict[str, Any]
    state: str
    cursor_step_id: str | None
    cursor_generation: int
    parked_stop_code: str | None
    parked_reason: str | None
    terminal_outcome: str | None
    closure_state: str
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class PreparedInvocation:
    """An invocation claimed in SQLite before any command is spawned."""

    invocation_id: str
    run_id: str
    step_id: str
    cursor_generation: int
    idempotency_key: str
    resolved_command: dict[str, Any]
    prepared_at: str


@dataclass(frozen=True, slots=True)
class CommandExecution:
    """The bounded command result consumed to create a CommandReceipt."""

    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False


@dataclass(frozen=True, slots=True)
class TrailRunResult:
    """The sole JSON-object result emitted by every trail runner command."""

    command: str
    exit_class: ExitClass
    outcome: str
    run_id: str | None = None
    state: str | None = None
    cursor_step: str | None = None
    data: dict[str, Any] | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a document conforming to trail-run-result.v1."""
        return {
            "schema_version": "trail-run-result.v1",
            "command": self.command,
            "exit_class": int(self.exit_class),
            "outcome": self.outcome,
            "run_id": self.run_id,
            "state": self.state,
            "cursor_step": self.cursor_step,
            "data": self.data or {},
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> TrailRunResult:
        """Restore a stored, already-emitted idempotent result."""
        return cls(
            command=str(payload["command"]),
            exit_class=ExitClass(int(payload["exit_class"])),
            outcome=str(payload["outcome"]),
            run_id=payload.get("run_id"),
            state=payload.get("state"),
            cursor_step=payload.get("cursor_step"),
            data=dict(payload.get("data") or {}),
            error=payload.get("error"),
        )


class TrailRunnerError(Exception):
    """A fail-closed runner error that maps to the public invalid-input class."""


class DeviationRefusedError(TrailRunnerError):
    """Raised when a request does not name the run's exact current cursor."""


class ReceiptChainError(TrailRunnerError):
    """Raised when a persisted receipt chain cannot be proven intact."""


class AuthorityReceiptUnavailableError(TrailRunnerError):
    """Raised while P4 authority verification is intentionally unavailable."""


class InjectedCrash(BaseException):
    """Test-only crash marker that intentionally bypasses normal error handling."""
