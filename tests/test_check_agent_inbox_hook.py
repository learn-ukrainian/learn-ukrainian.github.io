"""Exercise the native hook's supported metadata-only probe (#10800)."""

import json
import os
import sqlite3
import subprocess
import sys
from contextlib import closing
from pathlib import Path

import pytest

from scripts import inbox_pending
from scripts.fleet_comms.migrations import apply_migrations
from tests.helpers.agy_inbox_fixtures import add_authority

HOOK = Path(__file__).resolve().parents[1] / "agents_extensions/shared/hooks/check-agent-inbox.sh"


def _run_probe(monkeypatch, db: Path, recipient: str) -> None:
    assert '-m scripts.inbox_pending --native-hook --recipient "$recipient"' in HOOK.read_text()
    monkeypatch.setenv("AB_DB_PATH", str(db))
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(db.parent))
    assert inbox_pending.main(["--native-hook", "--recipient", recipient]) == 0


@pytest.mark.parametrize("recipient", ["codex", "grok", "grok-build"])
def test_probe_special_path_counts_one_unread_and_is_readonly(tmp_path, monkeypatch, capsys, recipient):
    db = tmp_path / "inbox ? # % space.db"
    target = "grok-build" if recipient == "grok" else "grok" if recipient == "grok-build" else recipient
    with closing(sqlite3.connect(db)) as conn:
        conn.execute("CREATE TABLE messages (id INTEGER PRIMARY KEY, to_llm TEXT, acknowledged INTEGER, consumed_by_live_driver INTEGER)")
        conn.executemany(
            "INSERT INTO messages(to_llm, acknowledged, consumed_by_live_driver) VALUES (?, ?, ?)",
            [(target, None, None), (target, 1, 0), (target, 0, 1), ("claude", 0, 0)],
        )
        conn.commit()
    before = db.read_bytes()
    authority = tmp_path / "comms.sqlite3"
    with closing(sqlite3.connect(authority)) as conn:
        apply_migrations(conn)
    add_authority(authority, recipient=recipient)
    add_authority(authority, recipient="lane:infra", identifier="authority-message_" + "b" * 32, delivery_id="lane-row")
    add_authority(authority, recipient="claude-infra", identifier="authority-message_" + "c" * 32, delivery_id="old-alias")
    add_authority(authority, recipient="grok-infra", identifier="authority-message_" + "d" * 32, delivery_id="new-alias")
    authority_before = authority.read_bytes()
    connect = sqlite3.connect
    opened = []

    def inspect_connection(*args, **kwargs):
        conn = connect(*args, **kwargs)
        opened.append(conn)
        assert Path(conn.execute("PRAGMA database_list").fetchone()[2]) in {db.resolve(), authority.resolve()}
        assert conn.execute("PRAGMA busy_timeout").fetchone() == (200,)
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            conn.execute("CREATE TABLE forbidden_write(value TEXT)")
        return conn

    monkeypatch.setattr(sqlite3, "connect", inspect_connection)
    _run_probe(monkeypatch, db, recipient)

    output = json.loads(capsys.readouterr().out)["hookSpecificOutput"]
    assert output["hookEventName"] == "UserPromptSubmit"
    line = output["additionalContext"]
    assert line.startswith("AUTHORITY INBOX: 1; oldest ")
    assert f'; legacy 1; .venv/bin/python -m scripts.fleet_comms deliveries claim --recipient {recipient}' in line
    assert len(opened) == 2
    for conn in opened:
        with pytest.raises(sqlite3.ProgrammingError, match="closed"):
            conn.execute("SELECT 1")
    env = {
        **os.environ, "CLAUDE_PROJECT_DIR": str(HOOK.parents[3]), "LU_DRIVER_STATE_PYTHON": sys.executable,
        "SESSION_HANDOFF_AGENT": "infra", "GEMINI_SESSION": "0", "LEARN_UKRAINIAN_PIPELINE": "0",
    }
    actual_hook = subprocess.run(["bash", str(HOOK)], input="{}", env=env, text=True, capture_output=True, timeout=10)
    assert actual_hook.returncode == 0 and actual_hook.stderr == ""
    actual_line = json.loads(actual_hook.stdout)["hookSpecificOutput"]["additionalContext"]
    assert actual_line.startswith("AUTHORITY INBOX: 3; oldest ")
    assert "; legacy 0; .venv/bin/python -m scripts.fleet_comms deliveries claim --recipient lane:infra" in actual_line
    assert "UNIQUE_PRIVATE_BODY" not in actual_line
    assert db.read_bytes() == before
    assert authority.read_bytes() == authority_before
    assert set(tmp_path.iterdir()) == {db, authority}


@pytest.mark.parametrize("state", ["empty", "missing", "corrupt", "schema_drift"])
def test_probe_empty_and_error_results(tmp_path, monkeypatch, capsys, state):
    db = tmp_path / "inbox ? #.db"
    if state == "corrupt":
        db.write_bytes(b"not a SQLite database")
    elif state in ("empty", "schema_drift"):
        with closing(sqlite3.connect(db)) as conn:
            if state == "empty":
                conn.execute("CREATE TABLE messages (id INTEGER PRIMARY KEY, to_llm TEXT, acknowledged INTEGER, consumed_by_live_driver INTEGER)")
            else:
                conn.execute("CREATE TABLE unrelated (id INTEGER)")
            conn.commit()
    before = db.read_bytes() if db.exists() else None
    authority = tmp_path / "comms.sqlite3"
    if state == "empty":
        with closing(sqlite3.connect(authority)) as conn:
            apply_migrations(conn)
    elif state != "missing":
        authority.write_bytes(b"not a SQLite database")
    authority_before = authority.read_bytes() if authority.exists() else None

    _run_probe(monkeypatch, db, "codex")

    captured = capsys.readouterr()
    line = json.loads(captured.out)["hookSpecificOutput"]["additionalContext"]
    assert line.startswith(
        "AUTHORITY INBOX: 0; oldest none; legacy 0;" if state == "empty"
        else "AUTHORITY INBOX: unknown; oldest unknown; legacy unknown;"
    )
    assert "deliveries claim --recipient codex" in line
    assert captured.err == ""
    assert (db.read_bytes() if db.exists() else None) == before
    assert (authority.read_bytes() if authority.exists() else None) == authority_before
    assert set(tmp_path.iterdir()) == (set() if state == "missing" else {db, authority})
