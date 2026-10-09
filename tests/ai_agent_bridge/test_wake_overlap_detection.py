"""Fake resume races against real rollouts and durable existing inbox rows."""

import io
import json
import sqlite3
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from scripts.ai_agent_bridge import _inbox_watch as watch
from scripts.ai_agent_bridge import _ui_codex as ui

THREAD = "019e6063-c3da-78d1-acaa-4cd684a08786"
ARGS = ["codex", "--wake-driver", "codex", "--epic", "fixture", "--once"]


def append(path, kind, turn_id=None):
    payload = {"type": kind}
    if turn_id is not None:
        payload["turn_id"] = turn_id
    with path.open("a") as stream:
        stream.write(json.dumps({"type": "event_msg", "payload": payload}) + "\n")


@pytest.fixture
def wake(tmp_path, monkeypatch):
    db = tmp_path / "inbox.db"
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TABLE messages (id INTEGER PRIMARY KEY, from_llm, to_llm, task_id, content, consumed_by_live_driver, data)")
        conn.execute("INSERT INTO messages VALUES (7, 'sender', 'codex', 'fixture', 'pending', 0, ?)", (json.dumps({"attachment": "preserved"}),))
    rollout = tmp_path / "rollout-fixture.jsonl"
    rollout.write_text('{}\n')
    monkeypatch.setattr(watch._config, "DB_PATH", db)
    monkeypatch.setattr(watch, "DEFAULT_LOCK_DIR", tmp_path / "locks")
    lease = {"state": "active", "holder": {"agent": "codex"}, "generation": 2}
    remote = Mock(spec=["stream"])
    remote.stream.return_value = {"lease": lease}
    monkeypatch.setattr(ui, "find_live_session", lambda _: ui.LiveSession(THREAD, tmp_path, {}, rollout=rollout))
    monkeypatch.setattr(ui, "find_session_file", lambda _: None)
    service = Mock()
    service.store.connection.execute.return_value.fetchall.return_value = []
    service.__enter__ = Mock(return_value=service)
    service.__exit__ = Mock(return_value=False)
    monkeypatch.setattr("scripts.fleet_comms.authority.AuthorityService", lambda: service)
    monkeypatch.setattr("scripts.session_supervisor.remote.RemoteEpicClient", lambda: remote)
    lock = Mock()
    monkeypatch.setattr(watch, "acquire_watcher_lock", lambda *args: lock)
    state = SimpleNamespace(db=db, rollout=rollout, remote=remote, service=service, lock=lock, sends=0, action=lambda: None)

    def run(argv, **kwargs):
        if argv[0] == "bash":
            return SimpleNamespace(stdout="epic:123\n")
        assert argv[:3] == ["codex", "exec", "resume"]
        state.sends += 1
        state.action()  # Precisely after the final check, inside the fake process.
        return subprocess.CompletedProcess(argv, 0, stdout='{"type":"turn.started"}\n{"type":"turn.completed"}\n', stderr="")

    monkeypatch.setattr(ui.subprocess, "run", run)
    return state


def receipt(wake):
    with sqlite3.connect(wake.db) as conn:
        consumed, data = conn.execute("SELECT consumed_by_live_driver, data FROM messages WHERE id=7").fetchone()
    assert consumed == 0  # Only the live driver acknowledges even a clean wake.
    assert json.loads(data) == {"attachment": "preserved"}
    path = watch.codex_wake_state_path("codex")
    if not path.exists():
        return None
    attempts = json.loads(path.read_text())["receipts"].get("7", {})
    return next(iter(attempts.values()), None)


@pytest.mark.parametrize("ids", [True, False], ids=["turn-ids", "start-end-count"])
def test_attach_window_start_start_end_retained(wake, capsys, ids):
    def race():
        append(wake.rollout, "task_started", "live" if ids else None)
        append(wake.rollout, "task_started", "resume" if ids else None)
        append(wake.rollout, "task_complete", "resume" if ids else None)
    wake.action = race
    assert watch.main(ARGS) == 2
    report = receipt(wake)
    assert report["status"] == "OVERLAP"
    assert report["starts"] == 2 and report["ends"] == 1
    assert report["peak_open_count"] == 2 and report["open_count"] == 1
    assert report["turn_ids"] == (["live", "resume"] if ids else [])
    assert report["rollout"]["inode"] == wake.rollout.stat().st_ino
    assert report["message_ids"] == [7] and report["thread_id"] == THREAD
    assert '"status": "OVERLAP"' in capsys.readouterr().err


