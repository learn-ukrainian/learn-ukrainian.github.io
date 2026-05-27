from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from ai_llm.fallback import (
    AGY_GEMINI_MODEL,
    FINAL_GEMINI_MODEL,
    FLASH_GEMINI_MODEL,
    PRIMARY_GEMINI_MODEL,
    AttemptOutcome,
    build_gemini_ladder,
    call_gemini_with_fallback,
)


@pytest.fixture(autouse=True)
def isolate_gemini_auth_state(monkeypatch, tmp_path):
    monkeypatch.setenv("GEMINI_AUTH_MODE", "auto")
    monkeypatch.setenv(
        "LU_GEMINI_COOLDOWN_PATH",
        str(tmp_path / "gemini-cooldown.json"),
    )


class _FakeProc:
    def __init__(self, spec: dict[str, object]):
        self.spec = spec
        self.returncode = spec.get("returncode", 0)
        self.killed = False

    def communicate(self, input: str | None = None, timeout: int | None = None) -> tuple[str, str]:
        _ = input
        _ = timeout
        if self.spec.get("kind") == "timeout" and not self.killed:
            raise subprocess.TimeoutExpired(cmd="gemini", timeout=timeout or 0)
        return (
            str(self.spec.get("stdout", "")),
            str(self.spec.get("stderr", "")),
        )

    def kill(self) -> None:
        self.killed = True
        self.returncode = -9


class _FakePopenFactory:
    def __init__(self, specs: list[dict[str, object]]):
        self.specs = list(specs)
        self.calls: list[dict[str, object]] = []

    def __call__(self, cmd, **kwargs):
        proc = _FakeProc(self.specs.pop(0))
        self.calls.append({"cmd": cmd, **kwargs, "proc": proc})
        return proc


def _base_env() -> dict[str, str]:
    return {
        "GEMINI_API_KEY": "secret",
        "GOOGLE_API_KEY": "secret-google",
        "GOOGLE_GENERATIVE_AI_API_KEY": "secret-genai",
        "GOOGLE_APPLICATION_CREDENTIALS": "/tmp/fake-creds.json",
        "GEMINI_SESSION": "1",
    }


def test_build_gemini_ladder_inserts_agy_between_pro_and_flash():
    ladder = build_gemini_ladder(allowed_auth_modes=("api", "oauth"))

    assert [(r.cli, r.model, r.auth_mode) for r in ladder] == [
        ("gemini-cli", PRIMARY_GEMINI_MODEL, "api"),
        ("gemini-cli", PRIMARY_GEMINI_MODEL, "oauth"),
        ("agy-cli", AGY_GEMINI_MODEL, None),
        ("gemini-cli", FLASH_GEMINI_MODEL, "api"),
        ("gemini-cli", FLASH_GEMINI_MODEL, "oauth"),
        ("gemini-cli", FINAL_GEMINI_MODEL, "api"),
        ("gemini-cli", FINAL_GEMINI_MODEL, "oauth"),
    ]
    assert [r.index for r in ladder] == list(range(1, 8))
    assert all(r.total == 7 for r in ladder)


def test_build_gemini_ladder_without_api_key_keeps_agy_rung():
    ladder = build_gemini_ladder(
        allowed_auth_modes=("oauth",),
    )

    assert [(r.cli, r.model, r.auth_mode) for r in ladder] == [
        ("gemini-cli", PRIMARY_GEMINI_MODEL, "oauth"),
        ("agy-cli", AGY_GEMINI_MODEL, None),
        ("gemini-cli", FLASH_GEMINI_MODEL, "oauth"),
        ("gemini-cli", FINAL_GEMINI_MODEL, "oauth"),
    ]
    assert [r.index for r in ladder] == [1, 2, 3, 4]
    assert all(r.total == 4 for r in ladder)


def test_call_gemini_with_fallback_rung1_success(tmp_path):
    factory = _FakePopenFactory(
        [{"stdout": "A" * 120, "stderr": "", "returncode": 0}]
    )

    with patch("ai_llm.fallback.subprocess.Popen", factory):
        result = call_gemini_with_fallback(
            "prompt",
            task_name="unit-test",
            cwd=tmp_path,
            base_env=_base_env(),
            logger=lambda _msg: None,
            sleep_fn=lambda _seconds, _reason: None,
        )

    assert result.ok is True
    assert result.response_text == "A" * 120
    assert result.model_used == PRIMARY_GEMINI_MODEL
    assert result.auth_mode_used == "api"
    assert len(factory.calls) == 1
    assert factory.calls[0]["cmd"][2] == PRIMARY_GEMINI_MODEL
    assert factory.calls[0]["cmd"][-2:] == ["-p", "prompt"]
    assert factory.calls[0]["stdin"] == subprocess.DEVNULL
    assert factory.calls[0]["env"]["GEMINI_API_KEY"] == "secret"


