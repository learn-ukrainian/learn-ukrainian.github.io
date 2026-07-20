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
        {"new_session": False, "no_timeout": False, "review": False},
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

    proc = Mock(pid=4321)
    popen = Mock(return_value=proc)
    monkeypatch.setattr(lifecycle.subprocess, "Popen", popen)

    assert lifecycle.launch_background_ask(message_id, "agy", {"no_timeout": False}) == 4321

    assert popen.call_args.kwargs["start_new_session"] is True
    assert popen.call_args.args[0][-3:] == ["process-ask", str(message_id), "agy"]
    state = json.loads((tmp_path / "pids" / f"ask-{message_id}.json").read_text())
    assert state["pid"] == 4321
    assert state["target"] == "agy"


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
