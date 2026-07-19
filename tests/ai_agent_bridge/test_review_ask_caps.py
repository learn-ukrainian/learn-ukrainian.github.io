"""Formal review asks fail before broker delivery when their payload is fat."""

from __future__ import annotations

from pathlib import Path

import pytest
from ai_agent_bridge import _claude, _codex, _hermes, _opencode
from ai_agent_bridge import _review_safety as safety


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
    with pytest.raises(SystemExit, match=r"review-pr.*exceeds_cap|exceeds_cap.*review-pr"):
        ask(
            "x" * (safety.MAX_REVIEW_REQUEST_BYTES + 1),
            task_id="review-fat",
            msg_type="review",
            **kwargs,
        )


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

    with pytest.raises(SystemExit, match=r"review-pr.*attachment_exceeds_cap|attachment_exceeds_cap.*review-pr"):
        ask(
            "thin pointer only",
            task_id="review-attachment",
            msg_type="review",
            data=str(attachment),
            **kwargs,
        )


def test_formal_review_without_target_warns(capsys: pytest.CaptureFixture[str]) -> None:
    safety.warn_missing_review_target(formal_review=True, has_target=False)
    assert "prefer review-pr <N>" in capsys.readouterr().err
