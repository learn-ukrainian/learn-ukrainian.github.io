"""Regression coverage for opt-in detached ``ask-*`` lifecycle visibility."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from ai_agent_bridge import _ask_lifecycle as lifecycle
from ai_agent_bridge._agy import ask_agy
from ai_agent_bridge._cli import _build_parser
from ai_agent_bridge._db import get_db, init_db
from ai_agent_bridge._messaging import send_message


@pytest.fixture
def bridge_db(tmp_path, monkeypatch):
    db_path = tmp_path / "messages.db"
    monkeypatch.setattr("ai_agent_bridge._config.DB_PATH", db_path)
    monkeypatch.setattr("ai_agent_bridge._db.DB_PATH", db_path)
    monkeypatch.setattr(lifecycle, "PID_DIR", tmp_path / "pids")
    monkeypatch.setattr("ai_agent_bridge._broker.PID_DIR", tmp_path / "pids")
    conn = init_db()
    conn.close()
    return db_path


def _send_ask(task_id: str = "task-4837", target: str = "agy") -> int:
    message_id = send_message(
        "Please answer.",
        task_id=task_id,
        msg_type="query",
        from_llm="codex",
        to_llm=target,
        quiet=True,
    )
    lifecycle.register_ask(message_id)
    return message_id


def _status(message_id: int) -> str:
    conn = get_db()
    try:
        row = conn.execute("SELECT status FROM messages WHERE id = ?", (message_id,)).fetchone()
        assert row is not None
        return str(row[0])
    finally:
        conn.close()


def test_background_ask_sends_immediately_and_mocks_detached_spawn(bridge_db, monkeypatch):
    spawn = Mock(return_value=4321)
    monkeypatch.setattr("ai_agent_bridge._agy.launch_background_ask", spawn)

    message_id = ask_agy("Read one file", task_id="task-4837", background=True)

    assert _status(message_id) == "sent"
    spawn.assert_called_once_with(
        message_id,
        "agy",
        {
            "new_session": False,
            "no_timeout": False,
            "review": False,
            "timeout_seconds": 1800,
        },
    )


def test_background_branch_review_agy_refuses_sealed_cf(bridge_db, monkeypatch):
    """AGY sealed formal review is fail-closed before send (#5553 / #5555)."""
    spawn = Mock(return_value=4321)
    monkeypatch.setattr("ai_agent_bridge._agy.launch_background_ask", spawn)

    with pytest.raises(ValueError, match="agy_isolated_review_unsupported"):
        ask_agy(
            "Review the branch.",
            task_id="review-5150",
            review=True,
            review_branch="feature/review",
            background=True,
        )

    spawn.assert_not_called()
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id FROM messages WHERE task_id = ?",
            ("review-5150",),
        ).fetchone()
    finally:
        conn.close()
    assert row is None


