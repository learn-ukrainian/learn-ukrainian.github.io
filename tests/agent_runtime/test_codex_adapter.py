from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest

from scripts.agent_runtime.adapters.base import InvocationPlan
from scripts.agent_runtime.adapters.codex import CodexAdapter
from tests.helpers.codex_exec_stream import completed_stream, failed_stream, jsonl, thread_started, turn_started


def test_codex_build_invocation_sends_prompt_via_stdin(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("scripts.agent_runtime.adapters.codex.shutil.which", lambda _: "codex")
    adapter = CodexAdapter()

    plan = adapter.build_invocation(
        prompt="write the module",
        mode="workspace-write",
        cwd=tmp_path,
        model="gpt-6.1-sol",
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


def test_codex_liveness_dirs_include_local_date_midnight_straddle(tmp_path: Path, monkeypatch) -> None:
    adapter = CodexAdapter()
    scoped_home = tmp_path / "codex-home"
    local_rollout_dir = scoped_home / "sessions" / "2026" / "05" / "29"
    local_rollout_dir.mkdir(parents=True)
    utc_now = datetime(2026, 5, 28, 22, 12, tzinfo=UTC)
    local_now = datetime(2026, 5, 29, 0, 12, tzinfo=timezone(timedelta(hours=2)))

    adapter._codex_home_scope = str(scoped_home)
    monkeypatch.setattr(adapter, "_rollout_discovery_times", lambda: (utc_now, local_now))

    assert local_rollout_dir in adapter._candidate_rollout_dirs()
    plan = InvocationPlan(cmd=["codex"], cwd=tmp_path, output_file=tmp_path / "out.txt")
    assert local_rollout_dir in adapter.liveness_signal_paths(plan)


@pytest.mark.parametrize("model", ["gpt-5.6-terra", "gpt-5.5", "gpt-6-sol", "gpt-6-astra", "", "auto"])
def test_codex_rejects_unapproved_model_before_invocation_preparation(tmp_path, monkeypatch, model):
    adapter = CodexAdapter()

    def unexpected_preparation(*_args, **_kwargs):
        pytest.fail("unapproved model reached invocation preparation")

    monkeypatch.setattr("scripts.agent_runtime.adapters.codex.validate_read_only_tmp_root", unexpected_preparation)
    with pytest.raises(ValueError, match=r"model=.*rejected"):
        adapter.build_invocation(
            prompt="test", mode="read-only", cwd=tmp_path, model=model, task_id=None, session_id=None, tool_config=None
        )


@pytest.mark.parametrize("model,expected_model", [(None, "gpt-6.1-sol"), ("gpt-6-luna", "gpt-6-luna")])
@pytest.mark.parametrize("effort,expected", [(None, "high"), ("xhigh", "xhigh")])
def test_codex_pins_gpt6_and_preserves_effort(tmp_path, monkeypatch, model, expected_model, effort, expected):
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
    assert plan.cmd[plan.cmd.index("-m") + 1] == expected_model
    assert any(expected in arg and "model_reasoning_effort" in arg for arg in plan.cmd)


@pytest.mark.parametrize("returncode", [1, -9])
@pytest.mark.parametrize(
    "stdout",
    [
        "",
        jsonl(thread_started(), turn_started()),
        completed_stream(),
    ],
    ids=["no-events", "no-terminal", "completed-then-nonzero-exit"],
)
def test_nonzero_exit_never_returns_partial_output(tmp_path, returncode, stdout):
    """#9532: ``-o`` is written after ``turn.completed``; a nonzero exit that
    was not a verified early reap cannot prove those bytes are complete."""
    output = tmp_path / "last-message.txt"
    output.write_text("arbitrary partial bytes")
    result = CodexAdapter().parse_response(stdout=stdout, stderr="", returncode=returncode, output_file=output)
    assert not result.ok
    assert result.response == ""
    assert not result.rate_limited
    assert result.failure_code == "provider_stream_incomplete"
    assert result.provider_error_text == ""


@pytest.mark.parametrize("content,expected", [("", False), ("final answer", True)])
def test_zero_exit_requires_content(tmp_path, content, expected):
    output = tmp_path / "last-message.txt"
    output.write_text(content)
    result = CodexAdapter().parse_response(stdout=completed_stream(), stderr="", returncode=0, output_file=output)
    assert result.ok is expected


def test_nonzero_quota_failure_is_rate_limited_from_the_stream(tmp_path):
    output = tmp_path / "last-message.txt"
    output.write_text("")
    result = CodexAdapter().parse_response(
        stdout=failed_stream("You\u2019ve hit your usage limit. Try again later."),
        stderr="",
        returncode=1,
        output_file=output,
    )
    assert not result.ok
    assert result.rate_limited
    assert result.failure_code == "rate_limited"


def test_stderr_quota_text_never_classifies(tmp_path):
    """Without typed events the outcome is incomplete, whatever stderr says."""
    output = tmp_path / "last-message.txt"
    output.write_text("")
    result = CodexAdapter().parse_response(
        stdout="", stderr="ERROR: usage limit reached\n", returncode=1, output_file=output
    )
    assert not result.ok
    assert not result.rate_limited
    assert result.failure_code == "provider_stream_incomplete"
    assert "usage limit reached" in result.stderr_excerpt


def test_nonzero_output_file_quota_text_is_agent_text(tmp_path):
    """codex exec never writes a failed turn's error to ``-o`` (#9532)."""
    output = tmp_path / "last-message.txt"
    output.write_text("usage limit reached")
    result = CodexAdapter().parse_response(stdout="", stderr="", returncode=1, output_file=output)
    assert not result.ok
    assert not result.rate_limited


@pytest.mark.parametrize("session_id", [None, "synthetic-session"])
def test_codex_feature_order_and_isolation_history(tmp_path, session_id):
    import inspect

    adapter = CodexAdapter()
    plan = adapter.build_invocation(
        prompt="test", mode="workspace-write", cwd=tmp_path, model=None,
        task_id=None, session_id=session_id,
        tool_config={"disable_features": ["multi_agent", "apps"]},
    )
    try:
        toggles = [(arg, plan.cmd[index + 1]) for index, arg in enumerate(plan.cmd[:-1])
                   if arg in {"--enable", "--disable"}]
        assert toggles.index(("--enable", "multi_agent")) < toggles.index(("--disable", "multi_agent"))
        assert toggles.index(("--enable", "hooks")) < len(toggles) - 1
        assert toggles[-1] == ("--disable", "apps")
        source = inspect.getsource(adapter.build_invocation)
        assert "ORDER MATTERS: Codex CLI processes --enable and --disable" in source
        assert "PR #2230 follow-up" in source
        assert "2026-05-22 ab ask-codex" in source
        assert "codex-node-repl-leak-2026-05-22" in source
        assert "regardless of argv order" not in source
    finally:
        adapter.cleanup_invocation(plan)
        plan.output_file.unlink(missing_ok=True)
