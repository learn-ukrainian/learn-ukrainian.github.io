"""Routing-guard tests: user spend orders are load-bearing, not prose."""

from __future__ import annotations

import pytest

from scripts.ai_agent_bridge.routing_guard import (
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
        "deepseek-direct/qwen/qwen3.6-plus",
        "deepseek-direct/qwen3.6-plus",
        "deepseek-direct/openai/gpt-5.5",
        "deepseek-direct/gpt-5.5",
        "deepseek-direct/anthropic/claude-sonnet-5",
        "deepseek-direct/claude-sonnet-5",
        "deepseek-direct/google/gemini-3.1-pro-preview",
        "deepseek-direct/gemini-3.1-pro-preview",
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
        "deepseek-direct/deepseek-v4-flash",
        "deepseek-direct/deepseek-v4-pro",
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


def test_hermes_transport_is_wired_and_default_model_allowed(monkeypatch: pytest.MonkeyPatch) -> None:
    """ask-hermes is a NON-opencode transport: it needs its own guard.

    Regression (deepseek review 2026-07-05, finding 1): the hermes lane had a
    qwen default model and no guard — every bare ask-hermes silently burned the
    banned model, and --model could route subscription families via OpenRouter.
    The guard must fire BEFORE send_message (no orphaned bridge messages).
    """
    from scripts.ai_agent_bridge import _hermes

    def _boom(*args, **kwargs):  # pragma: no cover - failure path
        raise AssertionError("send_message must not run for a refused model")

    monkeypatch.setattr(_hermes, "send_message", _boom)
    with pytest.raises(RoutingGuardError):
        _hermes.ask_hermes("hi", task_id="t", model="qwen/qwen3.6-plus")
    with pytest.raises(RoutingGuardError):
        _hermes.ask_hermes("hi", task_id="t", model="openrouter/anthropic/claude-sonnet-5")
    # The shipped default must itself be guard-allowed, or every bare
    # ask-hermes would error out.
    assert_model_routing_allowed(_hermes.HERMES_DEFAULT_MODEL, context="test")
    assert "qwen" not in _hermes.HERMES_DEFAULT_MODEL.lower()


def test_delegate_help_does_not_advertise_qwen() -> None:
    """Banned agent must not appear ANYWHERE in dispatch --help (UX trap:
    --help offers it, the guard rejects it at dispatch). Runs the real parser
    so both argparse choices AND help prose are covered (codex re-review of
    #4500: the first source-check missed a prose mention)."""
    import subprocess
    from pathlib import Path

    repo_root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [str(repo_root / ".venv" / "bin" / "python"), str(repo_root / "scripts" / "delegate.py"), "dispatch", "--help"],
        capture_output=True,
        text=True,
        cwd=repo_root,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    assert "qwen" not in result.stdout.lower()


def test_delegate_dispatch_dry_run_rejects_guarded_model(tmp_path) -> None:
    """Functional interplay check (deepseek finding 3): a banned --model must
    exit 2 with the guard message BEFORE the dry-run task_id prints — proving
    cmd_dispatch actually reaches the guard (late import included)."""
    import subprocess
    from pathlib import Path

    repo_root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [
            str(repo_root / ".venv" / "bin" / "python"),
            str(repo_root / "scripts" / "delegate.py"),
            "dispatch",
            "--agent",
            "codex",
            "--model",
            "openrouter/anthropic/claude-sonnet-5",
            "--task-id",
            "guard-dry-run-test",
            "--prompt",
            "noop",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        cwd=repo_root,
        env={**__import__("os").environ, "LU_ROUTING_GUARD_OVERRIDE": ""},
        timeout=120,
    )
    assert result.returncode == 2, result.stdout + result.stderr
    assert "SUBSCRIPTION family" in result.stderr
    assert "guard-dry-run-test" not in result.stdout