def test_clean_single_turn_advances_cursor_without_ack(wake, monkeypatch, capsys):
    def clean():
        append(wake.rollout, "turn_started", "resume")
        append(wake.rollout, "turn_complete", "resume")
    wake.action = clean
    monkeypatch.setattr(watch.time, "sleep", Mock(side_effect=[None, RuntimeError("stop test daemon")]))
    with pytest.raises(RuntimeError, match="stop test daemon"):
        watch.run_supervisory_wake_watcher("codex", "codex", "fixture", interval_seconds=0, once=False)
    assert wake.sends == 1
    assert receipt(wake) is None
    report = next(json.loads(line) for line in capsys.readouterr().err.splitlines() if line.startswith('{'))
    assert report["status"] == "CLEAN" and report["starts"] == report["ends"] == 1
    wake.lock.release.assert_called_once()


@pytest.mark.parametrize("damage", ["decode_error", "read_error", "rollout_changing", "partial_final_line", "resume_not_exited", "missing_wake_lifecycle", "open_turns", "rollout_replaced", "ambiguous_turn_lifecycle"])
def test_ambiguous_post_resume_is_unknown(wake, monkeypatch, damage):
    def action():
        if damage != "missing_wake_lifecycle":
            append(wake.rollout, "turn_started", "resume")
            append(wake.rollout, "turn_complete", "wrong" if damage == "ambiguous_turn_lifecycle" else "resume")
        if damage == "decode_error":
            with wake.rollout.open("ab") as stream:
                stream.write(b'{broken}\n')
        elif damage == "read_error":
            wake.rollout.unlink()
        elif damage == "partial_final_line":
            with wake.rollout.open("ab") as stream:
                stream.write(b'{"type":"event_msg"}')
        elif damage == "open_turns":
            append(wake.rollout, "turn_started", "live")
        elif damage == "rollout_replaced":
            replacement = wake.rollout.with_suffix(".replacement")
            replacement.write_text('{}\n')
            replacement.replace(wake.rollout)
    wake.action = action
    if damage == "rollout_changing":
        original = ui.RolloutReader.ready
        def ready(reader, path):
            if wake.sends:
                reader.after_read = lambda: append(path, "agent_message")
            return original(reader, path)
        monkeypatch.setattr(ui.RolloutReader, "ready", ready)
    if damage == "resume_not_exited":
        original = ui.send
        def send(**kwargs):
            result = original(**kwargs)
            result["resume_exited"] = False
            return result
        monkeypatch.setattr(ui, "send", send)
    assert watch.main(ARGS) == 2
    report = receipt(wake)
    assert report["status"] == "UNKNOWN"
    assert report["reason"].startswith(damage)
    assert wake.sends == 1


def test_second_start_appended_after_resume_exits_is_detected(wake, monkeypatch):
    wake.action = lambda: append(wake.rollout, "turn_started", "live")
    original = ui.send
    def after_exit(**kwargs):
        result = original(**kwargs)
        assert result["resume_exited"]
        append(wake.rollout, "turn_started", "resume")
        append(wake.rollout, "turn_complete", "resume")
        return result
    monkeypatch.setattr(ui, "send", after_exit)
    assert watch.main(ARGS) == 2
    assert receipt(wake)["status"] == "OVERLAP"


def test_same_open_turn_id_repeated_is_clean(wake, capsys):
    def duplicate():
        append(wake.rollout, "task_started", "resume")
        append(wake.rollout, "turn_started", "resume")
        append(wake.rollout, "task_complete", "resume")
    wake.action = duplicate
    assert watch.main(ARGS) == 0
    assert receipt(wake) is None
    assert '"status": "CLEAN"' in capsys.readouterr().err


