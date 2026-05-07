"""Tier 2 warm-cache fix for ab discuss - closes #1782 sub-task 1."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from ai_agent_bridge import _channels, _cli, _db


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
    return result


def test_discuss_passes_session_id_for_resumable_agents(monkeypatch):
    """Claude + Gemini get a session_id; Codex does not (registry policy)."""
    _channels.create_channel("shared")
    monkeypatch.setattr(_channels, "fetch_monitor_state", lambda: None)
    captured_invokes = []

    def fake_runtime_invoke(agent, _prompt, **kwargs):
        captured_invokes.append((agent, kwargs))
        return _successful_result(agent)

    monkeypatch.setattr("agent_runtime.runner.invoke", fake_runtime_invoke)

    exit_code = _run_cli(
        [
            "discuss",
            "shared",
            "topic",
            "--with",
            "claude,gemini,codex",
            "--max-rounds",
            "2",
        ]
    )

    assert exit_code == 0
    by_agent = {agent: [] for agent in ("claude", "gemini", "codex")}
    for agent, kwargs in captured_invokes:
        by_agent[agent].append(kwargs)

    assert all(len(calls) == 2 for calls in by_agent.values())
    for agent in ("claude", "gemini"):
        first, second = by_agent[agent]
        assert first["session_id"] is not None
        assert second["session_id"] == first["session_id"]
        assert first["tool_config"]["is_new_session"] is True
        assert "is_new_session" not in second["tool_config"]

    for call in by_agent["codex"]:
        assert call["session_id"] is None
        assert "is_new_session" not in call["tool_config"]

    assert all(kwargs["entrypoint"] == "bridge" for _, kwargs in captured_invokes)


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
