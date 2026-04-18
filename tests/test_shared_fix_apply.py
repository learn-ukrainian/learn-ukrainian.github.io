"""Tests for shared first-occurrence fix application."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from shared.fix_apply import apply_fix_pair


def test_strict_present_applies() -> None:
    updated, applied = apply_fix_pair("alpha beta", "beta", "gamma")
    assert applied is True
    assert updated == "alpha gamma"


def test_strict_absent_does_not_apply() -> None:
    original = "alpha beta"
    updated, applied = apply_fix_pair(original, "delta", "gamma")
    assert applied is False
    assert updated == original


def test_strict_multi_occurrence_only_replaces_first() -> None:
    updated, applied = apply_fix_pair("one two two", "two", "three")
    assert applied is True
    assert updated == "one three two"


def test_strict_empty_replace_deletes_first_occurrence() -> None:
    updated, applied = apply_fix_pair("remove me me", "me ", "")
    assert applied is True
    assert updated == "remove me"


def test_tolerant_trailing_whitespace_variant_applies() -> None:
    updated, applied = apply_fix_pair(
        "Привіт світе",
        "Привіт світе   ",
        "Добрий день",
        tolerant_whitespace=True,
    )
    assert applied is True
    assert updated == "Добрий день"


def test_tolerant_tab_space_newline_runs_apply() -> None:
    updated, applied = apply_fix_pair(
        "Слава\t\n  Україні",
        "Слава Україні",
        "Героям слава",
        tolerant_whitespace=True,
    )
    assert applied is True
    assert updated == "Героям слава"


def test_tolerant_absent_does_not_apply() -> None:
    original = "alpha\tbeta"
    updated, applied = apply_fix_pair(
        original,
        "gamma delta",
        "epsilon",
        tolerant_whitespace=True,
    )
    assert applied is False
    assert updated == original


def test_unicode_strict_mode_works() -> None:
    updated, applied = apply_fix_pair("Київ і Львів", "Київ", "Харків")
    assert applied is True
    assert updated == "Харків і Львів"


def test_unicode_tolerant_mode_works() -> None:
    updated, applied = apply_fix_pair(
        "Українська\n  мова",
        "Українська мова",
        "рідна мова",
        tolerant_whitespace=True,
    )
    assert applied is True
    assert updated == "рідна мова"
