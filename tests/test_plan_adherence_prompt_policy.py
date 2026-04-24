"""Policy-pinning tests for the Plan Adherence reviewer prompt.

The `v6-review-plan-adherence.md` prompt encodes two policy-sensitive
rules that the reviewer uses to judge Plan Adherence:

  §2 — Section word budgets are SOFT. `target` and `max` are advisory,
       not binding. A section going over `max` is NEVER by itself a
       defect. Only silent deferral of contracted items is a defect.
       (Derived from NON-NEG rule #1 "word targets are MINIMUMS" and
        rule #3 "one section 20% over is fine if no section is >10%
        under".)

  §6 — Activity markers must be placed AFTER the teaching they test.
       A marker before the tested teaching is a defect.

Before #1529 / PR #1530 the §2 prose conflated "over max" with "silent
deferral," causing the reviewer to REJECT a1/1 for 5 false-positive
word-budget findings. These tests guard against that regression — if
the prompt drifts back to treating `max` as binding, the tests fail in
CI and block the regression.

The tests are intentionally phrasing-flexible (substring checks, not
exact-string matches) so minor wording edits stay green as long as the
operative rule is preserved.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_PROMPT_PATH = (
    Path(__file__).resolve().parent.parent
    / "scripts"
    / "build"
    / "phases"
    / "v6-review"
    / "v6-review-plan-adherence.md"
)


@pytest.fixture(scope="module")
def prompt_text() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


# ── §2 word-budget-is-soft policy ───────────────────────────────────


def test_prompt_exists(prompt_text: str) -> None:
    assert prompt_text.strip(), f"Prompt file is empty: {_PROMPT_PATH}"


def test_section_2_marks_word_budgets_as_soft(prompt_text: str) -> None:
    """§2 must declare `max` advisory, not binding. This is the core
    regression guard for the #1530 fix.
    """
    # Tolerate case + punctuation variation; check the operative phrase.
    lowered = prompt_text.lower()
    assert "advisory" in lowered, (
        "§2 must explicitly label section `max` as ADVISORY. "
        "Reviewer otherwise treats max as a hard limit and generates "
        "false-positive overrun findings (see #1529 a1/1 REJECT)."
    )


def test_section_2_explicitly_forbids_flagging_overruns(prompt_text: str) -> None:
    """Stronger guard — the prompt must explicitly tell the reviewer NOT
    to flag sections going over max. Positive 'advisory' language alone
    can be read ambiguously; the prohibition must be explicit."""
    lowered = prompt_text.lower()
    forbidden_phrases = (
        "never by itself",
        "do not flag",
        "do not penalize section overrun",
    )
    assert any(phrase in lowered for phrase in forbidden_phrases), (
        "§2 must contain an explicit 'do not flag over-max' instruction. "
        f"Expected one of {forbidden_phrases!r} somewhere in the prompt."
    )


def test_section_2_still_penalizes_silent_deferrals(prompt_text: str) -> None:
    """Softening §2 must not remove the deferral rule — that's the one
    class of §2 defect that is REAL. #1530 preserves this; guard it."""
    lowered = prompt_text.lower()
    assert "silent deferral" in lowered, (
        "§2 must still penalize silent deferrals — that is the one "
        "genuine Plan Adherence defect. If this test fires, the prompt "
        "has been over-softened."
    )


def test_section_2_lists_contract_fields_for_deferral_check(prompt_text: str) -> None:
    """The deferral check must be grounded in the specific contract
    fields that enumerate promised items. Without this anchoring the
    reviewer falls back to word-count heuristics and re-creates the
    false-positive class."""
    # Require mention of at least three of the five enumerable fields.
    fields = (
        "teaching_beats",
        "required_terms",
        "dialogue_acts",
        "factual_anchors",
        "activity_obligations",
    )
    present = [f for f in fields if f in prompt_text]
    assert len(present) >= 3, (
        "Silent-deferral definition must be anchored to specific contract "
        f"fields. Expected ≥3 of {fields!r}; found {present!r}. Without "
        "this, the reviewer will fall back to word-count heuristics."
    )


# ── §6 activity-marker policy (existing behaviour; guard it too) ───


def test_section_6_requires_marker_after_tested_teaching(prompt_text: str) -> None:
    """§6 is not touched by #1530 but is load-bearing for a1/1
    convergence. Pin it so nothing silently removes the rule."""
    lowered = prompt_text.lower()
    # Must mention that BEFORE-placement is a defect and AFTER is pass.
    assert "before" in lowered and "after" in lowered and "defect" in lowered, (
        "§6 must preserve the 'marker-BEFORE-teaching is a defect' rule."
    )


# ── Version tag hygiene ─────────────────────────────────────────────


def test_prompt_has_version_tag(prompt_text: str) -> None:
    """Every reviewer prompt starts with a semver-style version comment.
    Guards against silent edits that skip version bumps."""
    first_line = prompt_text.splitlines()[0]
    assert first_line.startswith("<!-- version:"), (
        f"Prompt must start with a `<!-- version: X.Y.Z | ... -->` tag; "
        f"got {first_line!r}"
    )
