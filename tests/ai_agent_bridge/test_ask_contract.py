"""Regression coverage for the uniform ask model/effort/provenance contract."""

from __future__ import annotations

import json
import sys
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from ai_agent_bridge import _acp_compat, _cli
from ai_agent_bridge._ask_contract import (
    EFFORT_CHOICES,
    resolve_model_selection,
    response_provenance,
    unsupported_effort_note,
)

ASK_SEATS = (
    ("ask-claude", "_handle_ask_claude", "claude"),
    ("ask-codex", "_handle_ask_codex", "codex"),
    ("ask-agy", "_handle_ask_agy", "agy"),
    ("ask-grok", "_handle_ask_grok_build", "grok"),
    ("ask-glm", "_handle_ask_glm", "glm"),
    ("ask-kimi", "_handle_ask_kimi", "kimi"),
    ("ask-cursor", "_handle_ask_cursor", "cursor"),
    ("ask-hermes", "_handle_ask_hermes", "hermes"),
    ("ask-pool", "_handle_ask_pool", "pool"),
)

RETIRED_ASK_SEATS = (
    ("ask-opencode", "_handle_ask_opencode", "opencode"),
    ("ask-gemma", "_handle_ask_gemma", "gemma"),
)


@pytest.mark.parametrize(("command", "handler_name", "target"), ASK_SEATS)
def test_effort_and_to_model_reach_every_enabled_acp_route(
    command: str, handler_name: str, target: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every enabled compatibility parser forwards controls to the ACP shim."""
    captured: dict[str, object] = {}

    def fake_compat(*args, **kwargs):
        captured["args"] = args
        captured.update(kwargs)
        return SimpleNamespace(ok=True)

    monkeypatch.setattr(_acp_compat, "run_compat_ask", fake_compat)
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
    assert captured["args"][0] == target
    assert "requested-model" in forwarded
    assert captured["effort"] == "xhigh"


def test_terminal_failure_replays_without_invoking_provider_again(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(tmp_path / "fleet-comms"))
    invoke = Mock(side_effect=RuntimeError("protected primary refused"))
    monkeypatch.setattr("agent_runtime.runner.invoke_inter_agent", invoke)

    with pytest.raises(RuntimeError, match="protected primary refused"):
        _acp_compat.run_compat_ask(
            "agy",
            "same prompt",
            task_id="failure-replay",
            source="codex",
            model="gemini-3.6-flash-high",
            effort="high",
        )

    replay = _acp_compat.run_compat_ask(
        "agy",
        "same prompt",
        task_id="failure-replay",
        source="codex",
        model="gemini-3.6-flash-high",
        effort="high",
    )

    assert replay.ok is False
    assert replay.transport_outcome == "error"
    assert replay.usage_record == {"replayed": True, "transport": "acp"}
    assert invoke.call_count == 1


def test_terminalization_conflict_preserves_completed_provider_response(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A bookkeeping collision must not hide the completed provider response."""
    from scripts.fleet_comms.authority import AuthorityStaleLeaseError

    class TerminalConflictAuthority:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def enqueue_request(self, **_kwargs):
            return SimpleNamespace(job_id="job-6367", state="queued")

        def claim_job(self, *_args, **_kwargs):
            return SimpleNamespace(fence_token=1)

        def finish_job(self, *_args, **_kwargs):
            raise AuthorityStaleLeaseError("terminalization_conflict")

    @contextmanager
    def execution_cwd(*_args, **_kwargs):
        yield tmp_path

    provider_result = SimpleNamespace(
        ok=True,
        agent="agy",
        model="gemini-3.6-flash-high",
        response="completed provider response",
        stderr_excerpt=None,
        duration_s=1.0,
        returncode=0,
        effort="high",
        transport_metadata=None,
        transport_outcome="ok",
    )
    invoke = Mock(return_value=provider_result)
    output_path = tmp_path / "response.txt"
    monkeypatch.setattr("scripts.fleet_comms.authority.AuthorityService", TerminalConflictAuthority)
    monkeypatch.setattr("agent_runtime.runner.invoke_inter_agent", invoke)
    monkeypatch.setattr("ai_agent_bridge._acp_execution.acp_execution_cwd", execution_cwd)

    with pytest.raises(RuntimeError, match="terminal bookkeeping failed after provider response"):
        _acp_compat._run_compat_ask_impl(
            "agy",
            "question",
            task_id="terminalization-conflict",
            model="gemini-3.6-flash-high",
            effort="high",
            output_path=str(output_path),
        )

    captured = capsys.readouterr()
    assert captured.out == "completed provider response\n"
    assert "terminalization_conflict" in captured.err
    assert output_path.read_text(encoding="utf-8") == "completed provider response"
    assert invoke.call_count == 1


def test_claim_race_to_terminal_replays_without_invoking_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A terminal race after enqueue must replay instead of spending a provider call."""
    from scripts.fleet_comms.authority import AuthorityServiceError

    replay_result = SimpleNamespace(
        ok=True,
        agent="agy",
        model="gemini-3.6-flash-high",
        response="durably completed response",
        stderr_excerpt=None,
        duration_s=1.0,
        returncode=0,
        effort="high",
        transport_metadata=None,
        transport_outcome="ok",
    )

    class ConcurrentTerminalAuthority:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def enqueue_request(self, **_kwargs):
            return SimpleNamespace(job_id="job-race", state="queued")

        def claim_job(self, *_args, **_kwargs):
            raise AuthorityServiceError("job_not_claimable")

        def get_job(self, _job_id):
            return SimpleNamespace(job_id="job-race", state="complete")

        def read_job_result(self, _job_id):
            return _acp_compat._result_receipt(replay_result)

    invoke = Mock(side_effect=AssertionError("terminal job reinvoked provider"))
    monkeypatch.setattr("scripts.fleet_comms.authority.AuthorityService", ConcurrentTerminalAuthority)
    monkeypatch.setattr("agent_runtime.runner.invoke_inter_agent", invoke)

    result = _acp_compat._run_compat_ask_impl(
        "agy",
        "question",
        task_id="terminal-claim-race",
        model="gemini-3.6-flash-high",
        effort="high",
    )

    assert result.response == "durably completed response"
    assert result.usage_record == {"replayed": True, "transport": "acp"}
    assert invoke.call_count == 0


def test_cli_returns_nonzero_for_replayed_or_live_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        _acp_compat,
        "run_compat_ask",
        lambda *args, **kwargs: SimpleNamespace(ok=False, stderr_excerpt="replayed failure"),
    )
    args = _cli._build_parser().parse_args(
        ["ask-agy", "question", "--task-id", "failed-seat", "--from", "codex"]
    )

    with pytest.raises(SystemExit, match="replayed failure"):
        _cli._handle_ask_agy(args)


@pytest.mark.parametrize(("command", "handler_name", "target"), RETIRED_ASK_SEATS)
def test_ask_target_without_an_enabled_acp_route_fails_closed(
    command: str, handler_name: str, target: str
) -> None:
    args = _cli._build_parser().parse_args(
        [command, "question", "--task-id", "retired-seat"]
    )
    with pytest.raises(SystemExit, match=f"{target!r} has no enabled ACP route"):
        getattr(_cli, handler_name)(args)


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


@pytest.mark.parametrize(
    "harness",
    [seat[0].removeprefix("ask-") for seat in (*ASK_SEATS, *RETIRED_ASK_SEATS)],
)
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
    """Native grok ask prompt includes NATIVE_ASK_TOOL_CONTRACT when not review-provisioned; absent on review-provisioned, reverted builders, and full drivers (#5893)."""
    from ai_agent_bridge._ask_contract import NATIVE_ASK_TOOL_CONTRACT
    from ai_agent_bridge._grok_build import _build_grok_build_prompt
    from ai_agent_bridge._prompts import (
        _build_full_execution_prompt,
        build_agy_prompt,
        build_claude_prompt,
        build_codex_prompt,
    )

    dummy_msg = {"from": "user", "task_id": "test-1", "type": "query", "content": "Hello", "data": None}

    # Present ONLY on native grok ask path without a provisioned review worktree
    assert NATIVE_ASK_TOOL_CONTRACT in _build_grok_build_prompt(dummy_msg, review_worktree_provisioned=False)

    # ABSENT on grok review-provisioned path
    assert NATIVE_ASK_TOOL_CONTRACT not in _build_grok_build_prompt(
        dummy_msg, review=True, review_worktree_provisioned=True
    )

    # ABSENT in the three reverted builders
    assert NATIVE_ASK_TOOL_CONTRACT not in build_agy_prompt(dummy_msg)
    assert NATIVE_ASK_TOOL_CONTRACT not in build_claude_prompt(dummy_msg)
    assert NATIVE_ASK_TOOL_CONTRACT not in build_codex_prompt(dummy_msg)

    # ABSENT in full driver prompt
    full_driver_prompt = _build_full_execution_prompt(dummy_msg, delimiters=None)
    assert NATIVE_ASK_TOOL_CONTRACT not in full_driver_prompt
