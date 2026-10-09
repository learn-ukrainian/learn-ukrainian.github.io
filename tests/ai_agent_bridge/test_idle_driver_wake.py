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
    lease, environment, rollout, _, _, process, remote = live_driver
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
        _append_event(rollout, "task_started", turn_id="resume")
        _append_event(rollout, "task_complete", turn_id="resume")
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
    (0, [{"type": kind} for kind in ["turn.started", "turn.completed"] * 2]),
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
    _, _, rollout, *_, remote = live_driver
    monkeypatch.setattr(watch._config, "DB_PATH", inbox_db)
    service = Mock()
    service.store.connection.execute.return_value.fetchall.return_value = []
    service.__enter__ = Mock(return_value=service)
    service.__exit__ = Mock(return_value=False)
    monkeypatch.setattr("scripts.fleet_comms.authority.AuthorityService", lambda: service)
    monkeypatch.setattr("scripts.session_supervisor.remote.RemoteEpicClient", lambda: remote)
    lock = Mock()
    monkeypatch.setattr(watch, "acquire_watcher_lock", lambda _: lock)
    send = Mock(side_effect=_completed_resume(rollout))
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


def _append_event(rollout, kind, **fields):
    with rollout.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"type": "event_msg", "payload": {"type": kind, **fields}}) + "\n")


def _completed_resume(rollout):
    def send(**kwargs):
        if kwargs.get("before_resume"):
            kwargs["before_resume"]()
        _append_event(rollout, "task_started", turn_id="resume")
        _append_event(rollout, "task_complete", turn_id="resume")
        return {"exit_code": 0, "events": [{"type": "turn.started"}, {"type": "turn.completed"}]}
    return send


def _assert_busy_then_resume(rollout, remote, monkeypatch, closing_kind="task_complete"):
    send = Mock(side_effect=_completed_resume(rollout))
    monkeypatch.setattr(ui, "send", send)
    launch = Mock(side_effect=AssertionError("second launcher forbidden"))
    service = Mock()
    rows = [watch.InboxEvent(1, "sender", "request", "pending")]
    with pytest.raises(RuntimeError, match="codex_wake_busy:"):
        _wake(service, remote, rows, launch)
    send.assert_not_called()
    _append_event(rollout, closing_kind)
    assert _wake(service, remote, rows, launch)
    send.assert_called_once()
    launch.assert_not_called()
    assert service.method_calls == []


@pytest.mark.parametrize("fake", ["payload-id", "nested-envelope"])
def test_regression_d1_oversized_impostor_never_wakes(live_driver, monkeypatch, fake):
    _, _, rollout, *_, remote = live_driver
    _append_event(rollout, "task_started")
    if fake == "payload-id":
        record = {"type": "event_msg", "payload": {"id": "task_complete", "type": "agent_message", "text": "x" * (1024 * 1024 + 1)}}
    else:
        record = {"nested": {"type": "event_msg", "payload": {"type": "task_complete"}}, "type": "response_item", "payload": {"text": "x" * (1024 * 1024 + 1)}}
    with rollout.open("a") as stream:
        stream.write(json.dumps(record) + "\n")
    _assert_busy_then_resume(rollout, remote, monkeypatch)


def test_regression_d2_busy_then_huge_completion_unblocks(live_driver, monkeypatch):
    _, _, rollout, *_, remote = live_driver
    _append_event(rollout, "task_started")
    send = Mock(side_effect=_completed_resume(rollout))
    monkeypatch.setattr(ui, "send", send)
    launch = Mock(side_effect=AssertionError("second launcher forbidden"))
    rows = [watch.InboxEvent(1, "sender", "request", "pending")]
    with pytest.raises(RuntimeError, match="codex_wake_busy:"):
        _wake(Mock(), remote, rows, launch)
    send.assert_not_called()
    with rollout.open("ab") as stream:
        stream.write(b'{"type":"event_msg","payload":{"type":"task_complete","last_agent_message":"')
        for _ in range(17):
            stream.write(b"x" * (1024 * 1024))
        stream.write(b'"}}\n')
    assert _wake(Mock(), remote, rows, launch)
    send.assert_called_once()
    launch.assert_not_called()


def test_regression_d3_final_recheck_observes_new_start(live_driver, monkeypatch):
    lease, _, rollout, *_, remote = live_driver
    _append_event(rollout, "task_complete")
    # Make the append happen precisely during the second lease query.
    calls = 0
    def stream(_):
        nonlocal calls
        calls += 1
        if calls == 2:
            _append_event(rollout, "task_started")
        return {"lease": lease}
    remote.stream.side_effect = stream
    send = Mock(side_effect=_completed_resume(rollout))
    monkeypatch.setattr(ui, "send", send)
    launch = Mock()
    with pytest.raises(RuntimeError, match="codex_wake_busy:start_event"):
        _wake(Mock(), remote, [watch.InboxEvent(1, "sender", "request", "pending")], launch)
    send.assert_not_called()
    launch.assert_not_called()


