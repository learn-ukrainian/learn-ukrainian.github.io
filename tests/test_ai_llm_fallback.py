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


def test_build_gemini_ladder_keeps_flash_on_agy_only():
    ladder = build_gemini_ladder(allowed_auth_modes=("api", "oauth"))

    assert [(r.cli, r.model, r.auth_mode) for r in ladder] == [
        ("gemini-cli", PRIMARY_GEMINI_MODEL, "api"),
        ("gemini-cli", PRIMARY_GEMINI_MODEL, "oauth"),
        ("agy-cli", AGY_GEMINI_MODEL, None),
    ]
    assert [r.index for r in ladder] == [1, 2, 3]
    assert all(r.total == 3 for r in ladder)


def test_build_gemini_ladder_without_api_key_keeps_agy_rung():
    ladder = build_gemini_ladder(
        allowed_auth_modes=("oauth",),
    )

    assert [(r.cli, r.model, r.auth_mode) for r in ladder] == [
        ("gemini-cli", PRIMARY_GEMINI_MODEL, "oauth"),
        ("agy-cli", AGY_GEMINI_MODEL, None),
    ]
    assert [r.index for r in ladder] == [1, 2]
    assert all(r.total == 2 for r in ladder)


@pytest.mark.parametrize("model", [PRIMARY_GEMINI_MODEL, FLASH_GEMINI_MODEL, FINAL_GEMINI_MODEL, "custom-model"])
@pytest.mark.parametrize("auth_modes", [("api", "oauth"), ("api",), ("oauth",)])
def test_agy_only_models_never_get_gemini_cli_rungs(model, auth_modes):
    ladder = build_gemini_ladder(model, allowed_auth_modes=auth_modes)
    assert all(r.cli != "gemini-cli" or r.model not in {FLASH_GEMINI_MODEL, FINAL_GEMINI_MODEL} for r in ladder)


def test_build_gemini_ladder_rejects_empty_auth_modes():
    with pytest.raises(ValueError, match="must not be empty"):
        build_gemini_ladder(allowed_auth_modes=())


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
