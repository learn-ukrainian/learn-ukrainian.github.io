from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from agents_extensions.shared.session_streams.cli import build_parser, main
from agents_extensions.shared.session_streams.db import SessionStreamDatabase
from agents_extensions.shared.session_streams.model import EntryType, LeaseHolder
from agents_extensions.shared.session_streams.store import SessionStreamStore

NOW = datetime(2026, 7, 18, 12, 0, tzinfo=UTC)


def _populated_database(tmp_path: Path) -> Path:
    path = tmp_path / "streams.sqlite3"
    store = SessionStreamStore(SessionStreamDatabase(path))
    lease = store.open_session(
        stream_id="epic:4707",
        holder=LeaseHolder(
            agent="codex",
            harness="codex",
            instance_id="cli-test",
            task_id="task-cli-test",
            process_id=44004,
        ),
        lineage_id="lineage-cli",
        ttl_seconds=60,
        session_id="session-cli",
        lease_id="lease-cli",
        now=NOW,
    )
    store.append_entry(
        lease,
        entry_type=EntryType.BINDING_ORDER,
        body="Pinned CLI order.",
        idempotency_key="cli-order",
        now=NOW + timedelta(seconds=1),
    )
    for index in range(3):
        store.append_entry(
            lease,
            entry_type=EntryType.NOTE,
            body=f"CLI note {index}",
            idempotency_key=f"cli-note-{index}",
            now=NOW + timedelta(seconds=2 + index),
        )
    return path


def test_help_is_self_sufficient() -> None:
    help_text = build_parser().format_help()
    assert "Outputs:" in help_text
    assert "Exit codes:" in help_text
    assert "Related:" in help_text
    assert "do not use it to cut over or retire file handoffs" in help_text


def test_tail_json_preserves_pinned_plus_last_n(tmp_path: Path, capsys) -> None:
    database = _populated_database(tmp_path)

    exit_code = main(
        ["--db", str(database), "tail", "--stream", "epic:4707", "--limit", "1", "--format", "json"]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert [entry["body"] for entry in payload["pinned"]] == ["Pinned CLI order."]
    assert [entry["body"] for entry in payload["recent"]] == ["CLI note 2"]
    assert len(payload["digest_sha256"]) == 64


def test_dump_jsonl_writes_atomically_complete_history(tmp_path: Path, capsys) -> None:
    database = _populated_database(tmp_path)
    output = tmp_path / "exports" / "epic-4707.jsonl"

    exit_code = main(
        [
            "--db",
            str(database),
            "dump",
            "--stream",
            "epic:4707",
            "--format",
            "jsonl",
            "--output",
            str(output),
        ]
    )

    assert exit_code == 0
    assert capsys.readouterr().out.strip() == str(output)
    records = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    record_types = {record["record_type"] for record in records}
    assert {"schema_migrations", "stream", "sessions", "session_events", "lease_events", "lease", "entries"} <= record_types
    assert not list(output.parent.glob(f".{output.name}.*.tmp"))


def test_tail_missing_stream_has_stable_exit_code(tmp_path: Path, capsys) -> None:
    database = _populated_database(tmp_path)

    exit_code = main(["--db", str(database), "tail", "--stream", "epic:9999"])

    assert exit_code == 3
    assert "stream not found" in capsys.readouterr().err
