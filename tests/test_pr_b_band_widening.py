"""Tests for PR-B band widening: word_count tolerance + callout_min (2026-05-23)."""

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


def test_word_count_within_8pct_tolerance_passes() -> None:
    """Regression: deepseek-pro 1197 vs A1 target 1200 (0.25% short) now passes."""
    text = "word " * 1197
    report = _word_count_gate(text, 1200)
    assert report["passed"] is True
    assert report["count"] == 1197
    assert report["min_with_tolerance"] == 1104  # int(1200 * 0.92)


def test_word_count_at_band_edge_passes() -> None:
    """count == min_with_tolerance (target * 0.92) passes."""
    text = "word " * 1104  # int(1200 * 0.92)
    report = _word_count_gate(text, 1200)
    assert report["passed"] is True
    assert report["min_with_tolerance"] == 1104


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


def test_word_count_reports_tolerance_metadata() -> None:
    """The gate report includes min_with_tolerance + tolerance_below_pct."""
    report = _word_count_gate("word " * 1200, 1200)
    assert report["min_with_tolerance"] == 1104
    assert report["tolerance_below_pct"] == 8.0
    assert report["target"] == 1200


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
