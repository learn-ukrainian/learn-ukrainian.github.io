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


def _rollout_text(cwd: Path, *event_payloads: dict) -> str:
    lines = [json.dumps({"type": "session_meta", "payload": {"id": THREAD, "cwd": str(cwd)}})]
    lines.extend(json.dumps({"type": "event_msg", "payload": payload}) for payload in event_payloads)
    return "\n".join(lines) + "\n"


def test_busy_pane_does_not_resume_until_the_open_turn_closes(live_driver, monkeypatch, tmp_path):
    """A rollout with an unmatched task_started is mid-turn. Resume waits."""
    _, _, rollout, _, _, _, remote = live_driver
    rollout.write_text(
        _rollout_text(tmp_path, {"type": "task_started", "turn_id": "turn-open"}),
        encoding="utf-8",
    )
    send = Mock(return_value={"exit_code": 0, "events": [{"type": "turn.started"}, {"type": "turn.completed"}]})
    monkeypatch.setattr(ui, "send", send)
    launch = Mock(side_effect=AssertionError("busy pane must not start a launcher"))
    event = watch.InboxEvent(7, "fixture-sender", "request-fixture", "pending")
    assert not _wake(Mock(), remote, [event], launch)
    send.assert_not_called()
    launch.assert_not_called()

    rollout.write_text(
        _rollout_text(
            tmp_path,
            {"type": "task_started", "turn_id": "turn-open"},
            {"type": "task_complete", "turn_id": "turn-open"},
        ),
        encoding="utf-8",
    )
    assert _wake(Mock(), remote, [event], launch)
    send.assert_called_once()


def test_missing_resume_binary_is_a_retained_inbox_failure(live_driver, monkeypatch):
    *_, remote = live_driver

    def missing(*_args, **_kwargs):
        raise FileNotFoundError("codex")

    monkeypatch.setattr(ui.subprocess, "run", missing)
    monkeypatch.setattr(ui, "find_session_file", lambda _: None)
    launch = Mock(side_effect=AssertionError("missing resume must not start a launcher"))
    with pytest.raises(RuntimeError, match="inbox retained"):
        _wake(Mock(), remote, [watch.InboxEvent(1, "sender", "request", "pending")], launch)
    launch.assert_not_called()


def test_two_unread_messages_coalesce_into_one_turn_in_id_order(live_driver, monkeypatch):
    """One Ready pane, one poll: both rows ride a single resume, older id first."""
    *_, remote = live_driver
    first = watch.InboxEvent(7, "sender-a", "req-a", "first payload")
    second = watch.InboxEvent(8, "sender-b", "req-b", "second payload")
    send = Mock(return_value={"exit_code": 0, "events": [{"type": "turn.started"}, {"type": "turn.completed"}]})
    monkeypatch.setattr(ui, "send", send)
    launch = Mock(side_effect=AssertionError("coalesced wake must not start a launcher"))
    assert _wake(Mock(), remote, [first, second], launch)
    send.assert_called_once()
    launch.assert_not_called()
    message = send.call_args.kwargs["message"]
    assert message.index("Message #7") < message.index("Message #8")
    assert message.index("first payload") < message.index("second payload")
    assert send.call_args.kwargs["bridge_id"] == "inbox-7-8"


def test_rollout_ready_tracks_turn_boundaries(tmp_path):
    path = tmp_path / "rollout-fixture.jsonl"
    path.write_text(_rollout_text(tmp_path), encoding="utf-8")
    assert ui.rollout_is_ready(path)
    path.write_text(
        _rollout_text(tmp_path, {"type": "task_started", "turn_id": "turn-a"}) + "{not-json",
        encoding="utf-8",
    )
    assert not ui.rollout_is_ready(path)
    closed = _rollout_text(
        tmp_path,
        {"type": "task_started", "turn_id": "turn-a"},
        {"type": "turn_aborted", "turn_id": "turn-a"},
        {"type": "turn_started", "turn_id": "turn-b"},
        {"type": "turn_complete", "turn_id": "turn-b"},
    )
    path.write_text(closed + "{partial", encoding="utf-8")
    assert not ui.rollout_is_ready(path)
    path.write_text(
        closed + json.dumps({"type": "event_msg", "payload": {"type": "task_started", "turn_id": "turn-c"}}) + "\n",
        encoding="utf-8",
    )
    assert not ui.rollout_is_ready(path)


