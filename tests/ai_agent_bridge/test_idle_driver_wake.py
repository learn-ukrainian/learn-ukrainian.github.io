"""Fake-only coverage for unread inbox turns under an occupied Codex lease."""

from __future__ import annotations

import io
import json
import sqlite3
import subprocess
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, call

import psutil
import pytest

from scripts.ai_agent_bridge import _inbox_watch as watch
from scripts.ai_agent_bridge import _ui_codex as ui

THREAD = "019e6063-c3da-78d1-acaa-4cd684a08786"


@pytest.fixture
def live_driver(tmp_path, monkeypatch):
    lease = {
        "session_id": "supervisor-fixture", "lease_id": "lease-fixture",
        "generation": 2, "fencing_token": 3, "state": "active",
        "holder": {"agent": "codex", "process_id": 1234},
    }
    environment = {
        "SESSION_STREAM_SESSION_ID": lease["session_id"],
        "SESSION_STREAM_LEASE_ID": lease["lease_id"],
        "SESSION_STREAM_GENERATION": "2", "SESSION_STREAM_FENCING_TOKEN": "3",
    }
    rollout = tmp_path / f"rollout-fixture-{THREAD}.jsonl"
    rollout.write_text(json.dumps({
        "type": "session_meta", "payload": {"id": THREAD, "cwd": str(tmp_path)},
    }) + "\n", encoding="utf-8")
    child = Mock()
    child.name.return_value = "codex"
    child.environ.return_value = environment
    child.open_files.return_value = [SimpleNamespace(path=str(rollout))]
    root = Mock()
    root.name.return_value = "bash"
    root.children.return_value = [child]
    process = Mock(return_value=root)
    monkeypatch.setattr(psutil, "Process", process)
    remote = Mock(spec=["stream"])
    remote.stream.return_value = {"lease": lease}
    return lease, environment, rollout, child, root, process, remote


def _wake(service, remote, events, run):
    return watch.wake_driver_once(
        service, remote, stream_id="epic:123", launcher=Path("start-codex-driver.sh"),
        epic="fixture", run=run, inbox_events=events,
    )


def test_unread_message_resumes_exact_live_thread_without_launcher(live_driver, monkeypatch, tmp_path):
    lease, environment, _, _, _, process, remote = live_driver
    before = deepcopy(lease)
    event = watch.InboxEvent(7, "fixture-sender", "request-fixture", "Please reconcile the pending work.")
    launcher = Mock(side_effect=AssertionError("second launcher forbidden"))
    # Even success must contain turn evidence, rather than only a zero exit code.
    def resume(argv, **kwargs):
        assert argv == ["codex", "exec", "resume", "--json", "--disable", "apps", THREAD, "-"]
        assert kwargs["cwd"] == str(tmp_path)
        assert kwargs["env"] == environment
        assert "Message #7 from fixture-sender, request request-fixture:" in kwargs["input"]
        assert event.content in kwargs["input"]
        assert kwargs["input"].startswith("Bridge-ID: inbox-7-7\n")
        return subprocess.CompletedProcess(argv, 0, stdout='{"type":"turn.started"}\n{"type":"turn.completed"}\n', stderr="")

    monkeypatch.setattr(ui.subprocess, "run", resume)
    monkeypatch.setattr(ui, "find_session_file", lambda _: None)
    service = Mock()
    assert _wake(service, remote, [event], launcher)
    launcher.assert_not_called()
    process.assert_called_once_with(1234)
    assert lease == before
    assert remote.method_calls == [call.stream("epic:123"), call.stream("epic:123")]
    assert service.method_calls == []  # No delivery acknowledgment or lease mutation.


@pytest.mark.parametrize("damage", ["wrong-envelope", "ambiguous", "missing", "invalid-metadata", "not-codex", "dead"])
def test_thread_discovery_fails_closed(live_driver, damage, tmp_path):
    lease, environment, rollout, child, root, process, _ = live_driver
    if damage == "wrong-envelope":
        environment["SESSION_STREAM_LEASE_ID"] = "other-lease"
    elif damage == "ambiguous":
        other = tmp_path / "rollout-other.jsonl"
        other.write_text(json.dumps({
            "type": "session_meta", "payload": {"id": "00000000-0000-0000-0000-000000000001", "cwd": str(tmp_path)},
        }) + "\n", encoding="utf-8")
        child.open_files.return_value.append(SimpleNamespace(path=str(other)))
    elif damage == "missing":
        child.open_files.return_value = []
    elif damage == "invalid-metadata":
        rollout.write_text("{}\n", encoding="utf-8")
    elif damage == "not-codex":
        child.name.return_value = "claude"
    else:
        process.side_effect = psutil.NoSuchProcess(1234)
    assert ui.find_live_session(lease) is None
    if damage != "dead":
        root.children.assert_called_once_with(recursive=True)


def test_missing_thread_never_falls_back_to_launcher(live_driver, monkeypatch):
    *_, remote = live_driver
    monkeypatch.setattr(ui, "find_live_session", lambda _: None)
    launch = Mock()
    with pytest.raises(RuntimeError, match="live Codex thread unavailable"):
        _wake(Mock(), remote, [watch.InboxEvent(1, "sender", "request", "pending")], launch)
    launch.assert_not_called()


