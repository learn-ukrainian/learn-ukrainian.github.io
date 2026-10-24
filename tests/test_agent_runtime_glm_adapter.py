"""Unit and integration tests for GlmAdapter (opencode CLI hosting glm-5.3-flash workhorse)."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import delegate
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


def test_glm_adapter_default_is_refused_after_retirement(tmp_path):
    with pytest.raises(ValueError, match="is retired in the model catalog"):
        _build("Analyze code architecture", tmp_path, mode="read-only")


def test_glm_retirement_binds_every_execution_mode(tmp_path):
    for mode in ("read-only", "workspace-write", "danger"):
        with pytest.raises(ValueError, match="is retired in the model catalog"):
            _build("test prompt", tmp_path, mode=mode)
    with pytest.raises(ValueError, match="unsupported mode"):
        _build("test prompt", tmp_path, mode="invalid_mode")


def test_glm_retirement_cannot_be_bypassed_by_model_override_or_effort(tmp_path):
    with pytest.raises(ValueError, match="is retired in the model catalog"):
        _build("Refactor module", tmp_path, model="glm-5.3", effort="high")


def test_glm_adapter_refuses_retired_openrouter_route(tmp_path):
    with pytest.raises(ValueError, match="is retired in the model catalog"):
        _build("Refactor module", tmp_path, model="openrouter/z-ai/glm-5.3-flash")


def test_glm_retirement_applies_when_effort_is_omitted(tmp_path):
    with pytest.raises(ValueError, match="is retired in the model catalog"):
        _build("Analyze code", tmp_path)


def test_glm_adapter_ci_refusal_guard(tmp_path, monkeypatch):
    for var in _CI_ENV_VARS:
        monkeypatch.setenv(var, "1")
        with pytest.raises(GlmEgressForbiddenError, match="refusing to run under"):
            _build("Should fail in CI", tmp_path)
        monkeypatch.delenv(var, raising=False)


def test_glm_ci_refusal_names_the_variable_never_its_value(tmp_path, monkeypatch):
    for var in _CI_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    sentinel = "https://ci.example.invalid/secret-token-8652"
    monkeypatch.setenv("JENKINS_URL", sentinel)
    with pytest.raises(GlmEgressForbiddenError, match="JENKINS_URL") as refused:
        _build("Should fail in CI", tmp_path)
    assert sentinel not in str(refused.value)


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
    # The adapter forwards stderr unchanged; no installed CLI evidence
    # supports this nested-prefix fixture. Pin the unclassified outcome.
    assert result.failure_code == "provider_stream_incomplete"
    assert result.provider_error_text == ""


def test_glm_adapter_parse_response_rate_limit():
    adapter = GlmAdapter()
    result = adapter.parse_response(
        stdout="",
        stderr="429 Too Many Requests: quota exceeded",
        returncode=1,
    )
    assert result.ok is False
    assert result.rate_limited is True


def test_glm_runner_refuses_retired_default_before_subprocess(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="is retired in the model catalog"):
        invoke("glm", "Analyze code", mode="read-only", cwd=tmp_path, entrypoint="runtime")


def test_glm_runner_refuses_retired_explicit_pin_before_subprocess(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="is retired in the model catalog"):
        invoke("glm", "Analyze code", model="glm-5.3", mode="read-only", cwd=tmp_path, entrypoint="runtime")


def test_glm_delegate_worker_records_retired_pin_as_failed(tmp_path, monkeypatch, capsys):
    fake_bin = tmp_path / "bin" / "opencode"
    fake_bin.parent.mkdir(parents=True, exist_ok=True)
    fake_bin.write_text("#!/bin/sh\necho 'Completed task analysis'\nexit 0\n")
    fake_bin.chmod(0o755)

    tasks_dir = tmp_path / "batch_state" / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks_dir))
    monkeypatch.setenv("PATH", f"{fake_bin.parent}:{os.environ.get('PATH', '')}")

    # Write initial state file as cmd_dispatch does
    state_path = delegate._state_path("glm-lifecycle-success")
    delegate._write_state_atomic(
        state_path,
        {
            "task_id": "glm-lifecycle-success",
            "agent": "glm",
            "model": "glm-5.3",
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
        model="glm-5.3",
        hard_timeout=300,
        silence_timeout=60,
    )

    assert rc == 1
    state = delegate._read_state(state_path)
    assert state is not None
    assert state["status"] == "failed"
    assert state["returncode"] is None
    assert state["agent"] == "glm"
    assert state["last_error"] == "adapter_rejected, ValueError"
    assert "is retired in the model catalog" in capsys.readouterr().err


def test_glm_delegate_worker_retirement_has_no_provider_returncode(tmp_path, monkeypatch, capsys):
    fake_bin = tmp_path / "bin" / "opencode"
    fake_bin.parent.mkdir(parents=True, exist_ok=True)
    fake_bin.write_text(
        '#!/bin/sh\nif [ "$1" = debug ] && [ "$2" = config ]; then exit 0; fi\n'
        "echo 'CLI internal error' >&2\nexit 1\n"
    )
    fake_bin.chmod(0o755)

    tasks_dir = tmp_path / "batch_state" / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks_dir))
    monkeypatch.setenv("PATH", f"{fake_bin.parent}:{os.environ.get('PATH', '')}")

    # Write initial state file as cmd_dispatch does
    state_path = delegate._state_path("glm-lifecycle-failure")
    delegate._write_state_atomic(
        state_path,
        {
            "task_id": "glm-lifecycle-failure",
            "agent": "glm",
            "model": "glm-5.3",
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
        model="glm-5.3",
        hard_timeout=300,
        silence_timeout=60,
    )

    assert rc == 1
    state = delegate._read_state(state_path)
    assert state is not None
    assert state["status"] == "failed"
    assert state["returncode"] is None
    assert state["agent"] == "glm"
    assert state["last_error"] == "adapter_rejected, ValueError"
    assert "is retired in the model catalog" in capsys.readouterr().err
