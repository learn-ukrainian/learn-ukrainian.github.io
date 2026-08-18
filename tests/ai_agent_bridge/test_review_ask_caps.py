"""Formal review asks fail before broker delivery when their payload is fat."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.ai_agent_bridge import _claude, _codex, _hermes, _opencode
from scripts.ai_agent_bridge import _review_safety as safety


@pytest.mark.parametrize(
    ("ask", "kwargs"),
    (
        (_codex.ask_codex, {"from_llm": "test"}),
        (_claude.ask_claude, {"from_llm": "test"}),
        (_opencode.ask_glm, {"from_llm": "test"}),
        (_hermes.ask_hermes, {"model": "deepseek-v4-flash", "from_llm": "test"}),
    ),
)
def test_named_transports_reject_fat_formal_review_body(ask, kwargs: dict[str, str]) -> None:
    with pytest.raises(SystemExit, match=r"review_ask_content_exceeds_cap") as exc_info:
        ask(
            "x" * (safety.MAX_REVIEW_REQUEST_BYTES + 1),
            task_id="review-fat",
            msg_type="review",
            **kwargs,
        )
    # #7010: the retired sealed command must not be named as the fix.
    assert "review-pr" not in str(exc_info.value)


@pytest.mark.parametrize(
    ("ask", "kwargs"),
    (
        (_codex.ask_codex, {"from_llm": "test"}),
        (_claude.ask_claude, {"from_llm": "test"}),
        (_opencode.ask_glm, {"from_llm": "test"}),
        (_hermes.ask_hermes, {"model": "deepseek-v4-flash", "from_llm": "test"}),
    ),
)
def test_named_transports_reject_fat_formal_review_attachment(
    ask,
    kwargs: dict[str, str],
    tmp_path: Path,
) -> None:
    attachment = tmp_path / "fat-evidence.txt"
    attachment.write_bytes(b"x" * (safety.MAX_ASK_ATTACHMENT_BYTES + 1))

    with pytest.raises(SystemExit, match=r"review_ask_attachment_exceeds_cap") as exc_info:
        ask(
            "thin pointer only",
            task_id="review-attachment",
            msg_type="review",
            data=str(attachment),
            **kwargs,
        )
    assert "review-pr" not in str(exc_info.value)


def test_formal_review_without_target_warns(capsys: pytest.CaptureFixture[str]) -> None:
    safety.warn_missing_review_target(formal_review=True, has_target=False)
    err = capsys.readouterr().err
    assert "--pr <N>" in err
    # #7010: the retired sealed command must not be named as the next step.
    assert "prefer review-pr" not in err