@pytest.mark.parametrize("status", ["OVERLAP", "UNKNOWN"])
def test_kept_receipt_survives_new_watcher_and_refuses_silent_replay(wake, capsys, status):
    def action():
        if status == "OVERLAP":
            append(wake.rollout, "task_started", "live")
            append(wake.rollout, "task_started", "resume")
            append(wake.rollout, "task_complete", "resume")
        else:
            with wake.rollout.open("ab") as stream:
                stream.write(b'{bad}\n')
    wake.action = action
    assert watch.main(ARGS) == 2
    before = receipt(wake)
    assert before["status"] == status
    wake.rollout.write_text('{}\n')  # Now READY, yet the old attempt needs reconciliation.
    assert watch.main(ARGS) == 2
    assert wake.sends == 1
    assert receipt(wake) == before
    assert "retained_event" in capsys.readouterr().err


def test_notification_mode_surfaces_kept_row_without_resume(wake, monkeypatch):
    event = {"schema": "codex-wake.v1", "status": "OVERLAP", "reason": "concurrent_turn_starts"}
    watch.record_codex_wake([watch.InboxEvent(7, "sender", "fixture", "pending")], event)
    monkeypatch.setattr("scripts.ai_agent_bridge._ask_lifecycle.run_ask_watchdog", lambda: None)
    output = io.StringIO()
    assert watch.run_watcher("codex", db_path=wake.db, lock_dir=wake.db.parent / "locks", output=output, once=True) == 7
    assert "id=7" in output.getvalue()
    assert "codex_wake=OVERLAP" in output.getvalue()
    assert "concurrent_turn_starts" in output.getvalue()
    assert "pending" not in output.getvalue()
    assert "sender" not in output.getvalue()
    assert wake.sends == 0 and receipt(wake) == event


def test_once_final_recheck_refusal_exits_two_without_resume(wake, capsys):
    assert "--once" in watch.build_parser().format_help()
    lease = wake.remote.stream.return_value["lease"]
    calls = 0
    def stream(_):
        nonlocal calls
        calls += 1
        if calls == 2:
            append(wake.rollout, "task_started", "live")
        return {"lease": lease}
    wake.remote.stream.side_effect = stream
    assert watch.main(ARGS) == 2
    assert wake.sends == 0 and receipt(wake) is None
    assert "codex_wake_busy:start_event" in capsys.readouterr().err


def test_completed_overlap_is_still_reported(wake):
    def race():
        for kind, turn_id in [("task_started", "live"), ("task_started", "resume"), ("task_complete", "live"), ("task_complete", "resume")]:
            append(wake.rollout, kind, turn_id)
    wake.action = race
    assert watch.main(ARGS) == 2
    report = receipt(wake)
    assert report["status"] == "OVERLAP" and report["open_count"] == 0


def test_historical_overlap_does_not_contaminate_new_clean_wake(wake, capsys):
    append(wake.rollout, "task_started", "old-a")
    append(wake.rollout, "task_started", "old-b")
    append(wake.rollout, "task_complete", "old-a")
    append(wake.rollout, "task_complete", "old-b")
    def clean():
        append(wake.rollout, "task_started")
        append(wake.rollout, "turn_aborted")
    wake.action = clean
    assert watch.main(ARGS) == 0
    assert receipt(wake) is None
    assert '"status": "CLEAN"' in capsys.readouterr().err


@pytest.mark.parametrize("value", ['null', '{}', '[]', '""', '"x","turn_id":"y"', '"' + 'x' * 300 + '"'])
def test_ambiguous_turn_ids_leave_readiness_rules_unchanged(wake, value):
    def action():
        with wake.rollout.open("a") as stream:
            stream.write('{"type":"event_msg","payload":{"type":"task_started","turn_id":' + value + '}}\n')
        append(wake.rollout, "task_complete")
    wake.action = action
    assert watch.main(ARGS) == 2
    assert receipt(wake)["reason"] == "ambiguous_turn_lifecycle"
    assert ui.rollout_is_ready(wake.rollout) == (True, "end_event:task_complete")


