#!/usr/bin/env python3
"""Writable-path admission guard for concurrent dispatches (#5643 Δ2-A).

Local single-host ledger (`batch_state/tasks/write-ownership.sqlite3`) with
``BEGIN IMMEDIATE`` atomic reconcile → compare → reserve. Read-only modes are
exempt. WARN mode (default) admits on conflict but records would-refuse;
REFUSE mode is armed later (#5645).

Claims come from normalized ``--research-owned-path`` values but are stored
separately from the fail-open research registry.
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEDGER_PATH = _REPO_ROOT / "batch_state" / "tasks" / "write-ownership.sqlite3"
DEFAULT_TASK_STATE_DIR = _REPO_ROOT / "batch_state" / "tasks"

WRITE_CAPABLE_MODES = frozenset({"workspace-write", "danger"})
TERMINAL_TASK_STATUSES = frozenset(
    {
        "done",
        "failed",
        "timeout",
        "rate_limited",
        "cancelled",
        "crashed",
        "dry_run",
    }
)


class ClaimKind(StrEnum):
    FILE = "file"
    SUBTREE = "subtree"
    UNKNOWN = "ownership_unknown"


class GuardMode(StrEnum):
    WARN = "warn"
    REFUSE = "refuse"


@dataclass(frozen=True)
class PathClaim:
    raw: str
    kind: ClaimKind
    # Normalized repo-relative path without trailing slashes / ** for compare.
    norm: str

    def as_dict(self) -> dict[str, str]:
        return {"raw": self.raw, "kind": self.kind.value, "norm": self.norm}


@dataclass
class AdmissionResult:
    admitted: bool
    mode: GuardMode
    would_refuse: bool
    reason: str
    conflicts: list[dict[str, object]] = field(default_factory=list)
    claims: list[PathClaim] = field(default_factory=list)
    unknown_claims: list[PathClaim] = field(default_factory=list)
    override_reason: str | None = None
    skipped: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "admitted": self.admitted,
            "mode": self.mode.value,
            "would_refuse": self.would_refuse,
            "reason": self.reason,
            "conflicts": self.conflicts,
            "claims": [c.as_dict() for c in self.claims],
            "unknown_claims": [c.as_dict() for c in self.unknown_claims],
            "override_reason": self.override_reason,
            "skipped": self.skipped,
        }


def normalize_claim(raw: str) -> PathClaim:
    """Normalize a single --research-owned-path value into a claim."""
    text = (raw or "").strip().replace("\\", "/")
    if not text or text in {".", "./"}:
        return PathClaim(raw=raw, kind=ClaimKind.UNKNOWN, norm="")

    # Drop leading ./
    while text.startswith("./"):
        text = text[2:]

    # Reject absolute / parent escapes as unknown (not comparable safely).
    if text.startswith("/") or text.startswith("../") or "/../" in f"/{text}/":
        return PathClaim(raw=raw, kind=ClaimKind.UNKNOWN, norm=text)

    # Subtree forms: path/ or path/**
    if text.endswith("/**"):
        base = text[: -len("/**")].rstrip("/")
        if not base or "*" in base or "?" in base or "[" in base:
            return PathClaim(raw=raw, kind=ClaimKind.UNKNOWN, norm=text)
        return PathClaim(raw=raw, kind=ClaimKind.SUBTREE, norm=base)
    if text.endswith("/"):
        base = text.rstrip("/")
        if not base or "*" in base or "?" in base or "[" in base:
            return PathClaim(raw=raw, kind=ClaimKind.UNKNOWN, norm=text)
        return PathClaim(raw=raw, kind=ClaimKind.SUBTREE, norm=base)

    # Any other wildcard → unknown
    if any(ch in text for ch in "*?["):
        return PathClaim(raw=raw, kind=ClaimKind.UNKNOWN, norm=text)

    return PathClaim(raw=raw, kind=ClaimKind.FILE, norm=text.rstrip("/"))


def claims_conflict(a: PathClaim, b: PathClaim) -> bool:
    """Return True if two concrete claims intersect. UNKNOWN never proves overlap alone."""
    if a.kind == ClaimKind.UNKNOWN or b.kind == ClaimKind.UNKNOWN:
        return False
    if a.kind == ClaimKind.FILE and b.kind == ClaimKind.FILE:
        return a.norm == b.norm
    if a.kind == ClaimKind.FILE and b.kind == ClaimKind.SUBTREE:
        return a.norm == b.norm or a.norm.startswith(b.norm + "/")
    if a.kind == ClaimKind.SUBTREE and b.kind == ClaimKind.FILE:
        return b.norm == a.norm or b.norm.startswith(a.norm + "/")
    # subtree/subtree
    return (
        a.norm == b.norm
        or a.norm.startswith(b.norm + "/")
        or b.norm.startswith(a.norm + "/")
    )


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    else:
        return True


def _task_still_active(task_id: str, pid: int | None, state_dir: Path) -> bool:
    """True if task state is non-terminal and pid (when known) is alive."""
    state_path = state_dir / f"{task_id}.json"
    status = None
    state_pid: int | None = None
    if state_path.is_file():
        try:
            data = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
        if isinstance(data, dict):
            status = data.get("status")
            raw_pid = data.get("pid")
            if isinstance(raw_pid, int):
                state_pid = raw_pid
            elif isinstance(raw_pid, str) and raw_pid.isdigit():
                state_pid = int(raw_pid)
    if status in TERMINAL_TASK_STATUSES:
        return False
    check_pid = state_pid if state_pid is not None else pid
    if check_pid is not None and check_pid > 0 and not _pid_alive(check_pid):
        return False
    # No state file and no pid → treat as stale (cannot prove active).
    if status is None and (check_pid is None or check_pid <= 0):
        return False
    # spawning/running/needs_finalize/empty with live pid (or unknown pid) = active
    if status in ("running", "spawning", "needs_finalize", "", None):
        if check_pid is None or check_pid <= 0:
            # State says active but no pid — keep claim conservatively if status explicit.
            return status in ("running", "spawning", "needs_finalize")
        return _pid_alive(check_pid)
    return False


class OwnershipLedger:
    def __init__(
        self,
        path: Path = DEFAULT_LEDGER_PATH,
        *,
        task_state_dir: Path = DEFAULT_TASK_STATE_DIR,
        mode: GuardMode = GuardMode.WARN,
    ) -> None:
        self.path = Path(path)
        self.task_state_dir = Path(task_state_dir)
        self.mode = mode
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.path), timeout=30.0, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS write_claims (
                task_id TEXT NOT NULL,
                claim_json TEXT NOT NULL,
                pid INTEGER,
                created_at REAL NOT NULL,
                PRIMARY KEY (task_id, claim_json)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS admission_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts REAL NOT NULL,
                task_id TEXT NOT NULL,
                event TEXT NOT NULL,
                payload TEXT NOT NULL
            )
            """
        )
        return conn

    def _reconcile_stale(self, conn: sqlite3.Connection) -> list[str]:
        released: list[str] = []
        rows = conn.execute(
            "SELECT DISTINCT task_id, pid FROM write_claims"
        ).fetchall()
        for row in rows:
            task_id = str(row["task_id"])
            pid = row["pid"]
            pid_i = int(pid) if pid is not None else None
            if not _task_still_active(task_id, pid_i, self.task_state_dir):
                conn.execute("DELETE FROM write_claims WHERE task_id = ?", (task_id,))
                released.append(task_id)
        return released

    def release(self, task_id: str) -> None:
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute("DELETE FROM write_claims WHERE task_id = ?", (task_id,))
            conn.execute("COMMIT")

    def admit(
        self,
        *,
        task_id: str,
        mode: str,
        owned_paths: Sequence[str] | None,
        allow_path_overlap: str | None = None,
        pid: int | None = None,
        caller: str = "delegate.cmd_dispatch",
    ) -> AdmissionResult:
        """Attempt admission. WARN always admits; REFUSE may refuse."""
        if mode not in WRITE_CAPABLE_MODES:
            return AdmissionResult(
                admitted=True,
                mode=self.mode,
                would_refuse=False,
                reason="read-only exempt",
                skipped=True,
            )

        claims = [normalize_claim(p) for p in (owned_paths or ())]
        unknown = [c for c in claims if c.kind == ClaimKind.UNKNOWN]
        concrete = [c for c in claims if c.kind != ClaimKind.UNKNOWN]

        # Solo dispatch with no claims stays admitted (Fable note).
        if not claims:
            return AdmissionResult(
                admitted=True,
                mode=self.mode,
                would_refuse=False,
                reason="no owned-path claims; solo admit",
                claims=[],
            )

        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            self._reconcile_stale(conn)

            active_rows = conn.execute(
                "SELECT task_id, claim_json, pid FROM write_claims WHERE task_id != ?",
                (task_id,),
            ).fetchall()
            active: list[tuple[str, PathClaim, int | None]] = []
            for row in active_rows:
                try:
                    payload = json.loads(row["claim_json"])
                    claim = PathClaim(
                        raw=str(payload.get("raw", "")),
                        kind=ClaimKind(str(payload.get("kind"))),
                        norm=str(payload.get("norm", "")),
                    )
                except (json.JSONDecodeError, ValueError, TypeError, KeyError):
                    continue
                active.append(
                    (
                        str(row["task_id"]),
                        claim,
                        int(row["pid"]) if row["pid"] is not None else None,
                    )
                )

            conflicts: list[dict[str, object]] = []
            for other_task, other_claim, other_pid in active:
                for mine in concrete:
                    if claims_conflict(mine, other_claim):
                        conflicts.append(
                            {
                                "other_task_id": other_task,
                                "other_pid": other_pid,
                                "other_claim": other_claim.as_dict(),
                                "our_claim": mine.as_dict(),
                            }
                        )

            # Missing/unknown claims cannot prove disjointness against an active writer.
            unprovable = bool(active) and (not concrete or bool(unknown))
            would_refuse = bool(conflicts) or unprovable

            override = (allow_path_overlap or "").strip() or None
            if override:
                would_refuse = False  # explicit override clears refuse intent for logging

            if would_refuse and self.mode == GuardMode.REFUSE and not override:
                event = {
                    "task_id": task_id,
                    "conflicts": conflicts,
                    "unknown": [c.as_dict() for c in unknown],
                    "caller": caller,
                }
                conn.execute(
                    "INSERT INTO admission_events (ts, task_id, event, payload) VALUES (?,?,?,?)",
                    (time.time(), task_id, "refused", json.dumps(event, sort_keys=True)),
                )
                conn.execute("COMMIT")
                return AdmissionResult(
                    admitted=False,
                    mode=self.mode,
                    would_refuse=True,
                    reason="path ownership conflict (REFUSE)",
                    conflicts=conflicts,
                    claims=concrete,
                    unknown_claims=unknown,
                )

            # Admit: replace this task's claims.
            conn.execute("DELETE FROM write_claims WHERE task_id = ?", (task_id,))
            now = time.time()
            for claim in concrete:
                conn.execute(
                    "INSERT INTO write_claims (task_id, claim_json, pid, created_at) VALUES (?,?,?,?)",
                    (task_id, json.dumps(claim.as_dict(), sort_keys=True), pid, now),
                )
            # Also store UNKNOWN claims so concurrent writers can see unprovable intent.
            for claim in unknown:
                conn.execute(
                    "INSERT INTO write_claims (task_id, claim_json, pid, created_at) VALUES (?,?,?,?)",
                    (task_id, json.dumps(claim.as_dict(), sort_keys=True), pid, now),
                )

            event_name = "admitted"
            if conflicts or unprovable:
                event_name = "would_refuse_warn" if not override else "override"
            event = {
                "task_id": task_id,
                "conflicts": conflicts,
                "unknown": [c.as_dict() for c in unknown],
                "override_reason": override,
                "caller": caller,
                "mode": self.mode.value,
            }
            conn.execute(
                "INSERT INTO admission_events (ts, task_id, event, payload) VALUES (?,?,?,?)",
                (now, task_id, event_name, json.dumps(event, sort_keys=True)),
            )
            conn.execute("COMMIT")

            if conflicts or unprovable:
                reason = (
                    f"would-refuse recorded ({event_name}); admitted under {self.mode.value}"
                )
            else:
                reason = "admitted; paths disjoint"

            return AdmissionResult(
                admitted=True,
                mode=self.mode,
                would_refuse=bool(conflicts or unprovable) and not override,
                reason=reason,
                conflicts=conflicts,
                claims=concrete,
                unknown_claims=unknown,
                override_reason=override,
            )


def admit_write_paths(
    *,
    task_id: str,
    mode: str,
    owned_paths: Sequence[str] | None,
    allow_path_overlap: str | None = None,
    pid: int | None = None,
    ledger_path: Path = DEFAULT_LEDGER_PATH,
    task_state_dir: Path = DEFAULT_TASK_STATE_DIR,
    guard_mode: GuardMode | str = GuardMode.WARN,
) -> AdmissionResult:
    gm = GuardMode(guard_mode) if not isinstance(guard_mode, GuardMode) else guard_mode
    ledger = OwnershipLedger(ledger_path, task_state_dir=task_state_dir, mode=gm)
    return ledger.admit(
        task_id=task_id,
        mode=mode,
        owned_paths=owned_paths,
        allow_path_overlap=allow_path_overlap,
        pid=pid,
    )


def env_guard_mode() -> GuardMode:
    """Resolve guard mode from env (default WARN). REFUSE only after soak (#5645)."""
    raw = (os.environ.get("DELEGATE_OWNERSHIP_MODE") or "warn").strip().lower()
    if raw in {"refuse", "deny", "fail"}:
        return GuardMode.REFUSE
    return GuardMode.WARN
