"""Focused contract tests for the normal ACP inter-agent transport cutover."""

from __future__ import annotations

import importlib
import threading
import time

import pytest

from scripts.agent_runtime import acpx_discuss, runner
from scripts.agent_runtime.adapters import acpx as acpx_module
from scripts.agent_runtime.adapters.acpx import AcpxKimiShadowAdapter
from scripts.agent_runtime.env_sanitize import build_agent_env
from scripts.agent_runtime.result import Result


def _result(agent: str, response: str = "bounded response") -> Result:
    return Result(
        ok=True,
        agent=agent,
        model="fixture",
        mode="read-only",
        response=response,
        stderr_excerpt=None,
        duration_s=0.01,
        session_id=None,
        rate_limited=False,
        stalled=False,
        returncode=0,
        usage_record={"outcome": "ok", "tokens": 5},
    )


def _active_acp(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LU_ACPX_TRANSPORT", "active")


def test_top_level_runner_uses_canonical_adapter_scope() -> None:
    top_level_runner = importlib.import_module("agent_runtime.runner")
    canonical_acpx = importlib.import_module("scripts.agent_runtime.adapters.acpx")
    with top_level_runner.active_communication_scope(
        source="codex",
        agent="glm",
        target_agent="glm",
    ):
        provenance = canonical_acpx.current_communication_provenance()
        assert provenance is not None
        assert provenance.metadata() == {
            "source": "codex",
            "agent": "glm",
            "via": "acp",
        }


def test_inter_agent_defaults_to_acp_and_seals_provenance(tmp_path, monkeypatch) -> None:
    _active_acp(monkeypatch)
    observed: dict[str, object] = {}

    def fake_direct(agent: str, _prompt: str, **kwargs) -> Result:
        observed["agent"] = agent
        observed["kwargs"] = kwargs
        observed["runner_provenance"] = runner._INTER_AGENT_TRANSPORT.get()
        observed["adapter_provenance"] = acpx_module.current_communication_provenance()
        return _result(agent)

    monkeypatch.setattr(runner, "_invoke_direct_only", fake_direct)

    result = runner.invoke_inter_agent(
        "GROK",
        "Compare the two bounded choices.",
        cwd=tmp_path,
        task_id="task-6159",
        correlation_id="corr-6159",
        idempotency_key="idem-6159",
        source="Codex",
    )

    assert observed["agent"] == "acpx-grok-shadow"
    kwargs = observed["kwargs"]
    assert isinstance(kwargs, dict)
    assert kwargs["entrypoint"] == "acpx-transport"
    assert kwargs["tool_config"] == {
        "acpx_transport": True,
        "target_agent": "grok",
        "correlation_id": "corr-6159",
        "idempotency_key": "idem-6159",
    }
    assert observed["runner_provenance"].metadata() == {
        "source": "codex",
        "agent": "grok",
        "via": "acp",
    }
    assert observed["adapter_provenance"].metadata() == result.transport_metadata
    assert result.transport_metadata == {
        "source": "codex",
        "agent": "grok",
        "via": "acp",
    }
    assert result.transport_outcome == "ok"
    assert result.usage_record["transport"] == result.transport_metadata


def test_inter_agent_refuses_unsupported_or_bridge_without_legacy_fallback(tmp_path, monkeypatch) -> None:
    _active_acp(monkeypatch)
    calls: list[str] = []
    monkeypatch.setattr(runner, "_invoke_direct_only", lambda *_a, **_k: calls.append("acp"))
    monkeypatch.setattr(runner, "invoke", lambda *_a, **_k: calls.append("legacy"))

    kwargs = {
        "cwd": tmp_path,
        "task_id": "task-6159",
        "correlation_id": "corr-6159",
        "idempotency_key": "idem-6159",
        "source": "codex",
    }
    with pytest.raises(runner.InterAgentTransportError, match="unsupported"):
        runner.invoke_inter_agent("not-a-seat", "prompt", **kwargs)
    with pytest.raises(runner.InterAgentTransportError, match="only 'acp'"):
        runner.invoke_inter_agent("grok", "prompt", transport="bridge", **kwargs)

    monkeypatch.setenv("LU_ACPX_TRANSPORT", "off")
    with pytest.raises(runner.InterAgentTransportError, match="unavailable"):
        runner.invoke_inter_agent("grok", "prompt", **kwargs)

    assert calls == []


def test_inter_agent_rejects_spoofed_provenance_and_unknown_source_before_spawn(
    tmp_path,
    monkeypatch,
) -> None:
    _active_acp(monkeypatch)
    spawned: list[bool] = []
    monkeypatch.setattr(runner, "_invoke_direct_only", lambda *_a, **_k: spawned.append(True))
    for variable in (
        "SESSION_HANDOFF_AGENT",
        "CODEX_THREAD_ID",
        "CODEX_SESSION",
        "CLAUDE_AGENT_NAME",
        "GROK_AGENT",
        "GEMINI_SESSION",
    ):
        monkeypatch.delenv(variable, raising=False)

    kwargs = {
        "cwd": tmp_path,
        "task_id": "task-6159",
        "correlation_id": "corr-6159",
        "idempotency_key": "idem-6159",
    }
    with pytest.raises(runner.InterAgentTransportError, match="runner-sealed"):
        runner.invoke_inter_agent(
            "grok",
            "prompt",
            source="codex",
            metadata={"Source": "forged"},
            **kwargs,
        )
    with pytest.raises(runner.InterAgentTransportError, match="trusted initiating Source"):
        runner.invoke_inter_agent("grok", "prompt", **kwargs)

    assert spawned == []


def test_inter_agent_does_not_forward_or_return_raw_credentials(tmp_path, monkeypatch) -> None:
    _active_acp(monkeypatch)
    secret = "secret-value-never-for-acp-result"
    monkeypatch.setenv("OPENAI_API_KEY", secret)
    captured: dict[str, object] = {}

    def fake_direct(agent: str, _prompt: str, **kwargs) -> Result:
        captured["agent"] = agent
        captured["kwargs"] = kwargs
        return _result(agent)

    monkeypatch.setattr(runner, "_invoke_direct_only", fake_direct)
    result = runner.invoke_inter_agent(
        "grok",
        "Prompt text has no credential.",
        cwd=tmp_path,
        task_id="task-6159",
        correlation_id="corr-6159",
        idempotency_key="idem-credential-boundary",
        source="codex",
    )

    assert secret not in repr(captured)
    assert secret not in repr(result)
    assert secret not in repr(result.usage_record)


def test_adapter_transport_metadata_and_auth_selector_are_non_secret(tmp_path, monkeypatch) -> None:
    _active_acp(monkeypatch)
    secret = "moonshot-secret-must-not-leak"
    monkeypatch.setenv("KIMI_API_KEY", secret)
    monkeypatch.setattr(acpx_module, "_require_non_primary_worktree", lambda *_a, **_k: None)
    monkeypatch.setattr(
        acpx_module,
        "_require_compatible_acpx_binary",
        lambda **_kwargs: (str(tmp_path / "acpx"), "0.13.0"),
    )

    with acpx_module.active_communication_scope(
        source="codex",
        agent="kimi",
        target_agent="kimi",
    ):
        plan = AcpxKimiShadowAdapter().build_invocation(
            prompt="bounded prompt",
            mode="read-only",
            cwd=tmp_path,
            model=None,
            task_id="task-6159",
            session_id=None,
            tool_config={
                "acpx_transport": True,
                "target_agent": "kimi",
                "correlation_id": "corr-6159",
                "idempotency_key": "idem-6159",
            },
        )

    env = build_agent_env(provider="acpx-kimi-shadow", overrides=plan.env_overrides)
    assert plan.metadata["source"] == "codex"
    assert plan.metadata["agent"] == "kimi"
    assert plan.metadata["via"] == "acp"
    assert plan.metadata["acpx_discussion"] is False
    assert plan.metadata["acpx_transport"] is True
    assert plan.env_overrides == {"ACPX_AUTH_LOGIN": "1"}
    assert env["ACPX_AUTH_LOGIN"] == "1"
    assert "KIMI_API_KEY" not in env
    assert secret not in repr(plan)
    assert secret not in repr(env)


def test_adapter_extra_metadata_cannot_override_runner_sealed_provenance(tmp_path, monkeypatch) -> None:
    _active_acp(monkeypatch)
    monkeypatch.setattr(acpx_module, "_require_non_primary_worktree", lambda *_a, **_k: None)
    monkeypatch.setattr(
        acpx_module,
        "_require_compatible_acpx_binary",
        lambda **_kwargs: (str(tmp_path / "acpx"), "0.13.0"),
    )

    class SpoofingAdapter(AcpxKimiShadowAdapter):
        def _extra_metadata(self):
            return {"source": "forged", "agent": "forged", "via": "bridge"}

    with acpx_module.active_communication_scope(
        source="codex",
        agent="kimi",
        target_agent="kimi",
    ):
        plan = SpoofingAdapter().build_invocation(
            prompt="bounded prompt",
            mode="read-only",
            cwd=tmp_path,
            model=None,
            task_id="task-6159",
            session_id=None,
            tool_config={
                "acpx_transport": True,
                "target_agent": "kimi",
                "correlation_id": "corr-6159",
                "idempotency_key": "idem-6159",
            },
        )

    assert {field: plan.metadata[field] for field in ("source", "agent", "via")} == {
        "source": "codex",
        "agent": "kimi",
        "via": "acp",
    }


def test_discussion_uses_normal_transport_for_three_participants_with_pins(
    tmp_path,
    monkeypatch,
) -> None:
    _active_acp(monkeypatch)
    monkeypatch.setattr(acpx_discuss, "classify_repo_path", lambda *_a, **_k: "dispatch_worktree")
    calls: list[tuple[str, dict[str, object]]] = []
    active = 0
    active_max = 0
    lock = threading.Lock()

    def participant(agent: str, _prompt: str, **kwargs) -> Result:
        nonlocal active, active_max
        with lock:
            active += 1
            active_max = max(active_max, active)
        try:
            time.sleep(0.02)
            calls.append((agent, kwargs))
            return _result(agent, f"{agent} response")
        finally:
            with lock:
                active -= 1

    controller = acpx_discuss.AcpxDiscussionController(
        root=tmp_path / "plane",
        participant_call=None,
        synthesis_call=lambda agent, _prompt, **_kwargs: _result(agent, "synthesis"),
    )
    monkeypatch.setattr(acpx_discuss, "invoke_inter_agent", participant)
    try:
        payload = controller.run(
            prompt="Compare the bounded options.",
            cwd=tmp_path,
            task_id="task-6159",
            correlation_id="corr-6159",
            idempotency_key="idem-three-seat",
            rounds=2,
            participants=("claude", "kimicc", "glm"),
            models={"kimicc": "kimi-code/k3", "glm": "glm-5.2"},
            efforts={"glm": "high"},
            source="codex",
        )
    finally:
        controller.close()

    assert payload["state"] == "COMPLETE"
    assert len(payload["participant_outcomes"]) == 6
    assert {agent for agent, _kwargs in calls} == {"claude", "kimicc", "glm"}
    assert len(calls) == 6
    assert active_max <= acpx_discuss.PARTICIPANT_CONCURRENCY
    kimicc_calls = [kwargs for agent, kwargs in calls if agent == "kimicc"]
    glm_calls = [kwargs for agent, kwargs in calls if agent == "glm"]
    assert all(kwargs["model"] == "kimi-code/k3" for kwargs in kimicc_calls)
    assert all(kwargs["model"] == "glm-5.2" for kwargs in glm_calls)
    assert all(kwargs["effort"] == "high" for kwargs in glm_calls)
