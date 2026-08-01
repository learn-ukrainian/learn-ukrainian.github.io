"""Read-only ACP discussion cutover contracts."""

from __future__ import annotations

from types import SimpleNamespace

from scripts.ai_agent_bridge import _channels_cli


def _args() -> SimpleNamespace:
    return SimpleNamespace(
        channel="architecture",
        body="Compare the bounded options without tools.",
        with_agents="codex,claude",
        max_rounds=2,
        review=False,
        models=None,
        efforts=None,
    )


def test_discuss_rejects_retired_bridge_transport(monkeypatch, capsys) -> None:
    monkeypatch.setenv("LU_AGENT_COMM_TRANSPORT", "bridge")
    assert _channels_cli._handle_discuss(_args()) == 1
    assert "bridge provider transport is retired" in capsys.readouterr().err


def test_discuss_rejects_single_participant_before_provider_call(monkeypatch) -> None:
    monkeypatch.setenv("LU_AGENT_COMM_TRANSPORT", "acp")
    args = _args()
    args.with_agents = "codex"
    called = False

    def fail_provider(**_kwargs):
        nonlocal called
        called = True
        raise AssertionError("provider must not be called")

    monkeypatch.setattr("agent_runtime.acpx_discuss.run_discussion", fail_provider)
    assert _channels_cli._handle_discuss(args) == 1
    assert called is False
