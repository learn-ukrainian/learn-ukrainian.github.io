"""The retired bridge discussion worker has no ordinary execution path."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from scripts.ai_agent_bridge import _channels, _channels_cli


def test_discuss_uses_acp_and_durable_authority_only(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    for name in (
        "LU_RUNTIME_INITIATOR",
        "LU_RUNTIME_INITIATOR_SOURCE",
        "SESSION_HANDOFF_AGENT",
        "CLAUDE_AGENT_NAME",
        "CODEX_SESSION",
        "GROK_AGENT",
        "GEMINI_SESSION",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(tmp_path / "fleet"))
    monkeypatch.setenv("LU_AGENT_COMM_TRANSPORT", "acp")
    monkeypatch.setenv("CODEX_THREAD_ID", "thread-cutover")
    monkeypatch.setattr(
        _channels,
        "load_channel_context",
        lambda _channel: {"body": "", "revs": {}, "missing": []},
    )
    observed: dict[str, object] = {}

    def fake_discussion(**kwargs):
        observed.update(kwargs)
        return {
            "conversation_id": "conversation_" + "b" * 32,
            "state": "COMPLETE",
            "rounds_completed": 2,
            "synthesis": "done",
        }

    monkeypatch.setattr("agent_runtime.acpx_discuss.run_discussion", fake_discussion)
    monkeypatch.setattr(
        "agent_runtime.runner.invoke",
        lambda *_a, **_k: (_ for _ in ()).throw(
            AssertionError("retired bridge runtime must not execute")
        ),
    )
    args = SimpleNamespace(
        channel="architecture",
        body="Compare.",
        with_agents="codex,claude",
        max_rounds=2,
        review=False,
        models=None,
        efforts=None,
    )
    assert _channels_cli._handle_discuss(args) == 0
    assert observed["participants"] == ("codex", "claude")
    assert observed["source"] == "codex"
    assert "/fleet.html?conversation=" in capsys.readouterr().out


def test_partial_discussion_reports_zero_completed_rounds_not_requested_rounds(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(tmp_path / "fleet"))
    monkeypatch.setenv("LU_AGENT_COMM_TRANSPORT", "acp")
    monkeypatch.setenv("CODEX_THREAD_ID", "thread-partial")
    monkeypatch.setattr(
        _channels,
        "load_channel_context",
        lambda _channel: {"body": "", "revs": {}, "missing": []},
    )
    monkeypatch.setattr(
        "agent_runtime.acpx_discuss.run_discussion",
        lambda **_kwargs: {
            "conversation_id": "conversation_" + "d" * 32,
            "state": "PARTIAL_COMPLETE",
            "rounds_completed": 0,
            "synthesis": None,
        },
    )
    args = SimpleNamespace(
        channel="architecture",
        body="Compare.",
        with_agents="codex,claude",
        max_rounds=2,
        review=False,
        models=None,
        efforts=None,
    )

    assert _channels_cli._handle_discuss(args) == 1

    output = capsys.readouterr().out
    assert "state: PARTIAL_COMPLETE; rounds completed: 0" in output
    assert "rounds: 2" not in output
