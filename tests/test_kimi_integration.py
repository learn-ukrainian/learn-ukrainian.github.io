"""Closed-registry integration coverage for the native Kimi lane."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from scripts.ai_agent_bridge import _ask_contract, _channels, _cli
from scripts.ai_agent_bridge._channels_cli import _cli_available_agent
from scripts.ai_agent_bridge._model import _build_kimi_probe_plan


def test_delegate_accepts_kimi_and_does_not_create_a_fallback_mapping():
    import delegate

    args = delegate.build_parser().parse_args(
        ["dispatch", "--agent", "kimi", "--task-id", "kimi-probe", "--prompt", "noop", "--dry-run"]
    )
    assert args.agent == "kimi"
    from scripts.common.fallback_substitutions import load_dispatch_fallbacks

    assert "kimi" not in load_dispatch_fallbacks(delegate._FALLBACK_SUBS_PATH)


def test_valid_agents_and_cli_registry_include_kimi():
    assert "kimi" in _channels.VALID_AGENTS
    assert _cli_available_agent("kimi") is True


def test_ask_kimi_parser_defaults_to_k3_and_check_model_accepts_kimi():
    parser = _cli._build_parser()
    ask = parser.parse_args(["ask-kimi", "hello", "--task-id", "kimi-ask", "--from", "codex"])
    probe = parser.parse_args(["check-model", "k3", "--agent", "kimi"])

    # --model no longer carries an argparse default: the contract needs to tell
    # "unset" from "explicitly passed" so --to-model/--model conflicts can be
    # detected. The default is applied downstream by resolve_model_selection().
    assert ask.model is None
    assert ask.to_model is None
    assert (
        _ask_contract.resolve_model_selection(
            lane="kimi", to_model=ask.to_model, model=ask.model, default="k3"
        )
        == "k3"
    )
    assert probe.agent == "kimi"
    assert probe.model == "k3"


def test_ask_review_flag_runs_as_normal_ask(monkeypatch):
    # Direct one-round review regime (operator order 2026-08-06): review=True is
    # a normal ask, never a sealed-path refusal. Mutation guard: re-adding the
    # formal_review_requires_sealed_snapshot raise fails this test.
    from scripts.ai_agent_bridge import _acp_compat

    sentinel = object()
    monkeypatch.setattr(_acp_compat, "_run_compat_ask_impl", lambda *a, **k: sentinel)
    result = _acp_compat.run_compat_ask(
        "claude", "hello", task_id="claude-ask", review=True
    )
    assert result is sentinel


def test_the_legacy_kimi_bridge_module_is_gone():
    """Kimi seats never take asks, so the native Kimi ask/process bridge was removed; ask-kimi routes through
    the ACP compat gate and process-kimi refuses before reading the message."""
    import importlib.util

    assert importlib.util.find_spec("scripts.ai_agent_bridge._kimi") is None


def test_kimi_background_worker_refuses_before_any_processor(monkeypatch):
    from scripts.ai_agent_bridge import _ask_lifecycle, _messaging

    monkeypatch.setattr(_messaging, "read_message", lambda *_a, **_k: None)
    with pytest.raises(ValueError, match="KIMI CODING-ONLY"):
        _ask_lifecycle._process_target(12, "kimi", {"new_session": True, "no_timeout": True, "review": True})


def test_check_model_refuses_read_only_native_kimi_probe():
    with pytest.raises(ValueError, match="KIMI CODING-ONLY"):
        _build_kimi_probe_plan("k3")


def test_kimi_trailer_is_accepted():
    from scripts.audit.lint_agent_trailer import _TRAILER_RE

    assert _TRAILER_RE.search("X-Agent: kimi/5326-kimi-lane-onboard\n")
