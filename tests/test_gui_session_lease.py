from __future__ import annotations

import json
import sqlite3
from datetime import timedelta
from pathlib import Path

from agents_extensions.shared.session_streams.model import isoformat_z, utc_now
from scripts.orchestration import gui_session_lease

TASK_ID = "019fb7a7-5e56-7760-8f53-0980ec7f0d0b"
PREDECESSOR_ID = "219fb7a7-5e56-7760-8f53-0980ec7f0d0b"


def _codex_fixture(
    tmp_path: Path,
    *,
    task_id: str = TASK_ID,
    output_task_id: str | None = None,
    include_outputs: bool = False,
    observed_offset: timedelta = timedelta(),
) -> tuple[Path, Path]:
    state_db = tmp_path / "state_5.sqlite"
    rollout = tmp_path / "rollout.jsonl"
    observed_at = isoformat_z(utc_now() + observed_offset)
    call_id = "call-native-read-thread"
    call = {
        "timestamp": observed_at,
        "type": "response_item",
        "payload": {
            "type": "function_call",
            "name": "read_thread",
            "call_id": call_id,
            "arguments": json.dumps(
                {
                    "threadId": task_id,
                    "turnLimit": 1,
                    "includeOutputs": include_outputs,
                    "maxOutputCharsPerItem": 400,
                },
                sort_keys=True,
            ),
        },
    }
    output = {
        "timestamp": observed_at,
        "type": "response_item",
        "payload": {
            "type": "function_call_output",
            "call_id": call_id,
            "output": json.dumps(
                {
                    "schemaVersion": 1,
                    "thread": {
                        "id": output_task_id or task_id,
                        "kind": "codex",
                        "hostId": "local",
                        "status": {"type": "active", "activeFlags": []},
                        "cwd": str(tmp_path),
                        "createdAt": 100,
                        "updatedAt": 200,
                    },
                },
                sort_keys=True,
            ),
        },
    }
    rollout.write_text(
        json.dumps(call, sort_keys=True) + "\n" + json.dumps(output, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with sqlite3.connect(state_db) as connection:
        connection.execute(
            "CREATE TABLE threads("
            "id TEXT PRIMARY KEY, title TEXT NOT NULL, cwd TEXT NOT NULL, rollout_path TEXT NOT NULL, "
            "created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL, archived INTEGER NOT NULL, archived_at INTEGER)"
        )
        connection.execute(
            "INSERT INTO threads VALUES (?, 'private title', ?, ?, 100, 200, 0, NULL)",
            (task_id, str(tmp_path), str(rollout)),
        )
    return state_db, rollout


def _base(session_db: Path, state_db: Path) -> list[str]:
    return [
        "--db",
        str(session_db),
        "--codex-state-db",
        str(state_db),
        "--proof-valid-seconds",
        "600",
        "--task-id",
        TASK_ID,
        "--stream-id",
        "epic:4707",
    ]


def test_source_blind_cli_lifecycle_and_exact_replay(tmp_path: Path, capsys) -> None:
    state_db, _ = _codex_fixture(tmp_path)
    session_db = tmp_path / "session-streams.sqlite3"
    acquire = [
        *_base(session_db, state_db),
        "acquire",
        "--lineage-id",
        "lineage-test",
        "--ttl-seconds",
        "60",
        "--session-id",
        "session-gui",
        "--lease-id",
        "lease-gui",
    ]
    assert gui_session_lease.main(acquire) == 0
    assert gui_session_lease.main(acquire) == 0
    assert gui_session_lease.main([*_base(session_db, state_db), "renew"]) == 0
    append = [
        *_base(session_db, state_db),
        "append",
        "--entry-type",
        "note",
        "--body",
        "Exact GUI lifecycle canary.",
        "--idempotency-key",
        "gui-canary-1",
    ]
    assert gui_session_lease.main(append) == 0
    assert gui_session_lease.main(append) == 0
    assert (
        gui_session_lease.main(
            [
                *_base(session_db, state_db),
                "transition",
                "--to-state",
                "rolling",
                "--reason",
                "rollover canary",
            ]
        )
        == 0
    )
    close = [*_base(session_db, state_db), "close", "--reason", "canary complete"]
    assert gui_session_lease.main(close) == 0
    assert gui_session_lease.main(close) == 0
    capsys.readouterr()

    with sqlite3.connect(session_db) as connection:
        assert connection.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM entries").fetchone()[0] == 1
        assert connection.execute("SELECT state FROM stream_leases").fetchone()[0] == "released"
        proofs = "\n".join(row[0] for row in connection.execute("SELECT proof_json FROM lease_events"))
        transition_proof = json.loads(
            connection.execute(
                "SELECT proof_json FROM lease_events WHERE event_type = 'transitioned'"
            ).fetchone()[0]
        )
    assert TASK_ID in proofs
    assert "private title" not in proofs
    assert "preview" not in proofs
    assert transition_proof["receipt"]["operation"] == "transition"


def test_native_readback_rejects_leaky_mismatched_stale_and_future_evidence(tmp_path: Path) -> None:
    for name, fixture_kwargs in (
        ("leaky", {"include_outputs": True}),
        ("wrong-task", {"output_task_id": "119fb7a7-5e56-7760-8f53-0980ec7f0d0b"}),
    ):
        case = tmp_path / name
        case.mkdir()
        state_db, _ = _codex_fixture(case, **fixture_kwargs)
        assert (
            gui_session_lease.main(
                [
                    *_base(case / "streams.sqlite3", state_db),
                    "acquire",
                    "--lineage-id",
                    "lineage-test",
                    "--ttl-seconds",
                    "60",
                    "--session-id",
                    "session-gui",
                    "--lease-id",
                    "lease-gui",
                ]
            )
            == 2
        )

    for name, offset in (
        ("stale", timedelta(minutes=-20)),
        ("future", timedelta(minutes=20)),
    ):
        case = tmp_path / name
        case.mkdir()
        state_db, _ = _codex_fixture(case, observed_offset=offset)
        assert (
            gui_session_lease.main(
                [
                    *_base(case / "streams.sqlite3", state_db),
                    "--proof-valid-seconds",
                    "60",
                    "acquire",
                    "--lineage-id",
                    "lineage-test",
                    "--ttl-seconds",
                    "60",
                    "--session-id",
                    "session-gui",
                    "--lease-id",
                    "lease-gui",
                ]
            )
            == 2
        )


def test_archived_and_absent_native_tasks_are_recovery_only(tmp_path: Path) -> None:
    state_db, _ = _codex_fixture(tmp_path)
    with sqlite3.connect(state_db) as connection:
        connection.execute("UPDATE threads SET archived = 1, archived_at = 300")
    terminal = gui_session_lease.CodexGuiSessionLeaseAdapter.discover_native_readback(
        task_id=TASK_ID,
        state_db=state_db,
        require_recovery_state=True,
    )
    assert terminal["thread"]["status_type"] == "terminal"  # type: ignore[index]

    with sqlite3.connect(state_db) as connection:
        connection.execute("DELETE FROM threads")
    absent = gui_session_lease.CodexGuiSessionLeaseAdapter.discover_native_readback(
        task_id=TASK_ID,
        state_db=state_db,
        require_recovery_state=True,
    )
    assert absent["thread"]["status_type"] == "absent"  # type: ignore[index]


def test_cli_recovery_requires_archived_predecessor_and_is_exactly_replayable(tmp_path: Path) -> None:
    predecessor_root = tmp_path / "predecessor"
    predecessor_root.mkdir()
    state_db, _ = _codex_fixture(predecessor_root, task_id=PREDECESSOR_ID)
    session_db = tmp_path / "session-streams.sqlite3"
    predecessor_base = [
        "--db",
        str(session_db),
        "--codex-state-db",
        str(state_db),
        "--proof-valid-seconds",
        "600",
        "--task-id",
        PREDECESSOR_ID,
        "--stream-id",
        "epic:4707",
    ]
    assert (
        gui_session_lease.main(
            [
                *predecessor_base,
                "acquire",
                "--lineage-id",
                "lineage-predecessor",
                "--ttl-seconds",
                "60",
                "--session-id",
                "session-predecessor",
                "--lease-id",
                "lease-predecessor",
            ]
        )
        == 0
    )

    successor_root = tmp_path / "successor"
    successor_root.mkdir()
    successor_db, _ = _codex_fixture(successor_root)
    with sqlite3.connect(successor_db) as source:
        successor_row = source.execute("SELECT * FROM threads").fetchone()
    assert successor_row is not None
    with sqlite3.connect(state_db) as connection:
        connection.execute("UPDATE threads SET archived = 1, archived_at = 300 WHERE id = ?", (PREDECESSOR_ID,))
        connection.execute("INSERT INTO threads VALUES (?, ?, ?, ?, ?, ?, ?, ?)", tuple(successor_row))

    recover = [
        *_base(session_db, state_db),
        "recover",
        "--predecessor-task-id",
        PREDECESSOR_ID,
        "--predecessor-instance-id",
        "codex-desktop-local",
        "--predecessor-session-id",
        "session-predecessor",
        "--predecessor-lease-id",
        "lease-predecessor",
        "--predecessor-generation",
        "1",
        "--predecessor-fencing-token",
        "1",
        "--lineage-id",
        "lineage-successor",
        "--rollover-id",
        "rollover-exact",
        "--ttl-seconds",
        "60",
        "--session-id",
        "session-successor",
        "--lease-id",
        "lease-successor",
    ]
    assert gui_session_lease.main(recover) == 0
    assert gui_session_lease.main(recover) == 0
    with sqlite3.connect(session_db) as connection:
        connection.row_factory = sqlite3.Row
        projection = connection.execute("SELECT * FROM stream_leases").fetchone()
        assert projection is not None
        assert projection["holder_task_id"] == TASK_ID
        assert (projection["generation"], projection["fencing_token"]) == (2, 2)