def test_resume_receipt_names_thread_exit_and_turn(tmp_path):
    receipt = ui.resume_receipt({
        "thread_id": THREAD,
        "exit_code": 0,
        "events": [{"type": "turn.started", "turn_id": "turn-landed"}, {"type": "turn.completed"}],
        "stderr": "",
    })
    assert receipt["thread_id"] == THREAD
    assert receipt["exit_code"] == 0
    assert receipt["turn_ids"] == ["turn-landed"]
    assert receipt["event_types"] == ["turn.started", "turn.completed"]
    assert "events" not in receipt


def test_wake_watcher_retries_a_busy_pane_without_a_launcher(inbox_db, live_driver, monkeypatch, tmp_path):
    _, _, rollout, _, _, _, remote = live_driver
    rollout.write_text(_rollout_text(tmp_path, {"type": "task_started", "turn_id": "turn-open"}), encoding="utf-8")
    monkeypatch.setattr(watch._config, "DB_PATH", inbox_db)
    service = Mock()
    service.store.connection.execute.return_value.fetchall.return_value = []
    service.__enter__ = Mock(return_value=service)
    service.__exit__ = Mock(return_value=False)
    monkeypatch.setattr("scripts.fleet_comms.authority.AuthorityService", lambda: service)
    monkeypatch.setattr("scripts.session_supervisor.remote.RemoteEpicClient", lambda: remote)
    monkeypatch.setattr(watch, "acquire_watcher_lock", lambda _: Mock())

    def send(**_kwargs):
        assert "task_complete" in rollout.read_text(encoding="utf-8")
        return {"exit_code": 0, "events": [{"type": "turn.started"}, {"type": "turn.completed"}]}

    send = Mock(side_effect=send)
    monkeypatch.setattr(ui, "send", send)

    def selector(argv, **kwargs):
        assert argv[0] == "bash"
        return SimpleNamespace(stdout="epic:123\n")

    monkeypatch.setattr(watch.subprocess, "run", selector)

    def sleep(_seconds):
        if "task_complete" not in rollout.read_text(encoding="utf-8"):
            rollout.write_text(
                _rollout_text(
                    tmp_path,
                    {"type": "task_started", "turn_id": "turn-open"},
                    {"type": "task_complete", "turn_id": "turn-open"},
                ),
                encoding="utf-8",
            )
            return None
        raise OSError("stop fixture loop")

    monkeypatch.setattr(watch.time, "sleep", sleep)
    with pytest.raises(OSError, match="stop fixture loop"):
        watch.run_supervisory_wake_watcher("codex", "codex", "fixture", interval_seconds=1, once=False)
    send.assert_called_once()
    assert "unread payload" in send.call_args.kwargs["message"]


def test_abort_without_id_clears_open_turns(tmp_path):
    from scripts.ai_agent_bridge import _ui_codex as ui
    path = tmp_path / "rollout.jsonl"

    seq1 = _rollout_text(
        tmp_path,
        {"type": "task_started", "turn_id": "turn-a"},
        {"type": "turn_aborted"},
    )
    path.write_text(seq1, encoding="utf-8")
    assert ui.rollout_is_ready(path)


def test_restart_after_abort(tmp_path):
    from scripts.ai_agent_bridge import _ui_codex as ui
    path = tmp_path / "rollout.jsonl"
    seq = _rollout_text(
        tmp_path,
        {"type": "task_started", "turn_id": "turn-a"},
        {"type": "turn_aborted"},
        {"type": "task_started", "turn_id": "turn-b"},
    )
    path.write_text(seq, encoding="utf-8")
    assert not ui.rollout_is_ready(path)  # The last event is task_started