@pytest.mark.parametrize("exit_code,events", [
    (1, [{"type": "turn.started"}]), (-1, []), (0, []),
    (0, [{"type": "turn.started"}, {"type": "turn.completed"}, {"type": "error"}]),
])
def test_resume_failure_retains_message_without_launcher(live_driver, monkeypatch, exit_code, events):
    *_, remote = live_driver
    send = Mock(return_value={"exit_code": exit_code, "events": events})
    monkeypatch.setattr(ui, "send", send)
    launch = Mock()
    service = Mock()
    with pytest.raises(RuntimeError, match="inbox retained"):
        _wake(service, remote, [watch.InboxEvent(1, "sender", "request", "pending")], launch)
    send.assert_called_once()
    launch.assert_not_called()
    assert service.method_calls == []


def test_lease_rollover_between_discovery_and_send_refuses_turn(live_driver, monkeypatch):
    lease, *_, remote = live_driver
    changed = {**lease, "generation": 4}
    remote.stream.side_effect = [{"lease": lease}, {"lease": changed}]
    send = Mock()
    monkeypatch.setattr(ui, "send", send)
    launch = Mock()
    assert not _wake(Mock(), remote, [watch.InboxEvent(1, "sender", "request", "pending")], launch)
    send.assert_not_called()
    launch.assert_not_called()


@pytest.fixture
def inbox_db(tmp_path):
    path = tmp_path / "messages.db"
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE messages (id INTEGER, from_llm TEXT, to_llm TEXT, task_id TEXT, content TEXT, consumed_by_live_driver INTEGER)")
        conn.execute("INSERT INTO messages VALUES (7, 'sender', 'codex', 'fixture', 'unread payload', 0)")
        conn.execute("INSERT INTO messages VALUES (8, 'sender', 'claude', 'fixture', 'other seat', 0)")
        conn.execute("INSERT INTO messages VALUES (9, 'sender', 'codex', 'fixture', 'consumed payload', 1)")
    return path


def test_wake_mode_off_only_notifies(inbox_db, tmp_path, monkeypatch):
    output = io.StringIO()
    send = Mock(side_effect=AssertionError("notification mode cannot resume"))
    launch = Mock(side_effect=AssertionError("notification mode cannot launch"))
    monkeypatch.setattr(ui, "send", send)
    monkeypatch.setattr(watch, "wake_driver_once", launch)
    monkeypatch.setattr("scripts.ai_agent_bridge._ask_lifecycle.run_ask_watchdog", lambda: None)
    assert watch.run_watcher("codex", db_path=inbox_db, lock_dir=tmp_path / "locks", output=output, once=True) == 7
    assert "id=7" in output.getvalue()
    assert "id=8" not in output.getvalue() and "id=9" not in output.getvalue()
    send.assert_not_called()
    launch.assert_not_called()
    with sqlite3.connect(inbox_db) as conn:
        assert conn.execute("SELECT consumed_by_live_driver FROM messages WHERE id=7").fetchone() == (0,)


def test_explicit_wake_watcher_delivers_once_without_ack(inbox_db, live_driver, monkeypatch):
    *_, remote = live_driver
    monkeypatch.setattr(watch._config, "DB_PATH", inbox_db)
    service = Mock()
    service.store.connection.execute.return_value.fetchall.return_value = []
    service.__enter__ = Mock(return_value=service)
    service.__exit__ = Mock(return_value=False)
    monkeypatch.setattr("scripts.fleet_comms.authority.AuthorityService", lambda: service)
    monkeypatch.setattr("scripts.session_supervisor.remote.RemoteEpicClient", lambda: remote)
    lock = Mock()
    monkeypatch.setattr(watch, "acquire_watcher_lock", lambda _: lock)
    send = Mock(return_value={"exit_code": 0, "events": [{"type": "turn.started"}, {"type": "turn.completed"}]})
    monkeypatch.setattr(ui, "send", send)
    def selector(argv, **kwargs):
        assert argv[0] == "bash"  # Only the read-only stream selector may run.
        return SimpleNamespace(stdout="epic:123\n")
    monkeypatch.setattr(watch.subprocess, "run", selector)
    sleeps = Mock(side_effect=[None, OSError("stop fixture loop")])
    monkeypatch.setattr(watch.time, "sleep", sleeps)
    with pytest.raises(OSError, match="stop fixture loop"):
        watch.run_supervisory_wake_watcher("codex", "codex", "fixture", interval_seconds=1, once=False)
    send.assert_called_once()
    assert "unread payload" in send.call_args.kwargs["message"]
    assert "other seat" not in send.call_args.kwargs["message"]
    assert "consumed payload" not in send.call_args.kwargs["message"]
    lock.release.assert_called_once()
    with sqlite3.connect(inbox_db) as conn:
        assert conn.execute("SELECT consumed_by_live_driver FROM messages WHERE id=7").fetchone() == (0,)
