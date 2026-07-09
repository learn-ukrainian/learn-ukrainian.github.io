"""Tier 2 warm-cache fix for ab discuss - closes #1782 sub-task 1."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from ai_agent_bridge import _channels, _channels_cli, _cli, _db


@pytest.fixture(autouse=True)
def isolate_db(tmp_path):
    db_file = tmp_path / "messages.db"
    with patch("ai_agent_bridge._config.DB_PATH", db_file), patch(
        "ai_agent_bridge._db.DB_PATH", db_file
    ):
        _db.init_db()
        yield db_file


def _run_cli(argv: list[str]) -> int:
    with patch.object(sys, "argv", ["ab", *argv]):
        try:
            _cli.main()
        except SystemExit as exc:
            return exc.code if isinstance(exc.code, int) else 0
    return 0


def _successful_result(agent: str) -> MagicMock:
    result = MagicMock()
    result.ok = True
    result.response = f"[reply from {agent}] [AGREE]"
    result.session_id = None
    return result


def test_discuss_passes_session_id_for_resumable_agents(monkeypatch):
    """Claude/AGY get named IDs; Codex reuses the CLI-generated ID."""
    _channels.create_channel("shared")
    monkeypatch.setattr(_channels, "fetch_monitor_state", lambda: None)
    captured_invokes = []

    def fake_runtime_invoke(agent, _prompt, **kwargs):
        captured_invokes.append((agent, kwargs))
        result = _successful_result(agent)
        if agent == "codex":
            result.session_id = "2c8337b6-35da-415d-806d-91d10b5b1381"
        return result

    monkeypatch.setattr("agent_runtime.runner.invoke", fake_runtime_invoke)

    exit_code = _run_cli(
        [
            "discuss",
            "shared",
            "topic",
            "--with",
            "claude,agy,codex",
            "--max-rounds",
            "2",
        ]
    )

    assert exit_code == 0
    by_agent = {agent: [] for agent in ("claude", "agy", "codex")}
    for agent, kwargs in captured_invokes:
        by_agent[agent].append(kwargs)

    assert all(len(calls) == 2 for calls in by_agent.values())
    for agent in ("claude", "agy"):
        first, second = by_agent[agent]
        assert first["session_id"] is not None
        assert second["session_id"] == first["session_id"]
        assert first["tool_config"]["is_new_session"] is True
        assert "is_new_session" not in second["tool_config"]

    first, second = by_agent["codex"]
    assert first["session_id"] is None
    assert second["session_id"] == "2c8337b6-35da-415d-806d-91d10b5b1381"
    assert "is_new_session" not in first["tool_config"]
    assert "is_new_session" not in second["tool_config"]

    assert all(kwargs["entrypoint"] == "bridge" for _, kwargs in captured_invokes)


def test_discuss_acks_its_own_deliveries_on_convergence(monkeypatch, capsys):
    _channels.create_channel("shared")
    monkeypatch.setattr(_channels, "fetch_monitor_state", lambda: None)

    def fake_runtime_invoke(agent, _prompt, **_kwargs):
        return _successful_result(agent)

    monkeypatch.setattr("agent_runtime.runner.invoke", fake_runtime_invoke)

    exit_code = _run_cli(
        ["discuss", "shared", "topic", "--with", "claude,codex", "--max-rounds", "2"]
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "✅ converged at round 2" in captured.out

    conn = _db.get_db()
    try:
        rows = conn.execute(
            """
            SELECT d.status, d.error, d.to_agent, cm.from_agent
            FROM deliveries d
            JOIN channel_messages cm ON cm.message_id = d.message_id
            WHERE cm.channel = 'shared'
            ORDER BY cm.created_at ASC, d.delivery_id ASC
            """
        ).fetchall()
        pending_count = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM deliveries d
            JOIN channel_messages cm ON cm.message_id = d.message_id
            WHERE cm.channel = 'shared' AND d.status = 'pending'
            """
        ).fetchone()["count"]
    finally:
        conn.close()

    assert pending_count == 0
    assert len(rows) == 4
    assert all(row["status"] == "delivered" for row in rows)
    assert all(
        row["error"].startswith("acked by ab discuss orchestrator")
        for row in rows
    )
    assert not any(row["to_agent"] == row["from_agent"] for row in rows)


