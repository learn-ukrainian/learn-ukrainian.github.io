from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from agent_runtime.errors import AgentTimeoutError
from agent_runtime.result import Result
from agent_runtime.watchdog import WatchdogState
from batch_gemini_runner.constants import TIMEOUT_SECONDS
from batch_gemini_runner.execution import call_gemini


class _FakeStdin:
    def __init__(self) -> None:
        self.buffer = ""

    def write(self, text: str) -> int:
        self.buffer += text
        return len(text)

    def close(self) -> None:
        return None


class _FakeProc:
    def __init__(self, returncode: int = 0) -> None:
        self.returncode = returncode
        self.stdin = _FakeStdin()
        self.pid = 4321

    def poll(self) -> int:
        return self.returncode

    def wait(self, timeout: float | None = None) -> int:
        _ = timeout
        return self.returncode


class _PopenCapture:
    def __init__(self, returncode: int = 0) -> None:
        self.returncode = returncode
        self.calls: list[dict[str, object]] = []

    def __call__(self, *args, **kwargs):
        self.calls.append({"args": args, "kwargs": kwargs})
        return _FakeProc(self.returncode)


@pytest.fixture(autouse=True)
def _clear_runtime_state():
    from agent_runtime import runner as runner_mod

    runner_mod._ADAPTER_CACHE.clear()
    yield
    runner_mod._ADAPTER_CACHE.clear()


def _make_prompt_file(tmp_path: Path, text: str = "Say hello") -> Path:
    prompt_file = tmp_path / "prompt.md"
    prompt_file.write_text(text, encoding="utf-8")
    return prompt_file


def _invoke_with_captured_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    oauth_creds: bool,
    auth_mode: str | None = None,
) -> tuple[dict[str, object], _PopenCapture]:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("GEMINI_API_KEY", "test-api-key")
    if auth_mode is None:
        monkeypatch.delenv("GEMINI_AUTH_MODE", raising=False)
    else:
        monkeypatch.setenv("GEMINI_AUTH_MODE", auth_mode)

    gemini_dir = tmp_path / ".gemini"
    gemini_dir.mkdir(exist_ok=True)
    oauth_file = gemini_dir / "oauth_creds.json"
    if oauth_creds:
        oauth_file.write_text("{}", encoding="utf-8")
    else:
        oauth_file.unlink(missing_ok=True)

    payload = json.dumps({"response": "hello from gemini", "stats": {"models": {}}})
    popen_capture = _PopenCapture(returncode=0)
    watchdog_state = WatchdogState(
        start_time=0.0,
        last_activity=0.0,
        stdout_lines=[payload],
        stderr_lines=[],
    )

    with patch("agent_runtime.runner.has_headroom", return_value=(True, "")), patch(
        "agent_runtime.runner.write_record",
    ), patch(
        "agent_runtime.runner.subprocess.Popen", popen_capture,
    ), patch(
        "agent_runtime.runner.start_watchdog", return_value=(watchdog_state, []),
    ), patch(
        "agent_runtime.runner.stop_watchdog",
    ), patch(
        "agent_runtime.adapters.gemini.Path.home", return_value=tmp_path,
    ), patch(
        "batch_gemini_runner.execution._log_api_usage",
    ):
        result = call_gemini(_make_prompt_file(tmp_path), "bio", slug="demo", phase=2, retry=0)

    return result, popen_capture


def test_env_stripped_when_oauth_present(tmp_path, monkeypatch):
    _result, popen_capture = _invoke_with_captured_env(
        tmp_path, monkeypatch, oauth_creds=True,
    )

    env = popen_capture.calls[0]["kwargs"]["env"]
    assert "GEMINI_API_KEY" not in env
    assert "GOOGLE_API_KEY" not in env
    assert "GOOGLE_GENERATIVE_AI_API_KEY" not in env
    assert "GOOGLE_APPLICATION_CREDENTIALS" not in env


def test_env_stripped_when_oauth_absent_under_always_subscription(tmp_path, monkeypatch):
    """Always-subscription policy (2026-04-23, post-#1416): API-key envs are
    stripped unconditionally unless the caller explicitly requests
    ``GEMINI_AUTH_MODE=api``. Whether oauth creds are on disk is irrelevant —
    the Ultra subscription is the canonical path. See commit 4f0fae3c0b.
    """
    _result, popen_capture = _invoke_with_captured_env(
        tmp_path, monkeypatch, oauth_creds=False,
    )

    env = popen_capture.calls[0]["kwargs"]["env"]
    assert "GEMINI_API_KEY" not in env


def test_explicit_subscription_mode_strips(tmp_path, monkeypatch):
    _result, popen_capture = _invoke_with_captured_env(
        tmp_path, monkeypatch, oauth_creds=False, auth_mode="subscription",
    )

    env = popen_capture.calls[0]["kwargs"]["env"]
    assert "GEMINI_API_KEY" not in env


def test_explicit_api_mode_keeps_env_key(tmp_path, monkeypatch):
    """Escape hatch: ``GEMINI_AUTH_MODE=api`` is the only way to preserve the
    API-key env under always-subscription policy. Ensures the opt-out actually
    works for one-off debug runs."""
    _result, popen_capture = _invoke_with_captured_env(
        tmp_path, monkeypatch, oauth_creds=False, auth_mode="api",
    )

    env = popen_capture.calls[0]["kwargs"]["env"]
    assert env["GEMINI_API_KEY"] == "test-api-key"


def test_return_shape_preserved(tmp_path):
    prompt_file = _make_prompt_file(tmp_path)
    payload = {
        "response": "structured text",
        "stats": {
            "models": {
                "gemini-3.1-pro-preview": {
                    "tokens": {
                        "input": 10,
                        "candidates": 4,
                        "cached": 0,
                    },
                },
            },
        },
    }
    runtime_result = Result(
        ok=True,
        agent="gemini",
        model="gemini-3.1-pro-preview",
        mode="read-only",
        response=json.dumps(payload),
        stderr_excerpt="runtime stderr",
        duration_s=0.25,
        session_id=None,
        rate_limited=False,
        stalled=False,
        returncode=0,
        usage_record={},
    )

    with patch(
        "batch_gemini_runner.execution.runtime_invoke",
        return_value=runtime_result,
    ), patch(
        "batch_gemini_runner.execution._log_api_usage",
    ) as mock_log_usage:
        result = call_gemini(prompt_file, "bio", slug="demo", phase=2, retry=1)

    assert set(result.keys()) == {
        "returncode",
        "stdout",
        "stderr",
        "gemini_json",
        "elapsed_ms",
    }
    assert result["returncode"] == 0
    assert result["stdout"] == "structured text"
    assert result["stderr"] == "runtime stderr"
    assert result["gemini_json"] == payload
    assert result["elapsed_ms"] == 250
    mock_log_usage.assert_called_once()


def test_timeout_returns_existing_shape(tmp_path):
    prompt_file = _make_prompt_file(tmp_path)

    with patch(
        "batch_gemini_runner.execution.runtime_invoke",
        side_effect=AgentTimeoutError("gemini", TIMEOUT_SECONDS),
    ):
        result = call_gemini(prompt_file, "bio", slug="demo", phase=2, retry=0)

    assert result["returncode"] == -1
    assert "Timeout expired" in result["stderr"]
    assert result["stdout"] == ""
    assert result["gemini_json"] == {}
