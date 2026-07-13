"""Tests for exact authored-word floors plus the retained callout minimum."""

import pytest

from scripts.build.linear_pipeline import (
    _engagement_floor_gate,
    _word_count_gate,
)

# ----- word_count tolerance --------------------------------------------------


def test_word_count_at_target_passes() -> None:
    """Baseline: count exactly at target passes."""
    text = "word " * 1200
    report = _word_count_gate(text, 1200)
    assert report["passed"] is True
    assert report["count"] == 1200


def test_word_count_above_target_passes() -> None:
    text = "word " * 1300
    report = _word_count_gate(text, 1200)
    assert report["passed"] is True


def test_word_count_below_exact_floor_fails() -> None:
    """A reviewed plan floor is exact; even a small shortfall remains blocked."""
    text = "word " * 1197
    report = _word_count_gate(text, 1200)
    assert report["passed"] is False
    assert report["count"] == 1197
    assert report["min_with_tolerance"] == 1200


def test_retired_tolerance_band_no_longer_passes() -> None:
    text = "word " * 1104
    report = _word_count_gate(text, 1200)
    assert report["passed"] is False
    assert report["min_with_tolerance"] == 1200


def test_word_count_just_below_band_fails() -> None:
    """count == min_with_tolerance - 1 fails."""
    text = "word " * 1103
    report = _word_count_gate(text, 1200)
    assert report["passed"] is False
    assert report["count"] == 1103


def test_word_count_14pct_below_target_fails() -> None:
    """Regression: gemini-tools 1031 vs A1 target 1200 (14% short) still fails."""
    text = "word " * 1031
    report = _word_count_gate(text, 1200)
    assert report["passed"] is False
    assert report["count"] == 1031


def test_word_count_reports_exact_floor_metadata() -> None:
    report = _word_count_gate("word " * 1200, 1200)
    assert report["min_with_tolerance"] == 1200
    assert report["tolerance_below_pct"] == 0.0
    assert report["target"] == 1200


def test_word_count_excludes_primary_reading_fence() -> None:
    text = (
        ("counted " * 10)
        + "<!-- PRIMARY-READING -->\n"
        + ("primary " * 100)
        + "\n<!-- /PRIMARY-READING -->"
    )

    report = _word_count_gate(text, 20)

    assert report["count"] == 10


# ----- callout_min ------------------------------------------------------------


def test_engagement_floor_passes_with_one_callout() -> None:
    """Regression: single callout now satisfies the floor (was minimum 2)."""
    text = """
# Module

Some intro prose.

:::tip
A pedagogical mnemonic the learner can carry.
:::

More prose with a bullet list:

- Перший приклад (first example)
- Другий приклад (second example)
- Третій приклад (third example)
- Четвертий приклад (fourth example)
- П'ятий приклад (fifth example)
- Шостий приклад (sixth example)
"""
    plan = {"word_target": 100, "level": "a1"}
    report = _engagement_floor_gate(text, plan)
    # callout_min is the load-bearing check for this PR. The engagement_floor
    # also requires other signals; we assert specifically on callout_min.
    assert report["callout_min"] == 1
    # If the only failing dimension was callout count, passing now succeeds.
    assert report["callout_count"] >= 1


def test_engagement_floor_callout_min_is_1() -> None:
    """The callout floor is exactly 1, not 2 (regression on PR-B)."""
    text = ":::tip\nA mnemonic.\n:::\n"
    plan = {"word_target": 100, "level": "a1"}
    report = _engagement_floor_gate(text, plan)
    assert report["callout_min"] == 1


@pytest.mark.parametrize(
    "text",
    [
        ":::tip\nA mnemonic.\n:::\n\nThis section teaches the alphabet.",
        ":::tip\nA mnemonic.\n:::\n\nLearners will compare **а** and **о**.",
        ":::tip\nA mnemonic.\n:::\n\nThe activity asks you to hear **і**.",
    ],
)
def test_engagement_floor_flags_teacher_plan_meta_narration(text: str) -> None:
    plan = {"word_target": 100, "level": "a1"}
    report = _engagement_floor_gate(text, plan)
    assert report["passed"] is False
    assert len(report["meta_narration_hits"]) == 1