def test_receipt_state_is_atomic_and_preserves_attachments(wake, monkeypatch):
    with sqlite3.connect(wake.db) as conn:
        conn.execute("INSERT INTO messages VALUES (8, 'sender', 'codex', 'fixture', 'pending', 0, '[1,2]')")
    event = {"schema": "codex-wake.v1", "status": "OVERLAP", "reason": "concurrent_turn_starts"}
    watch.record_codex_wake([watch.InboxEvent(7, "sender", "fixture", "pending")], event)
    path = watch.codex_wake_state_path("codex")
    before = path.read_bytes()
    monkeypatch.setattr(watch.os, "replace", Mock(side_effect=OSError("fixture write failure")))
    with pytest.raises(watch.CodexWakePersistenceError, match="receipt_write_failed"):
        watch.record_codex_wake([watch.InboxEvent(i, "sender", "fixture", "pending") for i in [7, 8]], event)
    assert path.read_bytes() == before
    assert receipt(wake) == event
    assert list(path.parent.iterdir()) == [path]  # Atomic-write temporary removed.
    assert path.stat().st_mode & 0o777 == 0o600
    with sqlite3.connect(wake.db) as conn:
        assert conn.execute("SELECT data FROM messages WHERE id=8").fetchone() == ('[1,2]',)


def test_daemon_stops_if_receipt_cannot_be_persisted(wake, monkeypatch, capsys):
    def race():
        append(wake.rollout, "task_started", "live")
        append(wake.rollout, "task_started", "resume")
        append(wake.rollout, "task_complete", "resume")
        with sqlite3.connect(wake.db) as conn:
            conn.execute("UPDATE messages SET data = '[1,2]' WHERE id=7")
        monkeypatch.setattr("scripts.ai_agent_bridge._monitor_cache._atomic_write", Mock(side_effect=OSError("fixture write failure")))
    wake.action = race
    sleep = Mock(side_effect=AssertionError("must stop rather than repeat"))
    monkeypatch.setattr(watch.time, "sleep", sleep)
    assert watch.run_supervisory_wake_watcher("codex", "codex", "fixture", interval_seconds=0, once=False) == 2
    assert wake.sends == 1
    sleep.assert_not_called()
    assert '"reason": "receipt_write_failed"' in capsys.readouterr().err


def test_failed_resume_after_complete_rollout_is_durable_unknown(wake, monkeypatch):
    def clean():
        append(wake.rollout, "task_started", "resume")
        append(wake.rollout, "task_complete", "resume")
    wake.action = clean
    original = ui.send
    def failed(**kwargs):
        result = original(**kwargs)
        result["exit_code"] = 1
        return result
    monkeypatch.setattr(ui, "send", failed)
    assert watch.main(ARGS) == 2
    assert receipt(wake)["reason"] == "resume_failed"
    assert watch.main(ARGS) == 2 and wake.sends == 1


def test_resume_exception_is_durable_unknown(wake, monkeypatch):
    def failed(**kwargs):
        kwargs["before_resume"]()
        append(wake.rollout, "task_started", "resume")
        raise ValueError("private failure detail")
    monkeypatch.setattr(ui, "send", failed)
    assert watch.main(ARGS) == 2
    assert receipt(wake)["reason"] == "resume_exception"
    assert watch.main(ARGS) == 2


def test_retained_receipt_does_not_echo_untrusted_extra_fields(wake, capsys):
    event = {"schema": "codex-wake.v1", "status": "OVERLAP", "reason": "concurrent_turn_starts", "private": "private attachment detail"}
    watch.record_codex_wake([watch.InboxEvent(7, "sender", "fixture", "pending")], event)
    assert watch.main(ARGS) == 2
    assert "private attachment detail" not in capsys.readouterr().err
    assert wake.sends == 0


def test_open_turn_bound_is_unknown(wake):
    def overflow():
        for number in range(1025):
            append(wake.rollout, "task_started", f"turn-{number}")
    wake.action = overflow
    assert watch.main(ARGS) == 2
    assert receipt(wake)["reason"] == "ambiguous_turn_lifecycle"


