"""Routing-guard tests: user spend orders are load-bearing, not prose."""

from __future__ import annotations

import pytest

from scripts.routing_guard import (
    RoutingGuardError,
    assert_agent_routing_allowed,
    assert_model_routing_allowed,
)


@pytest.fixture(autouse=True)
def _no_override(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("LU_ROUTING_GUARD_OVERRIDE", raising=False)


@pytest.mark.parametrize(
    "model",
    [
        "qwen/qwen3.6-plus",
        "openrouter/qwen/qwen3.7-max",
        "qwen3-max",
        "openrouter/anthropic/claude-sonnet-5",
        "openrouter/openai/gpt-5.5",
        "openrouter/google/gemini-3.1-pro-preview",
        "OPENROUTER/ANTHROPIC/CLAUDE-OPUS-4.8",
    ],
)
def test_forbidden_models_refused(model: str) -> None:
    with pytest.raises(RoutingGuardError):
        assert_model_routing_allowed(model, context="test")


@pytest.mark.parametrize(
    "model",
    [
        "openrouter/google/gemma-4-31b-it",  # google/ but NOT gemini — no subscription lane
        "openrouter/deepseek/deepseek-v4-flash",
        "openrouter/deepseek/deepseek-v4-pro",
        "gemini-3.1-pro-high",  # agy NATIVE lane (no openrouter/ prefix) is the subscription path
        "claude-opus-4.8",  # native Anthropic lane
        "gpt-5.5",  # native codex lane
        None,
        "",
    ],
)
def test_allowed_models_pass(model: str | None) -> None:
    assert_model_routing_allowed(model, context="test")


def test_qwen_agent_refused_and_override_env_allows(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(RoutingGuardError):
        assert_agent_routing_allowed("qwen", context="test")
    assert_agent_routing_allowed("codex", context="test")

    monkeypatch.setenv("LU_ROUTING_GUARD_OVERRIDE", "1")
    assert_agent_routing_allowed("qwen", context="test")
    assert_model_routing_allowed("openrouter/anthropic/claude-sonnet-5", context="test")


def test_opencode_transport_is_wired() -> None:
    """The guard must sit at the single opencode subprocess choke point."""
    import inspect

    from scripts.ai_agent_bridge import _opencode

    src = inspect.getsource(_opencode._run_opencode)
    assert "assert_model_routing_allowed" in src


def test_delegate_dispatch_is_wired() -> None:
    from pathlib import Path

    src = Path("scripts/delegate.py").read_text(encoding="utf-8")
    assert "assert_agent_routing_allowed" in src
    assert "assert_model_routing_allowed" in src