def test_call_gemini_with_fallback_rate_limit_advances_to_oauth(tmp_path):
    factory = _FakePopenFactory(
        [
            {"stdout": "", "stderr": "Quota exceeded 429", "returncode": 1},
            {"stdout": "B" * 120, "stderr": "", "returncode": 0},
        ]
    )

    with patch("ai_llm.fallback.subprocess.Popen", factory):
        result = call_gemini_with_fallback(
            "prompt",
            task_name="unit-test",
            cwd=tmp_path,
            base_env=_base_env(),
            logger=lambda _msg: None,
            sleep_fn=lambda _seconds, _reason: None,
        )

    assert result.ok is True
    assert result.model_used == PRIMARY_GEMINI_MODEL
    assert result.auth_mode_used == "oauth"
    assert [call["cmd"][2] for call in factory.calls] == [
        PRIMARY_GEMINI_MODEL,
        PRIMARY_GEMINI_MODEL,
    ]
    assert "GEMINI_API_KEY" in factory.calls[0]["env"]
    for key in (
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
        "GOOGLE_GENERATIVE_AI_API_KEY",
        "GOOGLE_APPLICATION_CREDENTIALS",
    ):
        assert key not in factory.calls[1]["env"]


def test_call_gemini_with_fallback_all_rungs_rate_limited(tmp_path):
    factory = _FakePopenFactory(
        [
            {"stdout": "", "stderr": "rate_limited 429", "returncode": 1},
            {"stdout": "", "stderr": "quota", "returncode": 1},
            {"stdout": "", "stderr": "429", "returncode": 1},
            {"stdout": "", "stderr": "quota", "returncode": 1},
            {"stdout": "", "stderr": "429", "returncode": 1},
            {"stdout": "", "stderr": "rate_limited", "returncode": 1},
        ]
    )

    def agy_runner(_prompt: str, _timeout_s: int | None) -> AttemptOutcome:
        return AttemptOutcome(
            status="rate_limited",
            elapsed_s=0.1,
            stderr_excerpt="Agy quota exceeded",
        )

    with patch("ai_llm.fallback.subprocess.Popen", factory):
        result = call_gemini_with_fallback(
            "prompt",
            task_name="unit-test",
            cwd=tmp_path,
            base_env=_base_env(),
            logger=lambda _msg: None,
            sleep_fn=lambda _seconds, _reason: None,
            agy_runner=agy_runner,
        )

    assert result.ok is False
    assert result.response_text is None
    assert len(result.attempts) == 7
    assert [(attempt.cli, attempt.model) for attempt in result.attempts] == [
        ("gemini-cli", PRIMARY_GEMINI_MODEL),
        ("gemini-cli", PRIMARY_GEMINI_MODEL),
        ("agy-cli", AGY_GEMINI_MODEL),
        ("gemini-cli", FLASH_GEMINI_MODEL),
        ("gemini-cli", FLASH_GEMINI_MODEL),
        ("gemini-cli", FINAL_GEMINI_MODEL),
        ("gemini-cli", FINAL_GEMINI_MODEL),
    ]
    assert all(attempt.status == "rate_limited" for attempt in result.attempts)
    assert "all 7 Gemini fallback rungs exhausted" in (result.error_message or "")