@pytest.mark.parametrize("historical", [False, True])
def test_idless_completions_decrement_multiple_named_turns(wake, capsys, historical):
    def mixed():
        append(wake.rollout, "task_started", "a")
        append(wake.rollout, "task_started", "b")
        append(wake.rollout, "task_complete")
        append(wake.rollout, "turn_aborted")
    if historical:
        mixed()
        def clean():
            append(wake.rollout, "task_started", "resume")
            append(wake.rollout, "task_complete", "resume")
        wake.action = clean
        assert watch.main(ARGS) == 0
        assert '"status": "CLEAN"' in capsys.readouterr().err
    else:
        wake.action = mixed
        assert watch.main(ARGS) == 2
        report = receipt(wake)
        assert report["status"] == "UNKNOWN" and report["open_count"] == 0


@pytest.mark.parametrize("status", ["OVERLAP", "UNKNOWN"])
def test_retained_receipt_daemon_keeps_running_without_replay(wake, monkeypatch, status):
    def action():
        if status == "OVERLAP":
            append(wake.rollout, "task_started", "live")
            append(wake.rollout, "task_started", "resume")
            append(wake.rollout, "task_complete", "resume")
        else:
            with wake.rollout.open("ab") as stream:
                stream.write(b'{broken}\n')
    wake.action = action
    sleep = Mock(side_effect=[None, OSError("stop test daemon")])
    monkeypatch.setattr(watch.time, "sleep", sleep)
    with pytest.raises(OSError, match="stop test daemon"):
        watch.run_supervisory_wake_watcher("codex", "codex", "fixture", interval_seconds=0, once=False)
    assert sleep.call_count == 2 and wake.sends == 1
    assert receipt(wake)["status"] == status


@pytest.mark.parametrize("data", ["attachment text\nsecond line", "", None, '[1,2]', '"attachment"', '17', 'true', 'null', '{broken}', '{}'])
def test_attachment_without_receipt_wakes_normally(wake, data, monkeypatch, capsys):
    with sqlite3.connect(wake.db) as conn:
        conn.execute("UPDATE messages SET data = ? WHERE id=7", (data,))
    def clean():
        append(wake.rollout, "task_started", "resume")
        append(wake.rollout, "task_complete", "resume")
    wake.action = clean
    # As for object attachments, CLEAN advances only the watcher's cursor.
    # Inbox consumption still belongs to the live driver.
    monkeypatch.setattr(watch.time, "sleep", Mock(side_effect=[None, RuntimeError("stop test daemon")]))
    with pytest.raises(RuntimeError, match="stop test daemon"):
        watch.run_supervisory_wake_watcher("codex", "codex", "fixture", interval_seconds=0, once=False)
    assert wake.sends == 1
    with sqlite3.connect(wake.db) as conn:
        assert conn.execute("SELECT data, consumed_by_live_driver FROM messages WHERE id=7").fetchone() == (data, 0)
    assert '"status": "CLEAN"' in capsys.readouterr().err


def test_plain_text_after_retained_receipt_is_held_only_by_receipt(wake, capsys):
    report = {"schema": "codex-wake.v1", "status": "OVERLAP", "reason": "concurrent_turn_starts"}
    watch.record_codex_wake([watch.InboxEvent(7, "sender", "fixture", "pending")], report)
    with sqlite3.connect(wake.db) as conn:
        conn.execute("INSERT INTO messages VALUES (8, 'sender', 'codex', 'fixture', 'later', 0, 'plain attachment')")
    with watch.open_readonly_db(wake.db) as conn:
        events = watch.poll_once(conn, "codex")
    assert [event.message_id for event in events] == [7, 8]
    assert events[0].wake_event == report
    assert events[1].wake_event is None
    assert watch.main(ARGS) == 2
    assert wake.sends == 0
    assert "retained_event" in capsys.readouterr().err
    # The existing live-driver consumption flag unblocks the next row;
    # reconciliation garbage-collects the watcher-owned receipt.
    with sqlite3.connect(wake.db) as conn:
        conn.execute("UPDATE messages SET consumed_by_live_driver=1 WHERE id=7")
    def clean():
        append(wake.rollout, "task_started", "resume")
        append(wake.rollout, "task_complete", "resume")
    wake.action = clean
    assert watch.main(ARGS) == 0
    assert wake.sends == 1
    with sqlite3.connect(wake.db) as conn:
        assert json.loads(conn.execute("SELECT data FROM messages WHERE id=7").fetchone()[0]) == {"attachment": "preserved"}
        assert json.loads(watch.codex_wake_state_path("codex").read_text())["receipts"] == {}
        assert conn.execute("SELECT data, consumed_by_live_driver FROM messages WHERE id=8").fetchone() == ("plain attachment", 0)


