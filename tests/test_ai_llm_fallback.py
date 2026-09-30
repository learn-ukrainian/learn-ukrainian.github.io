from __future__ import annotations

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


@pytest.mark.parametrize("model", [
    PRIMARY_GEMINI_MODEL, AGY_GEMINI_MODEL, FLASH_GEMINI_MODEL,
    FINAL_GEMINI_MODEL, "gemini-3.7-flash-high", "uncatalogued-model",
])
def test_frozen_gemini_cli_is_terminal_before_any_provider_call(model, tmp_path):
    def forbidden(*args, **kwargs):
        raise AssertionError("a refused route must not call a provider or fallback")

    with patch("subprocess.Popen", forbidden), patch(
        "ai_llm.fallback._run_agy_via_runtime", forbidden,
    ):
        result = call_gemini_with_fallback(
            "prompt", task_name="refusal", preferred_model=model,
            cwd=tmp_path, agy_runner=forbidden, sleep_fn=forbidden,
        )

    assert not result.ok
    assert result.error_message
    assert result.response_text is None
    assert result.model_used is None
    assert result.cli_used is None
    assert result.attempts == []
    assert result.elapsed_s == 0.0
    assert list(tmp_path.iterdir()) == []