@pytest.mark.parametrize("record,reason", [
    (b'{"n":' + b"1" * 5000 + b'}\n', "ValueError"),
    (b'{"n":' + b"[" * 2000 + b"0" + b"]" * 2000 + b'}\n', "RecursionError"),
    (b'{"text":"\xff"}\n', "UnicodeDecodeError"),
], ids=["integer", "nesting", "utf8"])
def test_regression_d4_decoder_fault_never_sends(live_driver, monkeypatch, record, reason):
    _, _, rollout, *_, remote = live_driver
    with rollout.open("ab") as stream:
        stream.write(record)
    send = Mock(side_effect=_completed_resume(rollout))
    monkeypatch.setattr(ui, "send", send)
    with pytest.raises(RuntimeError, match=f"codex_wake_busy:decode_error:{reason}"):
        _wake(Mock(), remote, [watch.InboxEvent(1, "sender", "request", "pending")], Mock())
    send.assert_not_called()


def test_regression_d5_partial_start_never_wakes(live_driver, monkeypatch):
    _, _, rollout, *_, remote = live_driver
    with rollout.open("ab") as stream:
        stream.write(b'{"type":"event_msg","payload":{"type":"task_started"}}')
    send = Mock(side_effect=_completed_resume(rollout))
    monkeypatch.setattr(ui, "send", send)
    with pytest.raises(RuntimeError, match="codex_wake_busy:partial_final_line"):
        _wake(Mock(), remote, [watch.InboxEvent(1, "sender", "request", "pending")], Mock())
    send.assert_not_called()


def test_regression_d5_malformed_before_completion_never_wakes(live_driver, monkeypatch):
    _, _, rollout, *_, remote = live_driver
    with rollout.open("ab") as stream:
        stream.write(b'{"broken":}\n')
    _append_event(rollout, "task_complete")
    send = Mock(side_effect=_completed_resume(rollout))
    monkeypatch.setattr(ui, "send", send)
    with pytest.raises(RuntimeError, match="codex_wake_busy:decode_error:"):
        _wake(Mock(), remote, [watch.InboxEvent(1, "sender", "request", "pending")], Mock())
    send.assert_not_called()


def test_regression_d5_idless_abort_allows_completed_restart(live_driver, monkeypatch):
    _, _, rollout, *_, remote = live_driver
    _append_event(rollout, "task_started", turn_id="a")
    _assert_busy_then_resume(rollout, remote, monkeypatch, closing_kind="turn_aborted")
    _append_event(rollout, "task_started", turn_id="b")
    _assert_busy_then_resume(rollout, remote, monkeypatch)


def test_regression_d6_old_unmatched_start_never_wakes(live_driver, monkeypatch):
    _, _, rollout, *_, remote = live_driver
    with rollout.open("ab") as stream:
        stream.write(b'{"timestamp":"2000-01-01T00:00:00Z","type":"event_msg","payload":{"type":"task_started"}}\n')
    _assert_busy_then_resume(rollout, remote, monkeypatch)


def test_final_readiness_check_runs_immediately_before_spawn(live_driver, monkeypatch):
    _, _, rollout, *_, remote = live_driver
    def lookup(_):
        _append_event(rollout, "task_started")
    monkeypatch.setattr(ui, "find_session_file", lookup)
    spawn = Mock(side_effect=AssertionError("must not spawn"))
    monkeypatch.setattr(ui.subprocess, "run", spawn)
    with pytest.raises(RuntimeError, match="codex_wake_busy:start_event"):
        _wake(Mock(), remote, [watch.InboxEvent(1, "sender", "request", "pending")], Mock())
    spawn.assert_not_called()


def test_missing_codex_binary_is_typed_and_retains_inbox(live_driver, monkeypatch):
    *_, remote = live_driver
    monkeypatch.setattr(ui, "find_session_file", lambda _: None)
    monkeypatch.setattr(ui.subprocess, "run", Mock(side_effect=FileNotFoundError("codex")))
    service = Mock()
    with pytest.raises(RuntimeError, match="codex_resume_error:FileNotFoundError; inbox retained"):
        _wake(service, remote, [watch.InboxEvent(1, "sender", "request", "pending")], Mock())
    assert service.method_calls == []


def test_multiple_unread_rows_coalesce_oldest_first(live_driver, monkeypatch):
    _, _, rollout, *_, remote = live_driver
    send = Mock(side_effect=_completed_resume(rollout))
    monkeypatch.setattr(ui, "send", send)
    rows = [watch.InboxEvent(i, "sender", "request", "pending") for i in [3, 1, 2]]
    assert _wake(Mock(), remote, rows, Mock())
    send.assert_called_once()
    message = send.call_args.kwargs["message"]
    assert message.index("Message #1") < message.index("Message #2") < message.index("Message #3")
    assert send.call_args.kwargs["bridge_id"] == "inbox-1-3"


