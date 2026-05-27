from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from ai_llm.fallback import (
    AGY_GEMINI_MODEL,
    FLASH_GEMINI_MODEL,
    PRIMARY_GEMINI_MODEL,
    AttemptOutcome,
    build_gemini_ladder,
    run_gemini_fallback_ladder,
)


def test_shared_ladder_order_includes_agy_after_pro():
    ladder = build_gemini_ladder(allowed_auth_modes=("api", "oauth"))

    assert [(r.cli, r.model, r.auth_mode) for r in ladder[:4]] == [
        ("gemini-cli", PRIMARY_GEMINI_MODEL, "api"),
        ("gemini-cli", PRIMARY_GEMINI_MODEL, "oauth"),
        ("agy-cli", AGY_GEMINI_MODEL, None),
        ("gemini-cli", FLASH_GEMINI_MODEL, "api"),
    ]
    assert len(ladder) == 7


def test_agy_retryable_error_advances_to_flash_rung():
    outcomes = {
        (PRIMARY_GEMINI_MODEL, "api"): AttemptOutcome(
            status="rate_limited",
            elapsed_s=0.1,
            stderr_excerpt="429 quota",
        ),
        (PRIMARY_GEMINI_MODEL, "oauth"): AttemptOutcome(
            status="rate_limited",
            elapsed_s=0.1,
            stderr_excerpt="oauth quota",
        ),
        (AGY_GEMINI_MODEL, None): AttemptOutcome(
            status="retryable_error",
            elapsed_s=0.1,
            stderr_excerpt="agy unavailable",
        ),
        (FLASH_GEMINI_MODEL, "api"): AttemptOutcome(
            status="success",
            elapsed_s=0.1,
            response_text="flash answer",
        ),
    }
    seen: list[tuple[str, str | None]] = []

    def runner(rung, _attempt_idx, _timeout_s):
        key = (rung.model, rung.auth_mode)
        seen.append(key)
        return outcomes[key]

    result = run_gemini_fallback_ladder(
        task_name="agy-fallback-test",
        attempt_runner=runner,
        allowed_auth_modes=("api", "oauth"),
        logger=lambda _msg: None,
        sleep_fn=lambda _seconds, _reason: None,
    )

    assert result.ok is True
    assert result.model_used == FLASH_GEMINI_MODEL
    assert result.cli_used == "gemini-cli"
    assert seen == [
        (PRIMARY_GEMINI_MODEL, "api"),
        (PRIMARY_GEMINI_MODEL, "oauth"),
        (AGY_GEMINI_MODEL, None),
        (FLASH_GEMINI_MODEL, "api"),
    ]