def test_empty_file(tmp_path):
    from scripts.ai_agent_bridge import _ui_codex as ui
    path = tmp_path / "rollout.jsonl"
    path.write_text("", encoding="utf-8")
    assert ui.rollout_is_ready(path)  # Empty file means no lifecycle event found, returns True


def test_malformed_before_event(tmp_path):
    from scripts.ai_agent_bridge import _ui_codex as ui
    path = tmp_path / "rollout.jsonl"
    path.write_text('{"bad json\n' + _rollout_text(
        tmp_path,
        {"type": "turn_complete", "turn_id": "turn-a"}
    ), encoding="utf-8")
    # complete is found first going backwards, so it returns True before hitting the bad json
    assert ui.rollout_is_ready(path)

    # But if bad json is AFTER the event in the file (BEFORE the event going backward):
    seq = _rollout_text(tmp_path, {"type": "turn_complete", "turn_id": "turn-a"})
    path.write_text(seq + '{"bad json\n', encoding="utf-8")
    assert not ui.rollout_is_ready(path)  # Fails closed (BUSY)


def test_invalid_utf8(tmp_path):
    from scripts.ai_agent_bridge import _ui_codex as ui
    path = tmp_path / "rollout.jsonl"
    # Event goes first, then invalid utf-8 at the end (first going backward)
    seq = _rollout_text(tmp_path, {"type": "turn_complete", "turn_id": "turn-a"})
    with path.open("wb") as f:
        f.write(seq.encode("utf-8") + b'{"type": "bad"}\n\xff\xff\n')
    assert not ui.rollout_is_ready(path)


def test_oversized_record(tmp_path):
    from scripts.ai_agent_bridge import _ui_codex as ui
    path = tmp_path / "rollout.jsonl"

    # 1.5 MiB string (exceeds 1 MiB per-line cap)
    large_line = json.dumps({"type": "event_msg", "payload": "a" * (1500 * 1024)}) + "\n"
    seq = _rollout_text(tmp_path, {"type": "turn_complete", "turn_id": "turn-a"})

    # Large line is at the end. Since it exceeds cap, it should be skipped,
    # and the preceding turn_complete should make it READY.
    path.write_text(seq + large_line, encoding="utf-8")
    assert ui.rollout_is_ready(path)


def test_chunk_boundary(tmp_path):
    from scripts.ai_agent_bridge import _ui_codex as ui
    path = tmp_path / "rollout.jsonl"

    padding = "a" * (64 * 1024 - 10)  # Almost one chunk
    pad_line = json.dumps({"type": "padding", "data": padding}) + "\n"

    event_line = json.dumps({"type": "event_msg", "payload": {"type": "task_started", "turn_id": "turn-a"}}) + "\n"

    # The event_line will straddle the 64 KiB boundary when read backwards.
    path.write_text(pad_line + event_line + pad_line, encoding="utf-8")
    assert not ui.rollout_is_ready(path)


def test_cap_reached(tmp_path):
    from scripts.ai_agent_bridge import _ui_codex as ui
    path = tmp_path / "rollout.jsonl"

    # 17 MiB of non-lifecycle events (under 1 MiB each)
    line = json.dumps({"type": "event_msg", "payload": "a" * (500 * 1024)}) + "\n"
    lines = [line] * 35  # 35 * 500 KiB ≈ 17.5 MiB

    # Append a task_complete at the very beginning (beyond the 16 MiB cap from the end)
    seq = _rollout_text(tmp_path, {"type": "turn_complete", "turn_id": "turn-a"})

    path.write_text(seq + "".join(lines), encoding="utf-8")
    # Cap is reached without finding lifecycle event -> fails closed (BUSY)
    assert not ui.rollout_is_ready(path)