@pytest.mark.parametrize("data", ['{"raw": "sender attachment"}', '{"attachment": "preserved"}', 'plain attachment\nwith "quotes" and a backslash \\', '', '[1,2]', '"attachment"', '17', 'true', 'null', '{broken}'])
def test_retained_receipt_preserves_attachment_for_reader(wake, data, monkeypatch, capsys):
    from scripts.ai_agent_bridge import _messaging
    from scripts.ai_agent_bridge._ask_lifecycle import ask_attachment

    with sqlite3.connect(wake.db) as conn:
        conn.execute("UPDATE messages SET data = ? WHERE id=7", (data,))
    def race():
        append(wake.rollout, "task_started", "live")
        append(wake.rollout, "task_started", "resume")
        append(wake.rollout, "task_complete", "resume")
    wake.action = race
    assert watch.main(ARGS) == 2
    assert wake.sends == 1
    with sqlite3.connect(wake.db) as conn:
        stored, consumed = conn.execute("SELECT data, consumed_by_live_driver FROM messages WHERE id=7").fetchone()
        conn.execute("ALTER TABLE messages ADD COLUMN message_type TEXT DEFAULT 'message'")
        conn.execute("ALTER TABLE messages ADD COLUMN timestamp TEXT DEFAULT 'fixture'")
    monkeypatch.setattr(_messaging, "get_db", lambda: sqlite3.connect(wake.db))
    message = _messaging.read_message(7, quiet=True)
    assert consumed == 0
    assert stored == data
    assert message["data"] == data
    assert ask_attachment(message) == ask_attachment({"data": data})
    _messaging.read_message(7)
    output = capsys.readouterr().out
    assert data in output
    assert "codex_wake" not in output
    assert "[REDACTED_SECRET]" not in output
    assert watch.read_codex_wakes("codex", {7})[7]["status"] == "OVERLAP"
    assert watch.main(ARGS) == 2
    assert wake.sends == 1


@pytest.mark.parametrize("event", [
    None, [], "claimed event", {},
    {"schema": "codex-wake.v1", "status": "CLEAN", "reason": "completed"},
    {"schema": "codex-wake.v1", "status": "OTHER", "reason": "completed"},
    {"schema": "codex-wake.v1", "status": [], "reason": "completed"},
    {"schema": "codex-wake.v1", "status": {}, "reason": "completed"},
    {"schema": "other", "status": "OVERLAP", "reason": "concurrent_turn_starts"},
    {"schema": "codex-wake.v1", "status": "UNKNOWN", "reason": "untrusted\ntext"},
    {"schema": "codex-wake.v1", "status": "UNKNOWN", "reason": "open_turns", "starts": True},
    {"schema": "codex-wake.v1", "status": "UNKNOWN", "reason": "open_turns", "message_ids": ["7"]},
    {"schema": "codex-wake.v1", "status": "UNKNOWN", "reason": "open_turns", "turn_ids": ["bad\nturn"]},
    {"schema": "codex-wake.v1", "status": "UNKNOWN", "reason": "open_turns", "thread_id": "bad"},
    {"schema": "codex-wake.v1", "status": "UNKNOWN", "reason": "open_turns", "rollout": {}},
])
def test_invalid_receipt_has_distinct_refusal_reason(wake, capsys, event):
    data = json.dumps({"codex_wake": event, "raw": "attachment survives"})
    with sqlite3.connect(wake.db) as conn:
        conn.execute("UPDATE messages SET data=? WHERE id=7", (data,))
    path = watch.codex_wake_state_path("codex")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"schema": "inbox-wake-state.v1", "receipts": {"7": {"0" * 64: event}}}))
    for _ in range(3):
        assert watch.main(ARGS) == 2
    assert wake.sends == 0
    diagnostics = capsys.readouterr().err
    assert "wake_error:codex_wake:UNKNOWN:retained_receipt_invalid" in diagnostics
    assert "retained_event" not in diagnostics
    assert "untrusted" not in diagnostics
    with sqlite3.connect(wake.db) as conn:
        assert conn.execute("SELECT data, consumed_by_live_driver FROM messages WHERE id=7").fetchone() == (data, 0)


