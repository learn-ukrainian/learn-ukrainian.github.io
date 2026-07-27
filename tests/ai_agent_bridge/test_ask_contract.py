"""Regression coverage for the uniform ask model/effort/provenance contract."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from ai_agent_bridge import _cli
from ai_agent_bridge._ask_contract import (
    EFFORT_CHOICES,
    resolve_model_selection,
    response_provenance,
    unsupported_effort_note,
)

ASK_SEATS = (
    ("ask-claude", "_handle_ask_claude", "ask_claude"),
    ("ask-codex", "_handle_ask_codex", "ask_codex"),
    ("ask-agy", "_handle_ask_agy", "ask_agy"),
    ("ask-grok", "_handle_ask_grok_build", "ask_grok_build"),
    ("ask-glm", "_handle_ask_glm", "ask_glm"),
    ("ask-kimi", "_handle_ask_kimi", "ask_kimi"),
    ("ask-cursor", "_handle_ask_cursor", "ask_cursor"),
    ("ask-hermes", "_handle_ask_hermes", "ask_hermes"),
    ("ask-opencode", "_handle_ask_opencode", "ask_opencode"),
    ("ask-pool", "_handle_ask_pool", "ask_pool"),
    ("ask-gemma", "_handle_ask_gemma", "ask_gemma"),
)


@pytest.mark.parametrize(("command", "handler_name", "adapter_name"), ASK_SEATS)
def test_effort_and_to_model_reach_every_ask_adapter(
    command: str, handler_name: str, adapter_name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every public ask parser forwards both contract controls to its adapter."""
    captured: dict[str, object] = {}

    def fake_adapter(*args, **kwargs):
        captured["args"] = args
        captured.update(kwargs)

    monkeypatch.setattr(_cli, adapter_name, fake_adapter)
    args = _cli._build_parser().parse_args(
        [
            command,
            "question",
            "--task-id",
            "contract-seat",
            "--from",
            "claude",
            "--to-model",
            "requested-model",
            "--effort",
            "xhigh",
        ]
    )

    getattr(_cli, handler_name)(args)

    forwarded = tuple(captured.get("args", ())) + tuple(captured.values())
    assert "requested-model" in forwarded
    assert captured["effort"] == "xhigh"


@pytest.mark.parametrize("effort", EFFORT_CHOICES)
def test_every_contract_effort_value_is_accepted(effort: str) -> None:
    args = _cli._build_parser().parse_args(
        ["ask-codex", "question", "--task-id", "effort-values", "--effort", effort]
    )
    assert args.effort == effort


def test_to_model_wins_only_when_legacy_alias_agrees() -> None:
    assert (
        resolve_model_selection(
            lane="ask-cursor",
            to_model="requested",
            model="requested",
            default="default",
        )
        == "requested"
    )
    with pytest.raises(ValueError, match="conflicts with deprecated --model"):
        resolve_model_selection(
            lane="ask-cursor",
            to_model="requested",
            model="legacy",
            default="default",
        )


def test_unsupported_effort_emits_note_and_stamps_null(capsys: pytest.CaptureFixture[str]) -> None:
    applied, reason = unsupported_effort_note(
        lane="cursor", effort="xhigh", reason="Cursor Agent has no per-invocation effort flag"
    )
    assert applied is None
    assert reason == "Cursor Agent has no per-invocation effort flag"
    assert "NOTE: cursor cannot apply requested effort=xhigh" in capsys.readouterr().out


@pytest.mark.parametrize("harness", [seat[0].removeprefix("ask-") for seat in ASK_SEATS])
def test_every_response_provenance_shape_has_required_fields(harness: str) -> None:
    data, from_model = response_provenance(
        {"data": json.dumps({"to_model": "requested", "effort": "xhigh"})},
        actual_model="actual",
        harness=harness,
        effort_applied="xhigh",
    )
    assert from_model == "actual"
    assert json.loads(data) == {
        "effort_applied": "xhigh",
        "effort_requested": "xhigh",
        "from_model": "actual",
        "harness": harness,
        "model_requested": "requested",
    }


def test_native_ask_tool_contract_present_in_ask_mode_and_absent_otherwise() -> None:
    """Native ask prompt generators include NATIVE_ASK_TOOL_CONTRACT; full drivers do not (#5893)."""
    from ai_agent_bridge._ask_contract import NATIVE_ASK_TOOL_CONTRACT
    from ai_agent_bridge._grok_build import _build_grok_build_prompt
    from ai_agent_bridge._prompts import (
        _build_full_execution_prompt,
        build_agy_prompt,
        build_claude_prompt,
        build_codex_prompt,
    )

    dummy_msg = {"from": "user", "task_id": "test-1", "type": "query", "content": "Hello", "data": None}

    # Ask-mode prompts MUST contain NATIVE_ASK_TOOL_CONTRACT
    assert NATIVE_ASK_TOOL_CONTRACT in _build_grok_build_prompt(dummy_msg)
    assert NATIVE_ASK_TOOL_CONTRACT in build_agy_prompt(dummy_msg)
    assert NATIVE_ASK_TOOL_CONTRACT in build_claude_prompt(dummy_msg)
    assert NATIVE_ASK_TOOL_CONTRACT in build_codex_prompt(dummy_msg)

    # Full driver prompt MUST NOT contain NATIVE_ASK_TOOL_CONTRACT
    full_driver_prompt = _build_full_execution_prompt(dummy_msg, delimiters=None)
    assert NATIVE_ASK_TOOL_CONTRACT not in full_driver_prompt
