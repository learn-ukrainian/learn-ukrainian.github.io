"""Gemini review requests require an explicit profile (operator 2026-09-25)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from scripts.ai_agent_bridge._agy import gemini_review_profile_error
from scripts.ai_agent_bridge._channels_cli import _gemini_review_request_error
from scripts.ai_agent_bridge._cli import _handle_acp_compat
from scripts.audit import llm_reviewer_dispatch


def test_missing_profile_names_the_flag() -> None:
    message = gemini_review_profile_error(None)
    assert message is not None
    assert "--review-profile" in message
    assert "ukrainian" in message


def test_code_profile_cites_the_operator_rule() -> None:
    message = gemini_review_profile_error("code")
    assert message is not None
    assert "gemini_code_review_forbidden" in message
    assert "Gemini reviews Ukrainian only, never code" in message


def test_ukrainian_profile_is_allowed() -> None:
    assert gemini_review_profile_error("ukrainian") is None


def test_ask_agy_review_without_profile_is_refused() -> None:
    args = SimpleNamespace(
        content="review this diff",
        data=None,
        to_model=None,
        model=None,
        task_id="review-agy",
        review=True,
        type="query",
        pr=None,
        branch=None,
        review_profile=None,
        background=False,
    )
    with pytest.raises(SystemExit, match="--review-profile"):
        _handle_acp_compat(args, "agy")


def test_ask_agy_code_profile_is_refused() -> None:
    args = SimpleNamespace(
        content="review this diff",
        data=None,
        to_model=None,
        model=None,
        task_id="review-agy",
        review=True,
        type="query",
        pr=None,
        branch=None,
        review_profile="code",
        background=False,
    )
    with pytest.raises(SystemExit, match="Gemini reviews Ukrainian only, never code"):
        _handle_acp_compat(args, "agy")


def test_ask_agy_ukrainian_profile_reaches_dispatch(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, object] = {}

    def fake_dispatch(target: str, content: str, **kwargs: object) -> None:
        seen["target"] = target
        seen["content"] = content
        seen["kwargs"] = kwargs

    monkeypatch.setattr(
        "scripts.ai_agent_bridge._cli._dispatch_headless_review",
        fake_dispatch,
    )
    args = SimpleNamespace(
        content="перевір наголос",
        data=None,
        to_model=None,
        model=None,
        task_id="review-agy-uk",
        review=True,
        type="query",
        pr=None,
        branch=None,
        review_profile="ukrainian",
        background=False,
        effort=None,
        output_path=None,
        stdout_only=False,
        no_timeout=False,
    )
    _handle_acp_compat(args, "agy")
    assert seen["target"] == "agy"
    assert seen["content"] == "перевір наголос"


def test_post_reviews_to_agy_requires_a_profile() -> None:
    missing = _gemini_review_request_error(
        channel="reviews",
        agents=["agy"],
        review=False,
        profile=None,
    )
    assert missing is not None
    assert "--review-profile" in missing

    refused = _gemini_review_request_error(
        channel="reviews",
        agents=["agy"],
        review=False,
        profile="code",
    )
    assert refused is not None
    assert "gemini_code_review_forbidden" in refused

    assert (
        _gemini_review_request_error(
            channel="reviews",
            agents=["agy"],
            review=False,
            profile="ukrainian",
        )
        is None
    )


def test_discuss_with_agy_requires_a_profile() -> None:
    missing = _gemini_review_request_error(
        channel="architecture",
        agents=["claude", "agy"],
        review=False,
        profile=None,
        force=True,
    )
    assert missing is not None
    assert "--review-profile" in missing

    assert (
        _gemini_review_request_error(
            channel="architecture",
            agents=["claude", "agy"],
            review=False,
            profile="ukrainian",
            force=True,
        )
        is None
    )


def test_ukrainian_content_caller_passes_the_profile() -> None:
    command = llm_reviewer_dispatch.FRONTIER_FACTUAL_ROUTE.bridge_command
    assert command[:1] == ("ask-agy",)
    assert "--review" in command
    assert command[command.index("--review-profile") + 1] == "ukrainian"