def test_launch_background_ask_writes_state_and_uses_detached_popen(bridge_db, monkeypatch, tmp_path):
    message_id = _send_ask()
    monkeypatch.setattr(lifecycle, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(lifecycle, "_WORKER_START_GRACE_S", 0.05)
    monkeypatch.setattr(lifecycle, "_WORKER_POLL_S", 0.01)

    proc = Mock(pid=4321)
    proc.poll.return_value = None  # still running, matching real Popen while alive
    popen = Mock(return_value=proc)
    monkeypatch.setattr(lifecycle.subprocess, "Popen", popen)

    assert lifecycle.launch_background_ask(message_id, "agy", {"no_timeout": False}) == 4321

    assert popen.call_args.kwargs["start_new_session"] is True
    assert popen.call_args.args[0][-3:] == ["process-ask", str(message_id), "agy"]
    state = json.loads((tmp_path / "pids" / f"ask-{message_id}.json").read_text())
    assert state["pid"] == 4321
    assert state["target"] == "agy"
    launch = json.loads((tmp_path / "batch_state" / "asks" / "task-4837" / "launch.json").read_text())
    assert launch["message_id"] == message_id
    assert launch["pid"] == 4321
    assert launch["agent"] == "agy"
    assert launch["harness"] == "agy"
    assert launch["started_at"]


def test_background_exception_writes_well_formed_terminal_record(bridge_db, monkeypatch, tmp_path):
    """A detached exception must leave a crash-safe terminal artifact (#5891)."""
    message_id = _send_ask()
    monkeypatch.setattr(lifecycle, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(lifecycle, "_background_options", lambda *_args: {})
    monkeypatch.setattr(
        lifecycle,
        "_process_target",
        lambda *_args: (_ for _ in ()).throw(RuntimeError("adapter exploded")),
    )

    lifecycle.process_background_ask(message_id, "agy")

    terminal = json.loads((tmp_path / "batch_state" / "asks" / "task-4837" / "terminal.json").read_text())
    assert terminal["rc_or_signal"] == 1
    assert terminal["stage"] == "exception"
    assert terminal["stderr_tail"] == ""
    assert terminal["ended_at"]


def test_background_signal_handler_writes_terminal_record(bridge_db, monkeypatch, tmp_path):
    """SIGTERM is recorded before the detached process exits (#5891)."""
    message_id = _send_ask()
    monkeypatch.setattr(lifecycle, "REPO_ROOT", tmp_path)
    recorder = lifecycle._AskTerminalRecorder(message_id)

    with pytest.raises(SystemExit) as exc_info:
        recorder.signal_handler(lifecycle.signal.SIGTERM, None)

    assert exc_info.value.code == 128 + lifecycle.signal.SIGTERM
    terminal = json.loads((tmp_path / "batch_state" / "asks" / "task-4837" / "terminal.json").read_text())
    assert terminal["rc_or_signal"] == "SIGTERM"
    assert terminal["stage"] == "signal"
    assert terminal["ended_at"]


def test_asks_lists_replied_id_and_filters_task(bridge_db, capsys):
    first = _send_ask("task-a")
    reply_id = send_message(
        "answer",
        task_id="task-a",
        msg_type="response",
        from_llm="agy",
        to_llm="codex",
        quiet=True,
    )
    lifecycle.record_ask_reply(first, reply_id)
    _send_ask("task-b", target="cursor")

    lifecycle.print_asks("task-a")

    output = capsys.readouterr().out
    assert f"{first}  task-a  agy  replied (reply #{reply_id})" in output
    assert "task-b" not in output


def test_asks_marks_dead_launched_worker_without_terminal_as_died_silent(bridge_db, monkeypatch, capsys, tmp_path):
    """A vanished worker cannot remain indefinitely indistinguishable from pending."""
    message_id = _send_ask()
    monkeypatch.setattr(lifecycle, "REPO_ROOT", tmp_path)
    state_dir = tmp_path / "batch_state" / "asks" / "task-4837"
    lifecycle._atomic_write_json(
        state_dir / "launch.json",
        {
            "message_id": message_id,
            "pid": 999_999_999,
            "agent": "opencode",
            "harness": "opencode",
            "model": "grok-4.5",
            "started_at": "2026-07-27T00:00:00+00:00",
        },
    )

    lifecycle.print_asks("task-4837")

    assert "DIED-SILENT (retry recommended)" in capsys.readouterr().out


def test_reply_link_rejects_a_response_for_another_transport(bridge_db):
    message_id = _send_ask(target="agy")
    unrelated_reply = send_message(
        "wrong answer",
        task_id="task-4837",
        msg_type="response",
        from_llm="cursor",
        to_llm="codex",
        quiet=True,
    )

    assert lifecycle.record_ask_reply(message_id, unrelated_reply) is False
    assert _status(message_id) == "sent"


def test_narration_only_reply_is_not_recorded_as_success(bridge_db):
    """Finding 1: thin scaffolding via record_ask_reply is failure, not replied:N.

    A worker that narrates intent and exits 0 must not land as terminal success.
    Verified to fail against pre-fix code (would set replied:… and leave no failed:).
    """
    message_id = _send_ask(target="agy")
    lifecycle.mark_ask_processing(message_id)
    reply_id = send_message(
        "I'll check out the branch and run the tests.",
        task_id="task-4837",
        msg_type="response",
        from_llm="agy",
        to_llm="codex",
        quiet=True,
    )

    assert lifecycle.record_ask_reply(message_id, reply_id) is False
    status = _status(message_id)
    assert status.startswith("failed:"), status
    assert "thin scaffolding" in status
    assert f"replied:{reply_id}" != status


def test_substantive_reply_still_records_as_replied(bridge_db):
    """Usefulness gate must not break legitimate short or structured answers."""
    message_id = _send_ask(target="agy")
    reply_id = send_message(
        "VERDICT: APPROVED\n\nThe wiring test covers the launch path.",
        task_id="task-4837",
        msg_type="response",
        from_llm="agy",
        to_llm="codex",
        quiet=True,
    )

    assert lifecycle.record_ask_reply(message_id, reply_id) is True
    assert _status(message_id) == f"replied:{reply_id}"


def test_detached_timeout_marks_terminal_state_and_next_cli_notice_is_once(bridge_db, monkeypatch, capsys):
    message_id = _send_ask()
    monkeypatch.setattr(lifecycle, "_background_options", lambda *_args: {})
    monkeypatch.setattr(
        lifecycle,
        "_process_target",
        lambda *_args: (_ for _ in ()).throw(TimeoutError("worker timed out")),
    )

    lifecycle.process_background_ask(message_id, "agy")
    assert _status(message_id).startswith("timed-out:")

    lifecycle.maybe_print_timeout_notice()
    assert f"Background ask timed out: #{message_id}" in capsys.readouterr().err
    assert _status(message_id).startswith("timed-out-notified:")

    lifecycle.maybe_print_timeout_notice()
    assert capsys.readouterr().err == ""


@pytest.mark.parametrize(
    "command",
    [
        "ask-claude",
        "ask-codex",
        "ask-gemini",
        "ask-agy",
        "ask-hermes",
        "ask-opencode",
        "ask-pool",
        "ask-glm",
        "ask-gemma",
        "ask-cursor",
        "ask-grok-build",
    ],
)
def test_every_ask_command_accepts_background(command):
    args = _build_parser().parse_args([command, "question", "--task-id", "task-4837", "--background"])
    assert args.background is True


def test_asks_parser_accepts_task_filter():
    args = _build_parser().parse_args(["asks", "--task-id", "task-4837"])
    assert args.task_id == "task-4837"


def _reply_for(message_id: int, *, task_id: str = "task-4837", from_llm: str = "agy") -> int:
    return send_message(
        "answer",
        task_id=task_id,
        msg_type="response",
        from_llm=from_llm,
        to_llm="codex",
        quiet=True,
    )


def _enable_plane(monkeypatch, tmp_path, mode: str) -> None:
    monkeypatch.setenv("FLEET_COMMS_MESSAGE_PLANE", mode)
    monkeypatch.setattr(lifecycle, "_PLANE_ROOT_OVERRIDE", tmp_path / "fleet-comms-v1")


def test_message_plane_off_is_noop_for_register_and_reply(bridge_db, monkeypatch, tmp_path):
    """Default off: no fleet_request_id, reply path unchanged."""
    _enable_plane(monkeypatch, tmp_path, "off")
    message_id = _send_ask()
    assert lifecycle._load_fleet_request_id(message_id) is None
    reply_id = _reply_for(message_id)
    assert lifecycle.record_ask_reply(message_id, reply_id) is True
    assert _status(message_id) == f"replied:{reply_id}"
    assert not (tmp_path / "fleet-comms-v1" / "comms.sqlite3").exists()


def test_message_plane_shadow_does_not_block_legacy_replied(bridge_db, monkeypatch, tmp_path):
    """Shadow records a durable request but never blocks legacy replied."""
    _enable_plane(monkeypatch, tmp_path, "shadow")
    message_id = _send_ask()
    request_id = lifecycle._load_fleet_request_id(message_id)
    assert request_id is not None
    # Incomplete capture must still allow legacy replied under shadow.
    incomplete_stdout = json.dumps({"type": "agent_message", "text": "partial"})
    assert lifecycle.note_ask_plane_capture(
        message_id,
        adapter="agy",
        stdout=incomplete_stdout,
        returncode=0,
    )
    reply_id = _reply_for(message_id)
    assert lifecycle.record_ask_reply(message_id, reply_id) is True
    assert _status(message_id) == f"replied:{reply_id}"


def test_message_plane_dual_write_blocks_reply_when_incomplete(bridge_db, monkeypatch, tmp_path):
    """dual_write refuses record_ask_reply while the durable request is incomplete."""
    _enable_plane(monkeypatch, tmp_path, "dual_write")
    message_id = _send_ask()
    assert lifecycle._load_fleet_request_id(message_id) is not None
    incomplete_stdout = json.dumps({"type": "agent_message", "text": "no terminal"})
    assert lifecycle.note_ask_plane_capture(
        message_id,
        adapter="agy",
        stdout=incomplete_stdout,
        returncode=0,
    )
    reply_id = _reply_for(message_id)
    assert lifecycle.record_ask_reply(message_id, reply_id) is False
    assert _status(message_id) == "sent"


def test_message_plane_dual_write_allows_reply_when_complete(bridge_db, monkeypatch, tmp_path):
    """dual_write projects replied only after proven complete capture."""
    _enable_plane(monkeypatch, tmp_path, "dual_write")
    message_id = _send_ask()
    complete_stdout = "\n".join(
        [
            json.dumps({"type": "agent_message", "text": "done"}),
            json.dumps({"type": "result", "subtype": "success"}),
        ]
    )
    assert lifecycle.note_ask_plane_capture(
        message_id,
        adapter="agy",
        stdout=complete_stdout,
        returncode=0,
    )
    reply_id = _reply_for(message_id)
    assert lifecycle.record_ask_reply(message_id, reply_id) is True
    assert _status(message_id) == f"replied:{reply_id}"


def test_message_plane_import_error_fail_open(bridge_db, monkeypatch, tmp_path):
    """Plane import failures must not break legacy register/reply."""
    _enable_plane(monkeypatch, tmp_path, "dual_write")
    monkeypatch.setattr(lifecycle, "_import_message_plane", lambda: None)
    message_id = _send_ask()
    assert lifecycle._load_fleet_request_id(message_id) is None
    reply_id = _reply_for(message_id)
    assert lifecycle.record_ask_reply(message_id, reply_id) is True
    assert _status(message_id) == f"replied:{reply_id}"


def test_ask_reply_remains_unacked_for_requester(bridge_db, monkeypatch):
    """Ask reply message must remain unacknowledged (acknowledged=0) for the requester (#5773)."""
    ask_id = send_message(
        "Please review this PR",
        task_id="task-5773",
        msg_type="query",
        from_llm="codex",
        to_llm="claude",
        quiet=True,
    )
    lifecycle.register_ask(ask_id)

    mock_result = Mock(
        ok=True,
        response="VERDICT: APPROVED\n\nLooks good.",
        model="claude-sonnet-5",
        effort=None,
    )
    monkeypatch.setattr("ai_agent_bridge._claude.runtime_invoke", Mock(return_value=mock_result))

    from ai_agent_bridge._claude import process_for_claude

    process_for_claude(ask_id)

    conn = get_db()
    try:
        # Outbound ask message TO claude IS acknowledged by worker
        ask_row = conn.execute("SELECT acknowledged FROM messages WHERE id = ?", (ask_id,)).fetchone()
        assert ask_row is not None
        assert ask_row[0] == 1

        # Inbound reply message TO codex IS NOT acknowledged (acknowledged=0)
        reply_row = conn.execute(
            "SELECT id, acknowledged, from_llm, to_llm FROM messages WHERE to_llm = 'codex' AND task_id = 'task-5773'"
        ).fetchone()
        assert reply_row is not None
        assert reply_row[1] == 0
        assert reply_row[2] == "claude"
        assert reply_row[3] == "codex"
    finally:
        conn.close()


def test_background_ask_reply_remains_unacked_for_requester(bridge_db, monkeypatch):
    """Backgrounded ask reply message must remain unacknowledged (acknowledged=0) for requester (#5773)."""
    ask_id = send_message(
        "Background review request",
        task_id="task-5773-bg",
        msg_type="query",
        from_llm="claude-infra",
        to_llm="claude",
        quiet=True,
    )
    lifecycle.register_ask(ask_id)

    mock_result = Mock(
        ok=True,
        response="VERDICT: APPROVED\n\nBackground review complete.",
        model="claude-sonnet-5",
        effort=None,
    )
    monkeypatch.setattr("ai_agent_bridge._claude.runtime_invoke", Mock(return_value=mock_result))
    monkeypatch.setattr(lifecycle, "_background_options", lambda *_args: {})

    lifecycle.process_background_ask(ask_id, "claude")

    conn = get_db()
    try:
        # Outbound ask message IS acknowledged by worker
        ask_row = conn.execute("SELECT acknowledged FROM messages WHERE id = ?", (ask_id,)).fetchone()
        assert ask_row is not None
        assert ask_row[0] == 1

        # Inbound reply message TO claude-infra IS NOT acknowledged
        reply_row = conn.execute(
            "SELECT id, acknowledged, from_llm, to_llm FROM messages WHERE to_llm = 'claude-infra' AND task_id = 'task-5773-bg'"
        ).fetchone()
        assert reply_row is not None
        assert reply_row[1] == 0
        assert reply_row[2] == "claude"
        assert reply_row[3] == "claude-infra"
    finally:
        conn.close()


def test_watchdog_refires_dead_worker_without_clean_terminal_once(bridge_db, monkeypatch, tmp_path):
    """A dead background ask worker with no reply and no clean terminal gets auto-retried once (#5893)."""
    message_id = _send_ask("task-watchdog-1", target="grok")
    monkeypatch.setattr(lifecycle, "REPO_ROOT", tmp_path)
    state_dir = tmp_path / "batch_state" / "asks" / "task-watchdog-1"
    lifecycle._atomic_write_json(
        state_dir / "launch.json",
        {
            "message_id": message_id,
            "pid": 999_999_999,
            "agent": "grok",
            "harness": "grok",
            "model": "grok-3",
            "started_at": lifecycle._now_iso(),
        },
    )

    re_fire_mock = Mock(return_value=1234)
    monkeypatch.setattr(lifecycle, "launch_background_ask", re_fire_mock)

    retried = lifecycle.run_ask_watchdog(message_id)

    assert retried == [message_id]
    re_fire_mock.assert_called_once()
    meta = lifecycle._ask_metadata(lifecycle.fetch_ask_message(message_id, "grok"))
    assert meta.get("auto_retried") is True
    assert "auto-retried" not in meta


def test_watchdog_ignores_clean_terminal_records(bridge_db, monkeypatch, tmp_path):
    """Clean terminal records (rc=0, stage=success) are NOT re-fired by watchdog (#5893)."""
    message_id = _send_ask("task-watchdog-clean", target="grok")
    monkeypatch.setattr(lifecycle, "REPO_ROOT", tmp_path)
    state_dir = tmp_path / "batch_state" / "asks" / "task-watchdog-clean"
    lifecycle._atomic_write_json(
        state_dir / "launch.json",
        {
            "message_id": message_id,
            "pid": 999_999_999,
            "agent": "grok",
            "harness": "grok",
            "model": "grok-3",
            "started_at": lifecycle._now_iso(),
        },
    )
    lifecycle._atomic_write_json(
        state_dir / "terminal.json",
        {
            "rc_or_signal": 0,
            "stage": "success",
            "stderr_tail": "",
            "ended_at": lifecycle._now_iso(),
        },
    )

    re_fire_mock = Mock()
    monkeypatch.setattr(lifecycle, "launch_background_ask", re_fire_mock)

    retried = lifecycle.run_ask_watchdog(message_id)

    assert retried == []
    re_fire_mock.assert_not_called()


def test_watchdog_ignores_already_retried_asks(bridge_db, monkeypatch, tmp_path):
    """An ask that was already auto-retried (accepting kebab-case on read) must NOT be retried again (#5893)."""
    message_id = _send_ask("task-watchdog-retried", target="grok")
    monkeypatch.setattr(lifecycle, "REPO_ROOT", tmp_path)
    state_dir = tmp_path / "batch_state" / "asks" / "task-watchdog-retried"
    lifecycle._atomic_write_json(
        state_dir / "launch.json",
        {
            "message_id": message_id,
            "pid": 999_999_999,
            "agent": "grok",
            "harness": "grok",
            "model": "grok-3",
            "started_at": lifecycle._now_iso(),
        },
    )

    conn = get_db()
    try:
        conn.execute(
            "UPDATE messages SET data = ? WHERE id = ?",
            (json.dumps({"auto-retried": True}), message_id),
        )
        conn.commit()
    finally:
        conn.close()

    re_fire_mock = Mock()
    monkeypatch.setattr(lifecycle, "launch_background_ask", re_fire_mock)

    retried = lifecycle.run_ask_watchdog(message_id)

    assert retried == []
    re_fire_mock.assert_not_called()


def test_watchdog_ignores_stale_launch_records(bridge_db, monkeypatch, tmp_path):
    """Launch records older than 2x recorded hard timeout window are NOT re-fired by watchdog (#5893)."""
    from datetime import UTC, datetime, timedelta

    message_id = _send_ask("task-watchdog-stale", target="grok")
    monkeypatch.setattr(lifecycle, "REPO_ROOT", tmp_path)
    state_dir = tmp_path / "batch_state" / "asks" / "task-watchdog-stale"
    stale_timestamp = (datetime.now(UTC) - timedelta(seconds=3700)).isoformat()
    lifecycle._atomic_write_json(
        state_dir / "launch.json",
        {
            "message_id": message_id,
            "pid": 999_999_999,
            "agent": "grok",
            "harness": "grok",
            "model": "grok-3",
            "started_at": stale_timestamp,
            "timeout_seconds": 1800,
        },
    )

    assert lifecycle.should_auto_retry_ask(message_id) is False
    re_fire_mock = Mock()
    monkeypatch.setattr(lifecycle, "launch_background_ask", re_fire_mock)
    assert lifecycle.run_ask_watchdog(message_id) == []
    re_fire_mock.assert_not_called()


def test_watchdog_retries_fresh_launch_records(bridge_db, monkeypatch, tmp_path):
    """Launch records within 2x hard timeout window ARE retried by watchdog (#5893)."""
    from datetime import UTC, datetime, timedelta

    message_id = _send_ask("task-watchdog-fresh", target="grok")
    monkeypatch.setattr(lifecycle, "REPO_ROOT", tmp_path)
    state_dir = tmp_path / "batch_state" / "asks" / "task-watchdog-fresh"
    fresh_timestamp = (datetime.now(UTC) - timedelta(seconds=100)).isoformat()
    lifecycle._atomic_write_json(
        state_dir / "launch.json",
        {
            "message_id": message_id,
            "pid": 999_999_999,
            "agent": "grok",
            "harness": "grok",
            "model": "grok-3",
            "started_at": fresh_timestamp,
            "timeout_seconds": 1800,
        },
    )

    assert lifecycle.should_auto_retry_ask(message_id) is True


def test_watchdog_slow_lane_ask_dead_at_minute_35_is_eligible(bridge_db, monkeypatch, tmp_path):
    """A slow-lane ask dead at minute 35 (2100s) with recorded 1800s timeout IS eligible (2x1800=3600s window)."""
    from datetime import UTC, datetime, timedelta

    message_id = _send_ask("task-watchdog-slow-lane", target="agy")
    monkeypatch.setattr(lifecycle, "REPO_ROOT", tmp_path)
    state_dir = tmp_path / "batch_state" / "asks" / "task-watchdog-slow-lane"
    min35_timestamp = (datetime.now(UTC) - timedelta(seconds=2100)).isoformat()
    lifecycle._atomic_write_json(
        state_dir / "launch.json",
        {
            "message_id": message_id,
            "pid": 999_999_999,
            "agent": "agy",
            "harness": "agy",
            "model": "gemini-3.6-pro",
            "started_at": min35_timestamp,
            "timeout_seconds": 1800,
            "no_timeout": False,
        },
    )

    assert lifecycle.should_auto_retry_ask(message_id) is True


def test_watchdog_legacy_record_uses_fallback(bridge_db, monkeypatch, tmp_path):
    """Legacy launch record lacking timeout_seconds falls back to 2x1800 = 3600s window."""
    from datetime import UTC, datetime, timedelta

    message_id = _send_ask("task-watchdog-legacy", target="grok")
    monkeypatch.setattr(lifecycle, "REPO_ROOT", tmp_path)
    state_dir = tmp_path / "batch_state" / "asks" / "task-watchdog-legacy"

    # Eligible at minute 35 (2100s < 3600s)
    min35_timestamp = (datetime.now(UTC) - timedelta(seconds=2100)).isoformat()
    lifecycle._atomic_write_json(
        state_dir / "launch.json",
        {
            "message_id": message_id,
            "pid": 999_999_999,
            "agent": "grok",
            "harness": "grok",
            "model": "grok-3",
            "started_at": min35_timestamp,
        },
    )
    assert lifecycle.should_auto_retry_ask(message_id) is True

    # Stale at minute 62 (3700s > 3600s)
    min62_timestamp = (datetime.now(UTC) - timedelta(seconds=3700)).isoformat()
    lifecycle._atomic_write_json(
        state_dir / "launch.json",
        {
            "message_id": message_id,
            "pid": 999_999_999,
            "agent": "grok",
            "harness": "grok",
            "model": "grok-3",
            "started_at": min62_timestamp,
        },
    )
    assert lifecycle.should_auto_retry_ask(message_id) is False


def test_watchdog_stale_beyond_own_window_not_eligible(bridge_db, monkeypatch, tmp_path):
    """An ask with recorded timeout of 900s is NOT eligible at 1900s (> 2x900 = 1800s window)."""
    from datetime import UTC, datetime, timedelta

    message_id = _send_ask("task-watchdog-stale-window", target="claude")
    monkeypatch.setattr(lifecycle, "REPO_ROOT", tmp_path)
    state_dir = tmp_path / "batch_state" / "asks" / "task-watchdog-stale-window"
    stale_timestamp = (datetime.now(UTC) - timedelta(seconds=1900)).isoformat()
    lifecycle._atomic_write_json(
        state_dir / "launch.json",
        {
            "message_id": message_id,
            "pid": 999_999_999,
            "agent": "claude",
            "harness": "claude",
            "model": "claude-3-5-sonnet",
            "started_at": stale_timestamp,
            "timeout_seconds": 900,
        },
    )

    assert lifecycle.should_auto_retry_ask(message_id) is False


def test_atomic_retry_claim_prevents_concurrent_refire(bridge_db, monkeypatch, tmp_path):
    """Atomic O_CREAT|O_EXCL retry-claim file ensures exactly one claim succeeds (#5893 item 3)."""
    message_id = _send_ask("task-atomic-claim", target="grok")
    monkeypatch.setattr(lifecycle, "REPO_ROOT", tmp_path)
    state_dir = tmp_path / "batch_state" / "asks" / "task-atomic-claim"
    lifecycle._atomic_write_json(
        state_dir / "launch.json",
        {
            "message_id": message_id,
            "pid": 999_999_999,
            "agent": "grok",
            "harness": "grok",
            "model": "grok-3",
            "started_at": lifecycle._now_iso(),
            "timeout_seconds": 1800,
        },
    )

    # First claim succeeds
    assert lifecycle.claim_ask_retry(message_id) is True
    # Second claim fails
    assert lifecycle.claim_ask_retry(message_id) is False

    # Once claimed, should_auto_retry_ask and _re_fire_ask decline
    assert lifecycle.should_auto_retry_ask(message_id) is False
    assert lifecycle._re_fire_ask(message_id) is False


def test_cancel_and_retell_native_grok_permission_cancelled(bridge_db, monkeypatch, tmp_path):
    """A native Grok turn ending in permission_cancelled auto-retries once with refusal reason (#5893)."""
    from ai_agent_bridge import _grok_build

    monkeypatch.setattr(_grok_build, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(lifecycle, "REPO_ROOT", tmp_path)

    message_id = _send_ask("task-cancel-retell", target="grok")

    mock_invoke_1 = Mock(ok=True, response="I tried running a shell command.", model="grok-3", effort="medium", session_id="session-123")
    mock_invoke_2 = Mock(ok=True, response="Answer based on file content only.", model="grok-3", effort="medium", session_id="session-123")

    invokes = [mock_invoke_1, mock_invoke_2]
    prompts_captured = []

    def fake_invoke(*args, **kwargs):
        prompts_captured.append(args[1])
        return invokes.pop(0)

    monkeypatch.setattr(_grok_build.agent_runner, "invoke", fake_invoke)
    monkeypatch.setattr(
        _grok_build,
        "_native_grok_turn_status",
        Mock(
            side_effect=[
                {"outcome": "cancelled", "cancellation_category": "permission_cancelled"},
                {"outcome": "completed", "cancellation_category": None},
            ]
        ),
    )

    _grok_build.process_for_grok_build(message_id)

    assert len(prompts_captured) == 2
    assert "[Previous turn cancelled by permission policy]: Tool call permission cancelled" in prompts_captured[1]

    conn = get_db()
    try:
        row = conn.execute("SELECT data FROM messages WHERE message_type = 'response' AND task_id = 'task-cancel-retell'").fetchone()
        assert row is not None
        meta = json.loads(row[0])
        assert meta.get("cancel_retried") is True
    finally:
        conn.close()


def test_cancel_and_retell_composes_with_watchdog_within_bound(bridge_db, monkeypatch, tmp_path):
    """Total automatic re-fires for one ask never exceed MAX_TOTAL_ASK_RETRIES = 2 (#5893)."""
    from ai_agent_bridge import _grok_build
    from ai_agent_bridge._ask_contract import MAX_TOTAL_ASK_RETRIES

    assert MAX_TOTAL_ASK_RETRIES == 2

    message_id = _send_ask("task-bound", target="grok")

    conn = get_db()
    try:
        conn.execute(
            "UPDATE messages SET data = ? WHERE id = ?",
            (json.dumps({"total_retry_count": 2, "auto_retried": True}), message_id),
        )
        conn.commit()
    finally:
        conn.close()

    assert lifecycle.should_auto_retry_ask(message_id) is False

    msg = lifecycle.fetch_ask_message(message_id, "grok")
    assert _grok_build._can_cancel_retry(msg) is False


def test_asks_cli_watchdog_flag(bridge_db, monkeypatch, capsys):
    """asks --watchdog executes watchdog and lists asks."""
    from ai_agent_bridge import _cli

    watchdog_mock = Mock(return_value=[])
    monkeypatch.setattr("ai_agent_bridge._ask_lifecycle.run_ask_watchdog", watchdog_mock)

    args = _cli._build_parser().parse_args(["asks", "--watchdog"])
    _cli._dispatch_command(args)

    watchdog_mock.assert_called_once()
    assert "Watchdog run complete" in capsys.readouterr().out


def test_re_fire_ask_inner_claim_admits_exactly_one_caller(bridge_db, monkeypatch, tmp_path):
    """The once-only enforcement point under concurrency is the O_EXCL claim INSIDE
    _re_fire_ask: two callers that both already passed should_auto_retry_ask must
    resolve to exactly one live re-fire. (r3 review mutation check showed the
    pre-created-claim test only covers the outer should_auto_retry_ask decline —
    removing the inner claim left it green.)"""
    message_id = _send_ask("task-claim-inner", target="grok")
    monkeypatch.setattr(lifecycle, "REPO_ROOT", tmp_path)
    state_dir = tmp_path / "batch_state" / "asks" / "task-claim-inner"
    lifecycle._atomic_write_json(
        state_dir / "launch.json",
        {
            "message_id": message_id,
            "pid": 999_999_999,
            "agent": "grok",
            "harness": "grok",
            "model": "grok-3",
            "started_at": "2026-07-27T00:00:00+00:00",
        },
    )
    launches: list[int] = []
    monkeypatch.setattr(
        lifecycle, "launch_background_ask", lambda mid, target, options: launches.append(mid)
    )

    first = lifecycle._re_fire_ask(message_id)
    second = lifecycle._re_fire_ask(message_id)

    assert first is True
    assert second is False, "second concurrent-style caller must lose the O_EXCL claim"
    assert launches == [message_id], "exactly one live re-fire despite two callers"