def test_discuss_entrypoint_is_bridge_not_delegate(monkeypatch):
    """The entrypoint switch is the load-bearing change for the resume policy gate."""
    _channels.create_channel("shared")
    monkeypatch.setattr(_channels, "fetch_monitor_state", lambda: None)
    captured_entrypoints = []

    def fake_runtime_invoke(agent, _prompt, **kwargs):
        captured_entrypoints.append(kwargs["entrypoint"])
        return _successful_result(agent)

    monkeypatch.setattr("agent_runtime.runner.invoke", fake_runtime_invoke)

    exit_code = _run_cli(
        ["discuss", "shared", "topic", "--with", "claude,codex", "--max-rounds", "2"]
    )

    assert exit_code == 0
    assert captured_entrypoints
    assert set(captured_entrypoints) == {"bridge"}


def test_discuss_unknown_agent_defaults_to_no_resume(monkeypatch):
    """Agents not in registry get resume_policy='never' equivalent - no session_id."""
    _channels.create_channel("shared")
    monkeypatch.setattr(_channels, "fetch_monitor_state", lambda: None)
    monkeypatch.setattr(_channels, "VALID_AGENTS", (*_channels.VALID_AGENTS, "mystery"))
    monkeypatch.setattr(
        _channels,
        "VALID_POST_AGENTS",
        (*_channels.VALID_POST_AGENTS, "mystery"),
    )
    # Register `mystery` as cli_available so the new _reject_non_cli_agent gate
    # in _channels_cli (added in this PR) passes. The assertion below still
    # validates the resume-policy fallback for an agent without an explicit
    # resume_policy entry.
    from agent_runtime import registry as _registry
    monkeypatch.setitem(_registry.AGENTS, "mystery", {"cli_available": True})
    captured_invokes = []

    def fake_runtime_invoke(agent, _prompt, **kwargs):
        captured_invokes.append((agent, kwargs))
        return _successful_result(agent)

    monkeypatch.setattr("agent_runtime.runner.invoke", fake_runtime_invoke)

    exit_code = _run_cli(
        ["discuss", "shared", "topic", "--with", "mystery", "--max-rounds", "1"]
    )

    assert exit_code == 0
    assert len(captured_invokes) == 1
    assert captured_invokes[0][0] == "mystery"
    assert captured_invokes[0][1]["session_id"] is None
    assert captured_invokes[0][1]["entrypoint"] == "bridge"


def test_discuss_recovers_cursor_failure_from_session_transcript(
    tmp_path,
    monkeypatch,
):
    _channels.create_channel("shared")
    monkeypatch.setattr(_channels, "fetch_monitor_state", lambda: None)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))

    from agent_runtime.adapters.cursor import CursorAdapter

    session_id = "cursor-session-456"
    encoded = CursorAdapter()._encode_workspace_path(str(_channels_cli.REPO_ROOT))
    transcript = (
        tmp_path
        / ".cursor"
        / "projects"
        / encoded
        / "agent-transcripts"
        / session_id
        / f"{session_id}.jsonl"
    )
    transcript.parent.mkdir(parents=True)
    transcript.write_text(
        (
            '{"role":"assistant","message":{"content":['
            '{"type":"text","text":"Recovered cursor reply [VOTE: D] [AGREE]"},'
            '{"type":"tool_use","name":"Read"}]}}\n'
        ),
        encoding="utf-8",
    )

    def fake_runtime_invoke(agent, _prompt, **_kwargs):
        assert agent == "cursor"
        result = MagicMock()
        result.ok = False
        result.response = ""
        result.session_id = None
        result.stderr_excerpt = f'{{"session_id":"{session_id}"}}'
        return result

    monkeypatch.setattr("agent_runtime.runner.invoke", fake_runtime_invoke)

    exit_code = _run_cli(
        ["discuss", "shared", "topic", "--with", "cursor", "--max-rounds", "2"]
    )

    assert exit_code == 0
    cursor_bodies = [
        message["body"]
        for message in _channels.read("shared")
        if message["from_agent"] == "cursor"
    ]
    assert cursor_bodies
    assert all("Recovered cursor reply [VOTE: D] [AGREE]" in body for body in cursor_bodies)
    assert not any("[failed:" in body for body in cursor_bodies)