def test_call_gemini_with_fallback_agy_success_after_pro_rate_limit(tmp_path):
    factory = _FakePopenFactory(
        [
            {"stdout": "", "stderr": "rate_limited 429", "returncode": 1},
            {"stdout": "", "stderr": "quota", "returncode": 1},
        ]
    )

    def agy_runner(_prompt: str, _timeout_s: int | None) -> AttemptOutcome:
        return AttemptOutcome(
            status="success",
            elapsed_s=0.1,
            response_text="Agy answer" * 20,
        )

    with patch("ai_llm.fallback.subprocess.Popen", factory):
        result = call_gemini_with_fallback(
            "prompt",
            task_name="unit-test",
            cwd=tmp_path,
            base_env=_base_env(),
            logger=lambda _msg: None,
            sleep_fn=lambda _seconds, _reason: None,
            agy_runner=agy_runner,
        )

    assert result.ok is True
    assert result.model_used == AGY_GEMINI_MODEL
    assert result.auth_mode_used is None
    assert result.cli_used == "agy-cli"
    assert [(attempt.cli, attempt.model, attempt.status) for attempt in result.attempts] == [
        ("gemini-cli", PRIMARY_GEMINI_MODEL, "rate_limited"),
        ("gemini-cli", PRIMARY_GEMINI_MODEL, "rate_limited"),
        ("agy-cli", AGY_GEMINI_MODEL, "success"),
    ]


def test_call_gemini_with_fallback_agy_failure_falls_to_flash(tmp_path):
    factory = _FakePopenFactory(
        [
            {"stdout": "", "stderr": "rate_limited 429", "returncode": 1},
            {"stdout": "", "stderr": "quota", "returncode": 1},
            {"stdout": "Flash answer" * 20, "stderr": "", "returncode": 0},
        ]
    )

    def agy_runner(_prompt: str, _timeout_s: int | None) -> AttemptOutcome:
        return AttemptOutcome(
            status="retryable_error",
            elapsed_s=0.1,
            stderr_excerpt="agy unavailable",
        )

    with patch("ai_llm.fallback.subprocess.Popen", factory):
        result = call_gemini_with_fallback(
            "prompt",
            task_name="unit-test",
            cwd=tmp_path,
            base_env=_base_env(),
            logger=lambda _msg: None,
            sleep_fn=lambda _seconds, _reason: None,
            agy_runner=agy_runner,
        )

    assert result.ok is True
    assert result.model_used == FLASH_GEMINI_MODEL
    assert result.auth_mode_used == "api"
    assert result.cli_used == "gemini-cli"
    assert [(attempt.cli, attempt.model, attempt.status) for attempt in result.attempts] == [
        ("gemini-cli", PRIMARY_GEMINI_MODEL, "rate_limited"),
        ("gemini-cli", PRIMARY_GEMINI_MODEL, "rate_limited"),
        ("agy-cli", AGY_GEMINI_MODEL, "retryable_error"),
        ("gemini-cli", FLASH_GEMINI_MODEL, "success"),
    ]


def test_call_gemini_with_fallback_non_rate_limit_retries_same_rung(tmp_path):
    factory = _FakePopenFactory(
        [
            {"stdout": "", "stderr": "broken pipe", "returncode": 1},
            {"stdout": "", "stderr": "broken pipe", "returncode": 1},
            {"stdout": "", "stderr": "broken pipe", "returncode": 1},
        ]
    )

    with patch("ai_llm.fallback.subprocess.Popen", factory):
        result = call_gemini_with_fallback(
            "prompt",
            task_name="unit-test",
            cwd=tmp_path,
            base_env=_base_env(),
            logger=lambda _msg: None,
            sleep_fn=lambda _seconds, _reason: None,
        )

    assert result.ok is False
    assert len(factory.calls) == 3
    assert [call["cmd"][2] for call in factory.calls] == [
        PRIMARY_GEMINI_MODEL,
        PRIMARY_GEMINI_MODEL,
        PRIMARY_GEMINI_MODEL,
    ]
    assert all(attempt.auth_mode == "api" for attempt in result.attempts)
    assert all(attempt.status == "retryable_error" for attempt in result.attempts)


def test_call_gemini_with_fallback_timeout_retries_same_rung(tmp_path):
    factory = _FakePopenFactory(
        [
            {"kind": "timeout"},
            {"stdout": "C" * 120, "stderr": "", "returncode": 0},
        ]
    )

    with patch("ai_llm.fallback.subprocess.Popen", factory):
        result = call_gemini_with_fallback(
            "prompt",
            task_name="unit-test",
            cwd=tmp_path,
            base_env=_base_env(),
            logger=lambda _msg: None,
            sleep_fn=lambda _seconds, _reason: None,
        )

    assert result.ok is True
    assert result.auth_mode_used == "api"
    assert [call["cmd"][2] for call in factory.calls] == [
        PRIMARY_GEMINI_MODEL,
        PRIMARY_GEMINI_MODEL,
    ]
    assert result.attempts[0].status == "timeout"