@pytest.mark.parametrize("failure", ["overlap", "missing_binary"])
def test_wake_error_prints_inbox_retained_once(wake, monkeypatch, capsys, failure):
    if failure == "overlap":
        report = {"schema": "codex-wake.v1", "status": "OVERLAP", "reason": "concurrent_turn_starts"}
        watch.record_codex_wake([watch.InboxEvent(7, "sender", "fixture", "pending")], report)
    else:
        monkeypatch.setattr(ui, "send", Mock(side_effect=FileNotFoundError()))
    assert watch.main(ARGS) == 2
    line = next(line for line in capsys.readouterr().err.splitlines() if "wake_error:" in line)
    assert line.count("inbox retained") == 1


@pytest.mark.parametrize("forged", [
    {"schema": "codex-wake.v1", "status": "OVERLAP", "reason": "concurrent_turn_starts"},
    {"schema": "codex-wake.v1", "status": "CLEAN", "reason": "completed"},
    "x", None, 17, [1, 2],
    {"raw": "attachment", "codex_wake": {"status": "OVERLAP"}},
], ids=["overlap", "clean", "string", "null", "number", "array", "wrapper"])
@pytest.mark.parametrize("attachment_type", ["plain-text", "json-object"])
def test_sender_supplied_wake_key_has_no_effect(wake, capsys, forged, attachment_type):
    payload = json.dumps({"raw": "sender attachment", "codex_wake": forged})
    data = payload if attachment_type == "json-object" else "sender attachment\n" + payload
    with sqlite3.connect(wake.db) as conn:
        conn.execute("UPDATE messages SET data=? WHERE id=7", (data,))
        conn.execute("INSERT INTO messages VALUES (8, 'sender', 'codex', 'fixture', 'later', 0, 'next attachment')")
    def clean():
        append(wake.rollout, "task_started", "resume")
        append(wake.rollout, "task_complete", "resume")
    wake.action = clean
    assert watch.main(ARGS) == 0
    assert wake.sends == 1
    diagnostics = capsys.readouterr().err
    assert '"status": "CLEAN"' in diagnostics
    assert '"message_ids": [7, 8]' in diagnostics
    assert "sender attachment" not in diagnostics
    with sqlite3.connect(wake.db) as conn:
        assert conn.execute("SELECT data, consumed_by_live_driver FROM messages WHERE id=7").fetchone() == (data, 0)


@pytest.mark.parametrize("status", ["OVERLAP", "UNKNOWN"])
@pytest.mark.parametrize("disposition", ["ack", "deleted"])
def test_stale_watcher_receipt_is_collected_before_newer_wake(wake, monkeypatch, status, disposition):
    from scripts.ai_agent_bridge import _messaging

    report = {"schema": "codex-wake.v1", "status": status, "reason": "open_turns"}
    watch.record_codex_wake([watch.InboxEvent(7, "sender", "fixture", "pending")], report)
    with sqlite3.connect(wake.db) as conn:
        if disposition == "deleted":
            conn.execute("DELETE FROM messages WHERE id=7")
        conn.execute("INSERT INTO messages VALUES (8, 'sender', 'codex', 'fixture', 'later', 0, 'next attachment')")
        conn.execute("ALTER TABLE messages ADD COLUMN acknowledged INTEGER DEFAULT 0")
        conn.execute("ALTER TABLE messages ADD COLUMN consumed_at TEXT")
    if disposition == "ack":
        monkeypatch.setattr(_messaging, "get_db", lambda: sqlite3.connect(wake.db))
        _messaging.acknowledge(7, quiet=True, consumed_by_live_driver=True)
    def clean():
        append(wake.rollout, "task_started", "resume")
        append(wake.rollout, "task_complete", "resume")
    wake.action = clean
    assert watch.main(ARGS) == 0 and wake.sends == 1
    assert json.loads(watch.codex_wake_state_path("codex").read_text())["receipts"] == {}