@pytest.mark.parametrize("fault", [ValueError, RecursionError, UnicodeDecodeError, FileNotFoundError, RuntimeError, KeyError])
def test_watcher_survives_any_wake_exception_and_repolls_unread(inbox_db, monkeypatch, capsys, fault):
    monkeypatch.setattr(watch._config, "DB_PATH", inbox_db)
    service = Mock()
    service.__enter__ = Mock(return_value=service)
    service.__exit__ = Mock(return_value=False)
    monkeypatch.setattr("scripts.fleet_comms.authority.AuthorityService", lambda: service)
    monkeypatch.setattr("scripts.session_supervisor.remote.RemoteEpicClient", Mock())
    lock = Mock()
    monkeypatch.setattr(watch, "acquire_watcher_lock", lambda _: lock)
    monkeypatch.setattr(watch.subprocess, "run", Mock(return_value=SimpleNamespace(stdout="epic:123\n")))
    error = UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid") if fault is UnicodeDecodeError else fault("private text must not appear")
    wake = Mock(side_effect=[error, True])
    monkeypatch.setattr(watch, "wake_driver_once", wake)
    monkeypatch.setattr(watch.time, "sleep", Mock(side_effect=[None, OSError("stop fixture loop")]))
    with pytest.raises(OSError, match="stop fixture loop"):
        watch.run_supervisory_wake_watcher("codex", "codex", "fixture", interval_seconds=1, once=False)
    assert wake.call_count == 2
    assert [call.kwargs["inbox_events"][0].message_id for call in wake.call_args_list] == [7, 7]
    diagnostics = capsys.readouterr().err
    assert f"wake_error:{fault.__name__}; inbox retained" in diagnostics
    assert "private text" not in diagnostics
    lock.release.assert_called_once()
    with sqlite3.connect(inbox_db) as conn:
        assert conn.execute("SELECT consumed_by_live_driver FROM messages WHERE id=7").fetchone() == (0,)


def test_missing_rollout_path_never_falls_back_to_launcher(live_driver, tmp_path, monkeypatch):
    *_, remote = live_driver
    monkeypatch.setattr(ui, "find_live_session", lambda _: ui.LiveSession(THREAD, tmp_path, {}))
    send = Mock()
    monkeypatch.setattr(ui, "send", send)
    launch = Mock()
    with pytest.raises(RuntimeError, match="codex_wake_busy:rollout_unavailable"):
        _wake(Mock(), remote, [watch.InboxEvent(1, "sender", "request", "pending")], launch)
    send.assert_not_called()
    launch.assert_not_called()


def test_once_cli_resume_spawn_failure_exits_nonzero_and_retains_inbox(
    inbox_db, live_driver, monkeypatch, capsys,
):
    _, _, rollout, *_, remote = live_driver
    monkeypatch.setattr(watch._config, "DB_PATH", inbox_db)
    service = Mock()
    service.__enter__ = Mock(return_value=service)
    service.__exit__ = Mock(return_value=False)
    monkeypatch.setattr("scripts.fleet_comms.authority.AuthorityService", lambda: service)
    monkeypatch.setattr("scripts.session_supervisor.remote.RemoteEpicClient", lambda: remote)
    lock = Mock()
    monkeypatch.setattr(watch, "acquire_watcher_lock", lambda _: lock)
    monkeypatch.setattr(ui, "find_session_file", lambda _: None)
    spawn = Mock(side_effect=FileNotFoundError("private spawn detail"))
    def run(argv, **kwargs):
        if argv[0] == "bash":
            return SimpleNamespace(stdout="epic:123\n")
        return spawn(argv, **kwargs)
    monkeypatch.setattr(watch.subprocess, "run", run)
    args = ["codex", "--wake-driver", "codex", "--epic", "fixture", "--once"]
    assert watch.main(args) == 2
    spawn.assert_called_once()
    diagnostics = capsys.readouterr().err
    assert "wake_error:codex_resume_error:FileNotFoundError" in diagnostics
    assert "private spawn detail" not in diagnostics
    lock.release.assert_called_once()
    assert service.method_calls == []
    with sqlite3.connect(inbox_db) as conn:
        assert conn.execute("SELECT consumed_by_live_driver FROM messages WHERE id=7").fetchone() == (0,)
    def completed(argv, **kwargs):
        _append_event(rollout, "task_started", turn_id="resume")
        _append_event(rollout, "task_complete", turn_id="resume")
        return subprocess.CompletedProcess(
            argv, 0, stdout='{"type":"turn.started"}\n{"type":"turn.completed"}\n', stderr="",
        )
    spawn.side_effect = completed
    assert watch.main(args) == 0
    assert spawn.call_count == 2
    assert lock.release.call_count == 2
