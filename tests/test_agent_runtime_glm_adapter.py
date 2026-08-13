"""Unit and integration tests for GlmAdapter (opencode CLI hosting glm-5.2)."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import delegate
from agent_runtime import registry
from agent_runtime.adapters import glm
from agent_runtime.adapters.glm import (
    _CI_ENV_VARS,
    GlmAdapter,
    GlmEgressForbiddenError,
)
from agent_runtime.runner import invoke

FAKE_OPENCODE = "/usr/local/bin/opencode"


@pytest.fixture(autouse=True)
def _clear_ci_env(monkeypatch):
    for var in _CI_ENV_VARS:
        monkeypatch.delenv(var, raising=False)


def _build(prompt: str, tmp_path: Path, **kw):
    with patch("agent_runtime.adapters.glm.shutil.which", return_value=FAKE_OPENCODE):
        return GlmAdapter().build_invocation(
            prompt=prompt,
            mode=kw.pop("mode", "read-only"),
            cwd=tmp_path,
            model=kw.pop("model", None),
            task_id=kw.pop("task_id", None),
            session_id=kw.pop("session_id", None),
            tool_config=kw.pop("tool_config", None),
            effort=kw.pop("effort", None),
        )


def test_glm_registry_and_choices_wiring():
    assert "glm" in registry.AGENTS
    entry = registry.get_agent_entry("glm")
    assert entry["cli_available"] is True
    assert entry["default_model"] == "glm-5.2"
    assert entry["default_effort"] == "high"
    assert entry["resume_policy"] == "never"
    assert "glm" in delegate._DISPATCH_AGENT_CHOICES


def test_glm_adapter_basic_argv_construction(tmp_path):
    plan = _build("Analyze code architecture", tmp_path, mode="read-only")
    assert plan.cmd[0] == FAKE_OPENCODE
    assert plan.cmd[1] == "run"
    assert plan.cmd[2] == "--model"
    assert plan.cmd[3] == "zai-coding-plan/glm-5.2"
    assert "--auto" not in plan.cmd
    assert plan.cmd[-2] == "--"
    assert plan.cmd[-1] == "Analyze code architecture"
    assert plan.cwd == tmp_path
    assert plan.env_overrides.get("OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX") == "131072"


def test_glm_adapter_mode_mapping(tmp_path):
    # read-only: no --auto flag
    ro_plan = _build("test prompt", tmp_path, mode="read-only")
    assert "--auto" not in ro_plan.cmd

    # workspace-write: --auto flag included
    ww_plan = _build("test prompt", tmp_path, mode="workspace-write")
    assert "--auto" in ww_plan.cmd

    # danger: --auto flag included
    danger_plan = _build("test prompt", tmp_path, mode="danger")
    assert "--auto" in danger_plan.cmd

    # unsupported mode raises ValueError
    with pytest.raises(ValueError, match="unsupported mode"):
        _build("test prompt", tmp_path, mode="invalid_mode")


def test_glm_adapter_model_override_and_effort(tmp_path):
    plan = _build("Refactor module", tmp_path, model="zai-coding-plan/glm-5.2", effort="high")
    assert plan.cmd[3] == "zai-coding-plan/glm-5.2"
    assert "--variant" in plan.cmd
    variant_idx = plan.cmd.index("--variant")
    assert plan.cmd[variant_idx + 1] == "high"


def test_glm_adapter_omitted_effort_defaults_to_variant_high(tmp_path):
    """Operator 2026-08-13: omitted effort → --variant high."""
    plan = _build("Analyze code", tmp_path)
    assert plan.cmd[plan.cmd.index("--variant") + 1] == "high"


def test_glm_adapter_explicit_effort_max_wins(tmp_path):
    plan = _build("Analyze code", tmp_path, effort="max")
    assert plan.cmd[plan.cmd.index("--variant") + 1] == "max"


def test_glm_adapter_ci_refusal_guard(tmp_path, monkeypatch):
    for var in _CI_ENV_VARS:
        monkeypatch.setenv(var, "1")
        with pytest.raises(GlmEgressForbiddenError, match="refusing to run under"):
            _build("Should fail in CI", tmp_path)
        monkeypatch.delenv(var, raising=False)


def test_glm_ci_guard_mutation_check(tmp_path, monkeypatch):
    """Mutation check: disabling guard allows execution in CI, restoring it blocks."""
    monkeypatch.setenv("CI", "true")

    # 1. Guard active -> raises GlmEgressForbiddenError
    with pytest.raises(GlmEgressForbiddenError):
        _build("Prompt in CI", tmp_path)

    # 2. Disable guard (mutation) -> test fails to raise error (plan constructs)
    with patch.object(glm, "assert_glm_egress_allowed", lambda verb="": None):
        plan = _build("Prompt in CI", tmp_path)
        assert plan.cmd[0] == FAKE_OPENCODE

    # 3. Restore guard -> raises GlmEgressForbiddenError again
    with pytest.raises(GlmEgressForbiddenError):
        _build("Prompt in CI", tmp_path)


def test_glm_adapter_parse_response_success():
    adapter = GlmAdapter()
    result = adapter.parse_response(
        stdout="Analysis complete successfully",
        stderr="",
        returncode=0,
    )
    assert result.ok is True
    assert result.response == "Analysis complete successfully"
    assert result.stderr_excerpt is None
    assert result.rate_limited is False


def test_glm_adapter_parse_response_failure():
    adapter = GlmAdapter()
    result = adapter.parse_response(
        stdout="",
        stderr="opencode: error: connection failed",
        returncode=1,
    )
    assert result.ok is False
    assert result.response == ""
    assert "connection failed" in result.stderr_excerpt
    assert result.rate_limited is False


def test_glm_adapter_parse_response_rate_limit():
    adapter = GlmAdapter()
    result = adapter.parse_response(
        stdout="",
        stderr="429 Too Many Requests: quota exceeded",
        returncode=1,
    )
    assert result.ok is False
    assert result.rate_limited is True


def test_glm_runner_execution_with_fake_opencode_binary(tmp_path, monkeypatch):
    fake_bin = tmp_path / "bin" / "opencode"
    fake_bin.parent.mkdir(parents=True, exist_ok=True)
    fake_bin.write_text("#!/bin/sh\necho 'GLM Output: Verified'\nexit 0\n")
    fake_bin.chmod(0o755)

    monkeypatch.setenv("PATH", f"{fake_bin.parent}:{os.environ.get('PATH', '')}")

    res = invoke(
        "glm",
        "Explain quantum state",
        mode="read-only",
        cwd=tmp_path,
        entrypoint="runtime",
    )

    assert res.ok is True
    assert "GLM Output: Verified" in res.response
    assert res.returncode == 0


def test_glm_runner_execution_failure_path(tmp_path, monkeypatch):
    fake_bin = tmp_path / "bin" / "opencode"
    fake_bin.parent.mkdir(parents=True, exist_ok=True)
    fake_bin.write_text("#!/bin/sh\necho 'Fatal error in opencode' >&2\nexit 2\n")
    fake_bin.chmod(0o755)

    monkeypatch.setenv("PATH", f"{fake_bin.parent}:{os.environ.get('PATH', '')}")

    res = invoke(
        "glm",
        "Test failure path",
        mode="read-only",
        cwd=tmp_path,
        entrypoint="runtime",
    )

    assert res.ok is False
    assert res.returncode == 2
    assert "Fatal error in opencode" in res.stderr_excerpt


def test_glm_delegate_worker_state_lifecycle_success(tmp_path, monkeypatch):
    fake_bin = tmp_path / "bin" / "opencode"
    fake_bin.parent.mkdir(parents=True, exist_ok=True)
    fake_bin.write_text("#!/bin/sh\necho 'Completed task analysis'\nexit 0\n")
    fake_bin.chmod(0o755)

    tasks_dir = tmp_path / "batch_state" / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(delegate, "_TASKS_DIR", tasks_dir)
    monkeypatch.setenv("PATH", f"{fake_bin.parent}:{os.environ.get('PATH', '')}")

    # Write initial state file as cmd_dispatch does
    state_path = delegate._state_path("glm-lifecycle-success")
    delegate._write_state_atomic(
        state_path,
        {
            "task_id": "glm-lifecycle-success",
            "agent": "glm",
            "model": "glm-5.2",
            "mode": "read-only",
            "status": "spawning",
        },
    )

    rc = delegate._run_worker(
        task_id="glm-lifecycle-success",
        agent="glm",
        prompt="Do analysis",
        mode="read-only",
        cwd_str=str(tmp_path),
        model="glm-5.2",
        hard_timeout=300,
        silence_timeout=60,
    )

    assert rc == 0
    state = delegate._read_state(state_path)
    assert state is not None
    assert state["status"] == "done"
    assert state["returncode"] == 0
    assert state["agent"] == "glm"
    assert Path(state["result_file"]).read_text() == "Completed task analysis"


def test_glm_delegate_worker_state_lifecycle_failure(tmp_path, monkeypatch):
    fake_bin = tmp_path / "bin" / "opencode"
    fake_bin.parent.mkdir(parents=True, exist_ok=True)
    fake_bin.write_text("#!/bin/sh\necho 'CLI internal error' >&2\nexit 1\n")
    fake_bin.chmod(0o755)

    tasks_dir = tmp_path / "batch_state" / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(delegate, "_TASKS_DIR", tasks_dir)
    monkeypatch.setenv("PATH", f"{fake_bin.parent}:{os.environ.get('PATH', '')}")

    # Write initial state file as cmd_dispatch does
    state_path = delegate._state_path("glm-lifecycle-failure")
    delegate._write_state_atomic(
        state_path,
        {
            "task_id": "glm-lifecycle-failure",
            "agent": "glm",
            "model": "glm-5.2",
            "mode": "read-only",
            "status": "spawning",
        },
    )

    rc = delegate._run_worker(
        task_id="glm-lifecycle-failure",
        agent="glm",
        prompt="Do analysis",
        mode="read-only",
        cwd_str=str(tmp_path),
        model="glm-5.2",
        hard_timeout=300,
        silence_timeout=60,
    )

    assert rc == 1
    state = delegate._read_state(state_path)
    assert state is not None
    assert state["status"] == "failed"
    assert state["returncode"] == 1
    assert state["agent"] == "glm"
    assert "CLI internal error" in (state.get("stderr_excerpt") or state.get("last_error") or "")
