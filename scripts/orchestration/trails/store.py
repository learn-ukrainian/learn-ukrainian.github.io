"""SQLite-authoritative storage for pinned TrailSpec runs.

SQLite is the source of truth.  Receipt files are immutable projections written
from committed SQLite rows and are intentionally never consulted to advance a
cursor.  Every method that claims, advances, or parks a run uses ``BEGIN
IMMEDIATE`` so two weak-driver requests cannot both claim the same step.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager, suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .models import (
    DeviationRefusedError,
    PreparedInvocation,
    ReceiptChainError,
    TrailRun,
    TrailRunnerError,
)


def utc_now() -> str:
    """Return a stable UTC RFC3339 timestamp with an explicit Z suffix."""
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def canonical_json(data: Any) -> str:
    """Serialize evidence deterministically for storage and digest comparison."""
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest_json(data: Any) -> str:
    """Hash canonical JSON evidence using the TrailSpec SHA-256 convention."""
    return hashlib.sha256(canonical_json(data).encode("utf-8")).hexdigest()


class TrailStore:
    """Own the runs database and its immutable receipt projection directory."""

    def __init__(self, database_path: Path, receipts_root: Path) -> None:
        self.database_path = database_path
        self.receipts_root = receipts_root
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database_path, isolation_level=None, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = FULL")
        return connection

    def _initialize(self) -> None:
        with closing(self._connect()) as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS trail_runs (
                    run_id TEXT PRIMARY KEY,
                    trail_id TEXT NOT NULL,
                    trail_version TEXT NOT NULL,
                    trail_hash TEXT NOT NULL,
                    pinned_spec_json TEXT NOT NULL,
                    seat TEXT NOT NULL,
                    task_family TEXT NOT NULL,
                    params_json TEXT NOT NULL,
                    state TEXT NOT NULL,
                    cursor_step_id TEXT,
                    cursor_generation INTEGER NOT NULL,
                    parked_stop_code TEXT,
                    parked_reason TEXT,
                    terminal_outcome TEXT,
                    closure_state TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS trail_invocations (
                    invocation_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL REFERENCES trail_runs(run_id),
                    step_id TEXT NOT NULL,
                    cursor_generation INTEGER NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    resolved_command_json TEXT NOT NULL,
                    resolved_command_digest TEXT NOT NULL,
                    prepared_at TEXT NOT NULL,
                    completed_at TEXT,
                    status TEXT NOT NULL,
                    command_receipt_json TEXT,
                    command_receipt_digest TEXT,
                    result_json TEXT,
                    UNIQUE(run_id, idempotency_key),
                    UNIQUE(run_id, cursor_generation)
                );

                CREATE TABLE IF NOT EXISTS trail_step_receipts (
                    invocation_id TEXT PRIMARY KEY
                        REFERENCES trail_invocations(invocation_id),
                    run_id TEXT NOT NULL REFERENCES trail_runs(run_id),
                    cursor_generation INTEGER NOT NULL,
                    receipt_json TEXT NOT NULL,
                    receipt_digest TEXT NOT NULL,
                    UNIQUE(run_id, cursor_generation)
                );

                CREATE TABLE IF NOT EXISTS trail_summons (
                    summon_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL REFERENCES trail_runs(run_id),
                    invocation_id TEXT REFERENCES trail_invocations(invocation_id),
                    stop_code TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    state TEXT NOT NULL,
                    authority_receipt_id TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS trail_authority_receipts (
                    receipt_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL REFERENCES trail_runs(run_id),
                    summon_id TEXT NOT NULL UNIQUE REFERENCES trail_summons(summon_id),
                    source_id TEXT NOT NULL,
                    issuer TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    receipt_json TEXT NOT NULL,
                    receipt_digest TEXT NOT NULL,
                    consumed_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS trail_closures (
                    run_id TEXT PRIMARY KEY REFERENCES trail_runs(run_id),
                    attestation_json TEXT NOT NULL,
                    attestation_digest TEXT NOT NULL,
                    committed_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS trail_invocations_by_run
                    ON trail_invocations(run_id, cursor_generation);
                CREATE INDEX IF NOT EXISTS trail_summons_by_run
                    ON trail_summons(run_id, created_at);
                CREATE INDEX IF NOT EXISTS trail_authority_receipts_by_run
                    ON trail_authority_receipts(run_id, consumed_at);
                """
            )

    @contextmanager
    def _immediate_transaction(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.execute("COMMIT")
        except BaseException:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()

    @staticmethod
    def _run_from_row(row: sqlite3.Row) -> TrailRun:
        spec = json.loads(row["pinned_spec_json"])
        return TrailRun(
            run_id=str(row["run_id"]),
            trail_id=str(row["trail_id"]),
            trail_version=spec["version"],
            trail_hash=str(row["trail_hash"]),
            spec=spec,
            seat=str(row["seat"]),
            task_family=str(row["task_family"]),
            params=json.loads(row["params_json"]),
            state=str(row["state"]),
            cursor_step_id=row["cursor_step_id"],
            cursor_generation=int(row["cursor_generation"]),
            parked_stop_code=row["parked_stop_code"],
            parked_reason=row["parked_reason"],
            terminal_outcome=row["terminal_outcome"],
            closure_state=str(row["closure_state"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )

    @staticmethod
    def _get_run_locked(connection: sqlite3.Connection, run_id: str) -> TrailRun:
        row = connection.execute(
            "SELECT * FROM trail_runs WHERE run_id = ?", (run_id,)
        ).fetchone()
        if row is None:
            raise TrailRunnerError(f"unknown run_id '{run_id}'")
        return TrailStore._run_from_row(row)

    def create_run(
        self,
        *,
        run_id: str,
        spec: dict[str, Any],
        trail_hash: str,
        seat: str,
        task_family: str,
        params: dict[str, Any],
        inspection_only: bool,
    ) -> TrailRun:
        """Persist one immutable pinned spec before returning a run identifier."""
        steps = spec.get("steps")
        if not isinstance(steps, list) or not steps:
            raise TrailRunnerError("validated trail has no initial step")
        now = utc_now()
        state = "inspection" if inspection_only else "active"
        cursor_step_id = None if inspection_only else steps[0]["step_id"]
        with self._immediate_transaction() as connection:
            try:
                connection.execute(
                    """
                    INSERT INTO trail_runs (
                        run_id, trail_id, trail_version, trail_hash, pinned_spec_json,
                        seat, task_family, params_json, state, cursor_step_id,
                        cursor_generation, parked_stop_code, parked_reason,
                        terminal_outcome, closure_state, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, NULL, NULL, NULL, 'open', ?, ?)
                    """,
                    (
                        run_id,
                        spec["trail_id"],
                        str(spec["version"]),
                        trail_hash,
                        canonical_json(spec),
                        seat,
                        task_family,
                        canonical_json(params),
                        state,
                        cursor_step_id,
                        now,
                        now,
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise TrailRunnerError(f"run_id '{run_id}' already exists") from exc
            return self._get_run_locked(connection, run_id)

    def get_run(self, run_id: str) -> TrailRun:
        """Read the current authoritative run state."""
        with closing(self._connect()) as connection:
            return self._get_run_locked(connection, run_id)

    def prepare_invocation(
        self,
        *,
        run_id: str,
        expected_step: str,
        idempotency_key: str,
        invocation_id: str,
        resolved_command: dict[str, Any],
    ) -> tuple[str, PreparedInvocation | dict[str, Any] | TrailRun]:
        """Claim a cursor once, writing ``prepared`` before a process can spawn.

        Returns one of ``prepared``, ``replay``, or ``indeterminate``.  A prepared
        prior claimant is deliberately parked rather than guessed to have died:
        replaying a possible remote mutation is less safe than stopping the run.
        """
        with self._immediate_transaction() as connection:
            prior = connection.execute(
                """
                SELECT invocation_id, status, result_json FROM trail_invocations
                WHERE run_id = ? AND idempotency_key = ?
                """,
                (run_id, idempotency_key),
            ).fetchone()
            if prior is not None:
                if prior["status"] == "complete" and prior["result_json"] is not None:
                    return "replay", json.loads(prior["result_json"])
                run = self._get_run_locked(connection, run_id)
                connection.execute(
                    """
                    UPDATE trail_invocations SET status = 'indeterminate'
                    WHERE invocation_id = ? AND status = 'prepared'
                    """,
                    (prior["invocation_id"],),
                )
                self._park_locked(
                    connection,
                    run=run,
                    stop_code="STOP-unknown",
                    reason=(
                        "prepared invocation has no complete command receipt; "
                        "the command is indeterminate and will not be replayed"
                    ),
                    invocation_id=None,
                    summon_state="indeterminate",
                )
                return "indeterminate", self._get_run_locked(connection, run_id)

            run = self._get_run_locked(connection, run_id)
            if run.state != "active":
                raise DeviationRefusedError(
                    f"run '{run_id}' is {run.state}; its cursor cannot be stepped"
                )
            if run.cursor_step_id != expected_step:
                raise DeviationRefusedError(
                    f"expected current step '{run.cursor_step_id}', got '{expected_step}'"
                )

            resolved_command_json = canonical_json(resolved_command)
            prepared_at = utc_now()
            try:
                connection.execute(
                    """
                    INSERT INTO trail_invocations (
                        invocation_id, run_id, step_id, cursor_generation,
                        idempotency_key, resolved_command_json, resolved_command_digest,
                        prepared_at, completed_at, status, command_receipt_json,
                        command_receipt_digest, result_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, 'prepared', NULL, NULL, NULL)
                    """,
                    (
                        invocation_id,
                        run_id,
                        expected_step,
                        run.cursor_generation,
                        idempotency_key,
                        resolved_command_json,
                        digest_json(resolved_command),
                        prepared_at,
                    ),
                )
            except sqlite3.IntegrityError:
                # A second claimant for the same generation cannot safely infer
                # whether the first process reached an external side effect.
                run = self._get_run_locked(connection, run_id)
                connection.execute(
                    """
                    UPDATE trail_invocations SET status = 'indeterminate'
                    WHERE run_id = ? AND cursor_generation = ? AND status = 'prepared'
                    """,
                    (run_id, run.cursor_generation),
                )
                self._park_locked(
                    connection,
                    run=run,
                    stop_code="STOP-unknown",
                    reason="cursor claim raced another invocation; no command will be replayed",
                    invocation_id=None,
                    summon_state="indeterminate",
                )
                return "indeterminate", self._get_run_locked(connection, run_id)
            return (
                "prepared",
                PreparedInvocation(
                    invocation_id=invocation_id,
                    run_id=run_id,
                    step_id=expected_step,
                    cursor_generation=run.cursor_generation,
                    idempotency_key=idempotency_key,
                    resolved_command=resolved_command,
                    prepared_at=prepared_at,
                ),
            )

    def park_blocked(
        self,
        *,
        run_id: str,
        expected_step: str,
        stop_code: str,
        reason: str,
        blocked_id: str,
    ) -> TrailRun:
        """Atomically park a blocked step and create its open summon record."""
        with self._immediate_transaction() as connection:
            run = self._get_run_locked(connection, run_id)
            if run.state != "active" or run.cursor_step_id != expected_step:
                raise DeviationRefusedError(
                    f"expected active current step '{expected_step}', found "
                    f"state={run.state!r} cursor={run.cursor_step_id!r}"
                )
            self._park_locked(
                connection,
                run=run,
                stop_code=stop_code,
                reason=f"blocked_on {blocked_id}: {reason}",
                invocation_id=None,
                summon_state="blocked",
            )
            return self._get_run_locked(connection, run_id)

    def park_stop(
        self,
        *,
        run_id: str,
        expected_step: str,
        stop_code: str,
        reason: str,
    ) -> TrailRun:
        """Atomically park a current cursor for a typed STOP outcome without a command."""
        with self._immediate_transaction() as connection:
            run = self._get_run_locked(connection, run_id)
            if run.state != "active" or run.cursor_step_id != expected_step:
                raise DeviationRefusedError(
                    f"expected active current step '{expected_step}', found "
                    f"state={run.state!r} cursor={run.cursor_step_id!r}"
                )
            self._park_locked(
                connection,
                run=run,
                stop_code=stop_code,
                reason=reason,
                invocation_id=None,
                summon_state="stop",
            )
            return self._get_run_locked(connection, run_id)

    def complete_invocation(
        self,
        *,
        prepared: PreparedInvocation,
        command_receipt: dict[str, Any],
        step_receipt: dict[str, Any] | None,
        result: dict[str, Any],
        next_state: str,
        next_cursor_step: str | None,
        terminal_outcome: str | None = None,
        parked_stop_code: str | None = None,
        parked_reason: str | None = None,
        summon_state: str | None = None,
    ) -> TrailRun:
        """Commit a complete receipt and its cursor/parking transition together."""
        if next_state == "parked" and (
            not parked_stop_code or not parked_reason or not summon_state
        ):
            raise TrailRunnerError("parked completion requires a stop code, reason, and summon")
        with self._immediate_transaction() as connection:
            run = self._get_run_locked(connection, prepared.run_id)
            invocation = connection.execute(
                """
                SELECT status, cursor_generation FROM trail_invocations WHERE invocation_id = ?
                """,
                (prepared.invocation_id,),
            ).fetchone()
            if invocation is None or invocation["status"] != "prepared":
                raise ReceiptChainError(
                    f"invocation '{prepared.invocation_id}' is not durably prepared"
                )
            if int(invocation["cursor_generation"]) != run.cursor_generation:
                raise ReceiptChainError(
                    f"cursor advanced while invocation '{prepared.invocation_id}' was executing"
                )
            command_receipt_json = canonical_json(command_receipt)
            step_receipt_json = canonical_json(step_receipt) if step_receipt is not None else None
            now = utc_now()
            connection.execute(
                """
                UPDATE trail_invocations
                SET completed_at = ?, status = 'complete', command_receipt_json = ?,
                    command_receipt_digest = ?, result_json = ?
                WHERE invocation_id = ?
                """,
                (
                    command_receipt["completed_at"],
                    command_receipt_json,
                    digest_json(command_receipt),
                    canonical_json(result),
                    prepared.invocation_id,
                ),
            )
            if step_receipt_json is not None:
                connection.execute(
                    """
                    INSERT INTO trail_step_receipts (
                        invocation_id, run_id, cursor_generation, receipt_json, receipt_digest
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        prepared.invocation_id,
                        prepared.run_id,
                        prepared.cursor_generation,
                        step_receipt_json,
                        digest_json(step_receipt),
                    ),
                )

            if next_state == "parked":
                self._park_locked(
                    connection,
                    run=run,
                    stop_code=str(parked_stop_code),
                    reason=str(parked_reason),
                    invocation_id=prepared.invocation_id,
                    summon_state=str(summon_state),
                    updated_at=now,
                )
            else:
                connection.execute(
                    """
                    UPDATE trail_runs
                    SET state = ?, cursor_step_id = ?, cursor_generation = ?,
                        parked_stop_code = NULL, parked_reason = NULL,
                        terminal_outcome = ?, updated_at = ?
                    WHERE run_id = ?
                    """,
                    (
                        next_state,
                        next_cursor_step,
                        run.cursor_generation + 1,
                        terminal_outcome,
                        now,
                        prepared.run_id,
                    ),
                )
            return self._get_run_locked(connection, prepared.run_id)

    def _park_locked(
        self,
        connection: sqlite3.Connection,
        *,
        run: TrailRun,
        stop_code: str,
        reason: str,
        invocation_id: str | None,
        summon_state: str,
        updated_at: str | None = None,
    ) -> None:
        """Update state and insert a summon inside the caller's SQLite transaction."""
        now = updated_at or utc_now()
        connection.execute(
            """
            UPDATE trail_runs
            SET state = 'parked', parked_stop_code = ?, parked_reason = ?, updated_at = ?
            WHERE run_id = ?
            """,
            (stop_code, reason, now, run.run_id),
        )
        summon_id = digest_json(
            {
                "run_id": run.run_id,
                "cursor_generation": run.cursor_generation,
                "stop_code": stop_code,
                "reason": reason,
                "invocation_id": invocation_id,
            }
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO trail_summons (
                summon_id, run_id, invocation_id, stop_code, reason, state,
                authority_receipt_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, NULL, ?)
            """,
            (summon_id, run.run_id, invocation_id, stop_code, reason, summon_state, now),
        )

    def list_invocations(self, run_id: str) -> list[dict[str, Any]]:
        """Return ordered invocation rows with JSON evidence decoded for verification."""
        with closing(self._connect()) as connection:
            self._get_run_locked(connection, run_id)
            rows = connection.execute(
                """
                SELECT * FROM trail_invocations WHERE run_id = ?
                ORDER BY cursor_generation ASC
                """,
                (run_id,),
            ).fetchall()
        return [
            {
                "invocation_id": str(row["invocation_id"]),
                "step_id": str(row["step_id"]),
                "cursor_generation": int(row["cursor_generation"]),
                "idempotency_key": str(row["idempotency_key"]),
                "resolved_command": json.loads(row["resolved_command_json"]),
                "resolved_command_digest": str(row["resolved_command_digest"]),
                "prepared_at": str(row["prepared_at"]),
                "completed_at": row["completed_at"],
                "status": str(row["status"]),
                "command_receipt": (
                    json.loads(row["command_receipt_json"])
                    if row["command_receipt_json"] is not None
                    else None
                ),
                "command_receipt_digest": row["command_receipt_digest"],
                "result": json.loads(row["result_json"]) if row["result_json"] else None,
            }
            for row in rows
        ]

    def get_step_receipt(self, invocation_id: str) -> dict[str, Any] | None:
        """Return the immutable StepReceipt linked to an invocation, if it exists."""
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT receipt_json FROM trail_step_receipts WHERE invocation_id = ?",
                (invocation_id,),
            ).fetchone()
        return json.loads(row["receipt_json"]) if row is not None else None

    def list_summons(self, run_id: str) -> list[dict[str, Any]]:
        """Return summon records for status and test-only atomicity inspection."""
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT summon_id, invocation_id, stop_code, reason, state, authority_receipt_id,
                       created_at
                FROM trail_summons WHERE run_id = ? ORDER BY created_at ASC
                """,
                (run_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def record_authority_receipt(
        self,
        *,
        run_id: str,
        receipt: dict[str, Any],
        source_id: str,
    ) -> dict[str, Any]:
        """Consume one externally re-fetched receipt exactly once without inventing a transition.

        P1/P3 deliberately have no resume-transition/override field.  This method
        records the verified authority in the same transaction that consumes its
        precise summon, but leaves the run parked until a later approved trail
        contract supplies an executable transition.
        """
        receipt_id = receipt.get("receipt_id")
        summon_id = receipt.get("summon_id")
        if not isinstance(receipt_id, str) or not isinstance(summon_id, str):
            raise TrailRunnerError("verified authority receipt lacks receipt_id or summon_id")
        with self._immediate_transaction() as connection:
            run = self._get_run_locked(connection, run_id)
            if run.state != "parked":
                raise DeviationRefusedError("authority receipt can only bind a currently parked run")
            expected = {
                "run_id": run.run_id,
                "trail_id": run.trail_id,
                "trail_version": run.trail_version,
                "trail_hash": run.trail_hash,
                "step_id": run.cursor_step_id,
                "cursor_generation": run.cursor_generation,
            }
            for field, value in expected.items():
                if receipt.get(field) != value:
                    raise DeviationRefusedError(
                        f"authority receipt {field} no longer binds the parked run"
                    )
            summon = connection.execute(
                """
                SELECT stop_code, authority_receipt_id FROM trail_summons
                WHERE summon_id = ? AND run_id = ?
                """,
                (summon_id, run_id),
            ).fetchone()
            if summon is None:
                raise DeviationRefusedError("authority receipt does not name a summon for this run")
            if summon["authority_receipt_id"] is not None:
                raise DeviationRefusedError("summon already has a consumed authority receipt")
            if summon["stop_code"] != receipt.get("stop_code"):
                raise DeviationRefusedError("authority receipt STOP code differs from summon")
            now = utc_now()
            try:
                connection.execute(
                    """
                    INSERT INTO trail_authority_receipts (
                        receipt_id, run_id, summon_id, source_id, issuer, expires_at,
                        receipt_json, receipt_digest, consumed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        receipt_id,
                        run_id,
                        summon_id,
                        source_id,
                        receipt["issuer"],
                        receipt["expires_at"],
                        canonical_json(receipt),
                        digest_json(receipt),
                        now,
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise DeviationRefusedError("authority receipt has already been consumed") from exc
            updated = connection.execute(
                """
                UPDATE trail_summons
                SET authority_receipt_id = ?, state = 'authority-verified'
                WHERE summon_id = ? AND run_id = ? AND authority_receipt_id IS NULL
                """,
                (receipt_id, summon_id, run_id),
            )
            if updated.rowcount != 1:
                raise ReceiptChainError("authority receipt summon consumption raced another writer")
            return {
                "receipt_id": receipt_id,
                "summon_id": summon_id,
                "receipt_digest": digest_json(receipt),
                "source_id": source_id,
            }

    def list_authority_receipts(self, run_id: str) -> list[dict[str, Any]]:
        """Return durably consumed authority evidence for closure re-observation."""
        with closing(self._connect()) as connection:
            self._get_run_locked(connection, run_id)
            rows = connection.execute(
                """
                SELECT receipt_id, summon_id, source_id, issuer, expires_at, receipt_json,
                       receipt_digest, consumed_at
                FROM trail_authority_receipts WHERE run_id = ? ORDER BY consumed_at ASC
                """,
                (run_id,),
            ).fetchall()
        return [
            {
                **dict(row),
                "receipt": json.loads(str(row["receipt_json"])),
            }
            for row in rows
        ]

    def get_closure(self, run_id: str) -> dict[str, Any] | None:
        """Return the one immutable closure attestation, if terminal commit occurred."""
        with closing(self._connect()) as connection:
            self._get_run_locked(connection, run_id)
            row = connection.execute(
                "SELECT attestation_json, attestation_digest, committed_at FROM trail_closures WHERE run_id = ?",
                (run_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "attestation": json.loads(str(row["attestation_json"])),
            "attestation_digest": str(row["attestation_digest"]),
            "committed_at": str(row["committed_at"]),
        }

    def commit_closure(self, *, run_id: str, attestation: dict[str, Any]) -> dict[str, Any]:
        """Terminally commit exactly one immutable closure attestation or replay it."""
        digest = digest_json(attestation)
        with self._immediate_transaction() as connection:
            run = self._get_run_locked(connection, run_id)
            existing = connection.execute(
                "SELECT attestation_json, attestation_digest, committed_at FROM trail_closures WHERE run_id = ?",
                (run_id,),
            ).fetchone()
            if existing is not None:
                # A second closer can independently re-observe the same terminal
                # state a few microseconds later. The first committed immutable
                # attestation is authoritative; returning it prevents a timestamp
                # difference from turning an idempotent terminal replay into a
                # competing closure claim.
                return {
                    "attestation": json.loads(str(existing["attestation_json"])),
                    "attestation_digest": str(existing["attestation_digest"]),
                    "committed_at": str(existing["committed_at"]),
                }
            if run.state != "terminal" or not run.terminal_outcome:
                raise DeviationRefusedError("only a terminal run can commit closure")
            now = utc_now()
            connection.execute(
                """
                INSERT INTO trail_closures (run_id, attestation_json, attestation_digest, committed_at)
                VALUES (?, ?, ?, ?)
                """,
                (run_id, canonical_json(attestation), digest, now),
            )
            connection.execute(
                "UPDATE trail_runs SET closure_state = 'closed', updated_at = ? WHERE run_id = ?",
                (now, run_id),
            )
            return {
                "attestation": attestation,
                "attestation_digest": digest,
                "committed_at": now,
            }

    def park_terminal_closure(self, *, run_id: str, reason: str) -> TrailRun:
        """Atomically park closure while preserving the terminal command chain."""
        with self._immediate_transaction() as connection:
            run = self._get_run_locked(connection, run_id)
            if run.state != "terminal":
                raise DeviationRefusedError("only terminal runs can park closure")
            if run.closure_state == "closed":
                raise DeviationRefusedError("closed run cannot be re-parked for closure")
            now = utc_now()
            summon_id = digest_json(
                {
                    "kind": "closure",
                    "run_id": run_id,
                    "cursor_generation": run.cursor_generation,
                    "reason": reason,
                }
            )
            connection.execute(
                """
                INSERT OR IGNORE INTO trail_summons (
                    summon_id, run_id, invocation_id, stop_code, reason, state,
                    authority_receipt_id, created_at
                ) VALUES (?, ?, NULL, 'STOP-unknown', ?, 'closure', NULL, ?)
                """,
                (summon_id, run_id, reason, now),
            )
            connection.execute(
                "UPDATE trail_runs SET closure_state = 'parked', updated_at = ? WHERE run_id = ?",
                (now, run_id),
            )
            return self._get_run_locked(connection, run_id)

    def project_json(self, *, run_id: str, filename: str, payload: dict[str, Any]) -> Path:
        """Write a receipt projection exactly once, rejecting mismatched replacements."""
        if Path(filename).name != filename or not filename.endswith(".json"):
            raise TrailRunnerError("receipt projection filename must be a simple .json filename")
        target_dir = self.receipts_root / run_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / filename
        content = (canonical_json(payload) + "\n").encode("utf-8")
        try:
            descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError as exc:
            existing = target.read_bytes()
            if existing != content:
                raise ReceiptChainError(
                    f"immutable receipt projection differs: {target}"
                ) from exc
            return target
        try:
            with os.fdopen(descriptor, "wb") as receipt_file:
                receipt_file.write(content)
                receipt_file.flush()
                os.fsync(receipt_file.fileno())
        except BaseException:
            with suppress(OSError):
                target.unlink(missing_ok=True)
            raise
        return target

    def projection_path(self, *, run_id: str, filename: str) -> Path:
        """Return a deterministic projection path without trusting it as authority."""
        return self.receipts_root / run_id / filename