@pytest.mark.parametrize("data", [
    '{broken}', 'null', '[]', '{}',
    '{"schema":"other","receipts":{}}',
    '{"schema":"inbox-wake-state.v1","receipts":[]}',
    '{"schema":"inbox-wake-state.v1","receipts":{"bad":{}}}',
    '{"schema":"inbox-wake-state.v1","receipts":{"7":{}}}',
    '{"schema":"inbox-wake-state.v1","receipts":{"7":[]}}',
])
def test_corrupted_state_refuses_and_is_collected_after_ack(wake, capsys, data):
    path = watch.codex_wake_state_path("codex")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data)
    for _ in range(2):
        assert watch.main(ARGS) == 2
    assert wake.sends == 0
    diagnostics = capsys.readouterr().err
    assert '"message_ids": [7]' in diagnostics
    assert "retained_receipt_invalid" in diagnostics
    assert "pending" not in diagnostics and str(wake.db.parent) not in diagnostics
    with sqlite3.connect(wake.db) as conn:
        conn.execute("UPDATE messages SET consumed_by_live_driver=1 WHERE id=7")
    assert watch.main(ARGS) == 0
    assert json.loads(path.read_text())["receipts"] == {}


def test_unreadable_watcher_state_refuses_before_resume(wake, monkeypatch, capsys):
    monkeypatch.setattr(watch, "_read_wake_state", Mock(side_effect=PermissionError("private path")))
    assert watch.main(ARGS) == 2 and wake.sends == 0
    diagnostics = capsys.readouterr().err
    assert "retained_receipt_invalid" in diagnostics
    assert "private path" not in diagnostics


def test_rollout_key_is_identity_bound_and_does_not_use_cursor(wake):
    report = {"schema": "codex-wake.v1", "status": "UNKNOWN", "reason": "open_turns",
              "message_ids": [7], "thread_id": THREAD,
              "rollout": {"path_sha256": "a" * 64, "device": 1, "inode": 2, "offset": 3}}
    watch.record_codex_wake([watch.InboxEvent(7, "sender", "fixture", "pending")], report)
    key = watch._rollout_key(report)
    assert watch._rollout_key({**report, "rollout": {**report["rollout"], "offset": 99}}) == key
    assert watch._rollout_key({**report, "rollout": {**report["rollout"], "inode": 99}}) != key
    assert watch._rollout_key({**report, "thread_id": "019e6063-c3da-78d1-acaa-4cd684a08787"}) != key
    path = watch.codex_wake_state_path("codex")
    state = json.loads(path.read_text())
    state["receipts"]["7"][key]["rollout"]["inode"] = 99
    path.write_text(json.dumps(state))
    assert watch.main(ARGS) == 2 and wake.sends == 0
    assert watch.read_codex_wakes("codex", {7})[7]["reason"] == "retained_receipt_invalid"


def test_notification_cursor_preserves_receipt_until_ack(wake, monkeypatch):
    report = {"schema": "codex-wake.v1", "status": "UNKNOWN", "reason": "open_turns"}
    watch.record_codex_wake([watch.InboxEvent(7, "sender", "fixture", "pending")], report)
    with watch.open_readonly_db(wake.db) as conn:
        assert watch.poll_once(conn, "codex", last_seen=7) == []
    assert receipt(wake) == report
    assert watch.main(ARGS) == 2 and wake.sends == 0
