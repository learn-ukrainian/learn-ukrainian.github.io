from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest

from scripts.agent_runtime.adapters.base import InvocationPlan
from scripts.agent_runtime.adapters.codex import CodexAdapter


def test_codex_build_invocation_sends_prompt_via_stdin(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("scripts.agent_runtime.adapters.codex.shutil.which", lambda _: "codex")
    adapter = CodexAdapter()

    plan = adapter.build_invocation(
        prompt="write the module",
        mode="workspace-write",
        cwd=tmp_path,
        model="gpt-6-astra",
        task_id=None,
        session_id=None,
        tool_config=None,
        effort="xhigh",
    )

    assert plan.cwd == tmp_path
    assert plan.stdin_payload == "write the module"
    assert plan.cmd[-1] == "-"


def test_codex_build_invocation_honors_scoped_home(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("scripts.agent_runtime.adapters.codex.shutil.which", lambda _: "codex")
    adapter = CodexAdapter()
    scoped_home = tmp_path / "codex-home"

    plan = adapter.build_invocation(
        prompt="write the module",
        mode="workspace-write",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={"codex_home_override": str(scoped_home)},
        effort=None,
    )

    assert plan.env_overrides["CODEX_HOME"] == str(scoped_home)


def test_codex_rollout_capture_includes_local_date_midnight_straddle(
    tmp_path: Path,
    monkeypatch,
) -> None:
    adapter = CodexAdapter()
    scoped_home = tmp_path / "codex-home"
    local_rollout_dir = scoped_home / "sessions" / "2026" / "05" / "29"
    local_rollout_dir.mkdir(parents=True)
    rollout = local_rollout_dir / "rollout-2026-05-29T00-12-26-test.jsonl"
    prompt = "write the lesson"
    rollout.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "type": "event_msg",
                        "payload": {"type": "user_message", "message": prompt},
                    }
                ),
                json.dumps(
                    {
                        "type": "response_item",
                        "payload": {
                            "type": "function_call",
                            "namespace": "mcp__sources__",
                            "name": "verify_words",
                            "arguments": json.dumps({"words": ["ранок"]}),
                        },
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    output_file = tmp_path / "codex-output.txt"
    output_file.write_text("done", encoding="utf-8")
    utc_now = datetime(2026, 5, 28, 22, 12, tzinfo=UTC)
    local_now = datetime(2026, 5, 29, 0, 12, tzinfo=timezone(timedelta(hours=2)))

    adapter._codex_home_scope = str(scoped_home)
    monkeypatch.setattr(adapter, "_rollout_discovery_times", lambda: (utc_now, local_now))
    adapter._rollout_snapshot = set()

    assert local_rollout_dir in adapter._candidate_rollout_dirs()

    result = adapter.parse_response(
        stdout="",
        stderr="",
        returncode=0,
        output_file=output_file,
        plan=InvocationPlan(cmd=["codex"], cwd=tmp_path, stdin_payload=prompt),
    )

    assert [call["name"] for call in result.tool_calls] == ["mcp__sources__verify_words"]


@pytest.mark.parametrize("model", ["gpt-5.6-terra", "gpt-5.5", "", "auto"])
def test_codex_rejects_unapproved_model_before_state_reset(tmp_path, monkeypatch, model):
    adapter = CodexAdapter()

    def unexpected_reset():
        pytest.fail("unapproved model reached invocation preparation")

    monkeypatch.setattr(adapter, "_reset_per_invocation_state", unexpected_reset)
    with pytest.raises(ValueError, match=r"model=.*rejected"):
        adapter.build_invocation(
            prompt="test", mode="read-only", cwd=tmp_path, model=model, task_id=None, session_id=None, tool_config=None
        )


@pytest.mark.parametrize("model", [None, "gpt-6-astra"])
@pytest.mark.parametrize("effort,expected", [(None, "low"), ("xhigh", "xhigh")])
def test_codex_pins_gpt6_and_preserves_effort(tmp_path, monkeypatch, model, effort, expected):
    monkeypatch.setattr("scripts.agent_runtime.adapters.codex.shutil.which", lambda _: "codex")
    plan = CodexAdapter().build_invocation(
        prompt="test",
        mode="read-only",
        cwd=tmp_path,
        model=model,
        effort=effort,
        task_id=None,
        session_id=None,
        tool_config=None,
    )
    assert plan.cmd[plan.cmd.index("-m") + 1] == "gpt-6-astra"
    assert any(expected in arg and "model_reasoning_effort" in arg for arg in plan.cmd)


@pytest.mark.parametrize("returncode", [1, -9])
@pytest.mark.parametrize("evidence", ["none", "no-terminal", "stale", "foreign", "complete"])
def test_nonzero_exit_requires_matching_terminal_completion(tmp_path, monkeypatch, returncode, evidence):
    adapter = CodexAdapter()
    rollout_dir = tmp_path / "sessions"
    rollout_dir.mkdir()
    monkeypatch.setattr(adapter, "_candidate_rollout_dirs", lambda: [rollout_dir])
    prompt = "current invocation"
    rollout = rollout_dir / "rollout-test.jsonl"
    events = [
        {
            "type": "event_msg",
            "payload": {"type": "user_message", "message": "another invocation" if evidence == "foreign" else prompt},
        },
    ]
    if evidence != "no-terminal":
        events.append(
            {"type": "event_msg", "payload": {"type": "task_complete", "last_agent_message": "Verified final answer"}}
        )
    content = "\n".join(json.dumps(event) for event in events) + "\n"
    if evidence == "stale":
        rollout.write_text(content)
    adapter._reset_per_invocation_state()
    if evidence not in {"none", "stale"}:
        rollout.write_text(content)
    output = tmp_path / "last-message.txt"
    output.write_text("arbitrary partial bytes")
    plan = InvocationPlan(cmd=["codex"], cwd=tmp_path, stdin_payload=prompt)
    result = adapter.parse_response(stdout="", stderr="", returncode=returncode, output_file=output, plan=plan)
    assert result.ok is (evidence == "complete")
    assert result.response == ("Verified final answer" if evidence == "complete" else "")
    assert not result.rate_limited
    if evidence != "complete":
        assert "arbitrary partial bytes" in result.stderr_excerpt


@pytest.mark.parametrize("content,expected", [("", False), ("final answer", True)])
def test_zero_exit_requires_content(tmp_path, content, expected):
    output = tmp_path / "last-message.txt"
    output.write_text(content)
    result = CodexAdapter().parse_response(stdout="", stderr="", returncode=0, output_file=output)
    assert result.ok is expected


def test_nonzero_output_quota_error_remains_rate_limited(tmp_path):
    output = tmp_path / "last-message.txt"
    output.write_text("usage limit reached")
    result = CodexAdapter().parse_response(stdout="", stderr="", returncode=1, output_file=output)
    assert not result.ok
    assert result.rate_limited
