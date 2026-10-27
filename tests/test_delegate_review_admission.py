"""#9272: review routes retain an eligible identity and bare head pins refuse before effects."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from scripts.agent_runtime import target_admission
from scripts.agent_runtime.target_admission import ReviewAdmissionRefused, resolve_and_admit
from tests.claude_route_accounts import HOST_ACCOUNT


@pytest.mark.parametrize("risk", ["low", "medium"])
def test_native_gemini_low_medium_review_retains_requested_seat(risk):
    result = target_admission._resolve_review_target(
        "agy",
        "gemini-3.8-flash-high",
        author_model="gpt-6.1-sol",
        risk=risk,
        profile="code",
        attempt=False,
        snapshot=None,
        budget_seat="agy",
        claude_account=HOST_ACCOUNT,
    )
    assert result == ("agy", "gemini-3.8-flash-high")


@pytest.mark.parametrize(
    "risk,path",
    [
        ("high", "ordinary.py"),
        ("critical", "ordinary.py"),
        ("low", ".github/workflows/ci.yml"),
        ("medium", "scripts/review/reviewer_resolver.py"),
    ],
)
def test_gemini_review_attempt_refuses_high_risk_and_security(risk, path):
    with pytest.raises(ReviewAdmissionRefused):
        target_admission._resolve_review_target(
            "agy",
            "gemini-3.8-flash-high",
            author_model="gpt-6.1-sol",
            risk=risk,
            profile="code",
            attempt=True,
            snapshot=None,
            budget_seat="agy",
            changed_paths=(path,),
            claude_account=HOST_ACCOUNT,
        )


def test_9312_ineligible_ukrainian_reviewer_has_no_code_substitution_hint():
    with pytest.raises(ReviewAdmissionRefused) as refused:
        resolve_and_admit(
            ("grok",),
            model="grok-4.7",
            mode="read-only",
            review_dispatch=True,
            review_profile="ukrainian",
            claude_account=HOST_ACCOUNT,
        )
    assert "--review-profile ukrainian" in str(refused.value)
    assert "--review-author-model" not in str(refused.value)


def test_9312_merge_heading_is_followed_by_landing_policy(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    workflow = (Path(__file__).resolve().parents[1] / "agents_extensions/shared/rules/workflow.md").read_text(
        encoding="utf-8"
    )
    merge = workflow.split("## Merge policy — ready PRs must not sit", 1)[1]
    assert merge.split("\n\n", 1)[1].startswith("The binding landing order")


def _review_target(model, *, attempt=False, seat="cursor", author="claude-opus-5-5", risk="medium"):
    return target_admission._resolve_review_target(
        seat,
        model,
        author_model=author,
        risk=risk,
        profile="code",
        attempt=attempt,
        snapshot=None,
        budget_seat=seat,
        claude_account=HOST_ACCOUNT,
    )


@pytest.mark.parametrize("model", ["grok-4.7-high[fast]", "grok-4.7-high[1m]", "grok-4.7-high[]"])
def test_a_suffixed_cursor_grok_slug_is_never_an_attempt_identity(model):
    """#9488: eligibility is decided on the exact string the adapter would send as --model."""
    with pytest.raises(ReviewAdmissionRefused, match="REVIEW_ATTEMPT_IDENTITY_REFUSED"):
        _review_target(model, attempt=True)


def test_the_exact_cursor_grok_slug_is_kept_as_requested():
    assert _review_target("grok-4.7-high", attempt=True) == ("cursor", "grok-4.7-high")


def test_security_changed_paths_cannot_be_hidden_by_ordinary_owned_paths():
    with pytest.raises(ReviewAdmissionRefused, match="REVIEW_ATTEMPT_IDENTITY_REFUSED"):
        resolve_and_admit(
            ("claude",),
            mode="read-only",
            model="claude-sonnet-5-5",
            review_dispatch=True,
            review_author_model="gpt-6.1-sol",
            review_risk="low",
            review_attempt=True,
            review_owned_paths=("ordinary.py",),
            review_changed_paths=("scripts/ocr/_credentials.py",),
            claude_account=HOST_ACCOUNT,
        )


def test_a_native_seat_keeps_its_context_suffix():
    """Bracket suffixes on native seats (context windows) keep their pre-#9488 admission."""
    assert _review_target("claude-opus-5-5[1m]", seat="claude", author="gpt-6.1-sol") == (
        "claude",
        "claude-opus-5-5[1m]",
    )


FABLE_PINS = [
    ("claude", "claude-fable-5-1"),
    ("claude", "claude-fable-5-1[1m]"),
    ("cursor", "claude-fable-5-1-thinking-high"),  # the Cursor fallback slug
]
NO_REVIEW_ROLE = "holds no review, critique or approval role in the model catalog"


@pytest.mark.parametrize("seat,model", FABLE_PINS)
def test_bridge_review_mode_refuses_a_fable_pin(seat, model):
    """``ask-* --review`` admits in ``REVIEW_MODE`` before any prompt or dispatch is written."""
    from scripts.agent_runtime.kimi_admission import REVIEW_MODE

    with pytest.raises(ReviewAdmissionRefused, match=NO_REVIEW_ROLE):
        resolve_and_admit((seat,), mode=REVIEW_MODE, model=model, review=True)
    (target,) = resolve_and_admit(("claude",), mode=REVIEW_MODE, model="claude-opus-5-5", review=True)
    assert target.model == "claude-opus-5-5"


HIGH_RISK_RULE = "a formal review at high risk is performed only by gpt-6.1-sol, claude-opus-5-5"


@pytest.mark.parametrize("seat,model", [("claude", "claude-sonnet-5-5")])
def test_high_risk_review_attempt_refuses_with_the_rule(seat, model):
    with pytest.raises(ReviewAdmissionRefused, match="REVIEW_ATTEMPT_IDENTITY_REFUSED") as refused:
        _review_target(
            model, attempt=True, seat=seat, author="gpt-6.1-sol" if seat == "claude" else "claude-opus-5-5", risk="high"
        )
    assert HIGH_RISK_RULE in str(refused.value)


def test_review_admission_refuses_a_route_ignoring_the_reviewer_selector():
    with pytest.raises(ReviewAdmissionRefused, match="REVIEW_ROUTE_REFUSED"):
        resolve_and_admit(
            ("codex",),
            mode="read-only",
            model="gpt-6.1-sol",
            review_dispatch=True,
            route=lambda request: ("cursor", "grok-4.7", "budget"),
            claude_account=HOST_ACCOUNT,
        )


# --- #9739: a trusted review reads the target branch's complete authorship ------------------------
