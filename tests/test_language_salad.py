"""Tests for the language-salad detector.

Covers the critical cases that shipped as regressions during A1 build:

- Phase resolution: A1 M01-M03 resolve to the Alphabet phase (not Decoding).
- Dialog regex: `> **Анна:** Привіт!` (colon inside bold) is recognized as
  a dialog block and excluded from paragraph analysis. Previously only
  `> **Анна**:` (colon outside) matched, which caused entire dialog blocks
  to be emitted as "UK paragraphs" and triggered spurious
  PHASE_TRANSLATIONS_MISSING errors on A1 M01.
- Phase 0 (A1 M04-M14) still rejects multi-sentence UK prose paragraphs.
- Phase 0A (A1 M01-M03) does NOT reject UK prose and does NOT require
  its presence (dialog-based teaching is fine).
- Inline-gloss salad still fires for dense `**term** (gloss)` paragraphs
  at any phase (that's a style issue, not a phase issue).
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add scripts/ to path so `from audit.checks.language_salad import ...` works.
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from audit.checks.language_salad import (
    _ALPHABET_PHASE,
    PHASES,
    detect_language_salad,
    get_phase,
    split_paragraphs,
)

# ---------------------------------------------------------------------------
# Phase resolution
# ---------------------------------------------------------------------------


def test_a1_m01_to_m03_resolve_to_alphabet_phase():
    """A1 M01-M03 are the alphabet/phonetics modules and get a special phase."""
    for n in (1, 2, 3):
        phase = get_phase("a1", n)
        assert phase is _ALPHABET_PHASE, f"A1 M{n:02d} should be alphabet phase"
        assert phase.allow_uk_paragraphs is True
        assert phase.require_uk_paragraphs is False


def test_a1_m04_to_m14_resolve_to_decoding_phase():
    """A1 M04-M14 (post-alphabet decoding practice) forbid UK prose."""
    for n in (4, 10, 14):
        phase = get_phase("a1", n)
        assert phase is PHASES[0], f"A1 M{n:02d} should be decoding phase"
        assert phase.allow_uk_paragraphs is False


def test_a1_m15_to_m34_resolve_to_first_uk_prose_phase():
    """A1 M15+ moves to the first-UK-prose phase (Phase 1)."""
    for n in (15, 25, 34):
        phase = get_phase("a1", n)
        assert phase is PHASES[1], f"A1 M{n:02d} should be phase 1"


# ---------------------------------------------------------------------------
# Dialog regex fix
# ---------------------------------------------------------------------------


def test_dialog_with_colon_inside_bold_is_excluded_from_paragraphs():
    """`> **Анна:** Привіт!` dialog blocks must not be emitted as UK paragraphs.

    Regression: before 2026-04-10 only the `**Name**:` form (colon after
    the closing asterisks) was recognized. The `**Name:**` form (colon
    inside) leaked through, got picked up as a 3-sentence UK paragraph,
    and triggered PHASE_TRANSLATIONS_MISSING on A1 M01.
    """
    content = """
English intro paragraph here.

> **Анна:** Привіт! Як справи? *(Hi! How are you?)*
> **Іван:** Чудово! А у тебе? *(Great! And you?)*
> **Анна:** Добре. *(Good.)*

Another English paragraph here.
"""
    paragraphs = split_paragraphs(content)
    # The dialog lines must not appear as a paragraph.
    assert not any("Анна" in text for _, text in paragraphs), (
        f"Dialog leaked into paragraphs: "
        f"{[t for _, t in paragraphs if 'Анна' in t]}"
    )


def test_dialog_with_colon_outside_bold_still_excluded():
    """The legacy `**Name**:` form must continue to work."""
    content = """
Intro.

> **Maria**: Привіт!
> **Petro**: Привіт!

Outro.
"""
    paragraphs = split_paragraphs(content)
    assert not any("Maria" in text or "Petro" in text for _, text in paragraphs)


# ---------------------------------------------------------------------------
# Phase enforcement
# ---------------------------------------------------------------------------


def test_alphabet_phase_accepts_dialog_only_teaching():
    """A module teaching via dialogs + inline glosses (no UK prose) is fine."""
    content = """
---
title: Test
---

## Greeting

Your first Ukrainian conversation uses **Привіт!** (Hi!).

> **Анна:** Привіт! *(Hi!)*
> **Іван:** Привіт! *(Hi!)*

The word **Добре** (Good) is your first positive reply.
"""
    issues = detect_language_salad(content, "a1", 1)
    # Should be clean — no UK paragraphs, dialog excluded, no PHASE_NO_UK_PARAGRAPHS
    assert len(issues) == 0, f"Expected clean, got: {[str(i) for i in issues]}"


def test_alphabet_phase_allows_uk_prose_when_writer_uses_it():
    """If the writer DOES add a UK paragraph in M01-M03, it's allowed
    (with the standard translation-block requirement)."""
    content = """
---
title: Test
---

## Letters

Introduction paragraph in English.

Українська мова має тридцять три літери. Ця абетка — кирилиця. Кожна літера має свій звук.

> *The Ukrainian language has thirty-three letters. This alphabet is Cyrillic. Each letter has its own sound.*

Back to English.
"""
    issues = detect_language_salad(content, "a1", 2)
    error_types = {i.type for i in issues if i.severity == "error"}
    # Must NOT fire PHASE_UK_PARAGRAPH_TOO_EARLY (that's for Phase 0 / M04+)
    assert "PHASE_UK_PARAGRAPH_TOO_EARLY" not in error_types
    # Must NOT fire PHASE_NO_UK_PARAGRAPHS either
    assert "PHASE_NO_UK_PARAGRAPHS" not in error_types


def test_decoding_phase_rejects_uk_prose_paragraphs():
    """A1 M04-M14 (Decoding) still forbids multi-sentence UK prose."""
    content = """
---
title: Test
---

## Practice

English explanation.

Це український параграф. Він має два речення.

More English.
"""
    issues = detect_language_salad(content, "a1", 5)
    error_types = {i.type for i in issues if i.severity == "error"}
    assert "PHASE_UK_PARAGRAPH_TOO_EARLY" in error_types, (
        f"Expected PHASE_UK_PARAGRAPH_TOO_EARLY to fire on A1 M05, "
        f"got: {[str(i) for i in issues]}"
    )


def test_phase_1_requires_uk_paragraphs():
    """A1 M15+ (Phase 1) MUST have Ukrainian prose paragraphs."""
    content = """
---
title: Test
---

## Section

All English here. No Ukrainian prose at all, just inline like **кіт** (cat).

More English, nothing else.
"""
    issues = detect_language_salad(content, "a1", 20)
    error_types = {i.type for i in issues if i.severity == "error"}
    assert "PHASE_NO_UK_PARAGRAPHS" in error_types


def test_excessive_inline_glosses_detected_outside_alphabet_phase():
    """Dense `**term** (gloss)` paragraphs are a style problem outside
    the alphabet phase (A1 M01-M03).

    Alphabet/phonetics modules are term-gloss dense by design — every
    letter introduction naturally pairs a Ukrainian word with its English
    gloss. We only flag the pattern from M04 onward where prose density
    is expected.
    """
    content = """
---
title: Test
---

## Section

Today we learn **кіт** (cat), **собака** (dog), **риба** (fish), **пташка** (bird), and **миша** (mouse). These are the most common **тварини** (animals) you'll meet.
"""
    # M20 is firmly outside the alphabet phase — the check must fire here.
    issues = detect_language_salad(content, "a1", 20)
    error_types = {i.type for i in issues}
    assert "SALAD_EXCESSIVE_INLINE_GLOSSES" in error_types


def test_excessive_inline_glosses_allowed_in_alphabet_phase():
    """A1 M01-M03 (alphabet phase) must tolerate dense term-gloss pairs.

    Pedagogically, the alphabet modules pair every Ukrainian example word
    with its English gloss — that IS the module's content. Flagging it as
    "excessive" created false positives that blocked the first 3 modules.
    """
    content = """
---
title: Test
---

## Section

Today we learn **кіт** (cat), **собака** (dog), **риба** (fish), **пташка** (bird), and **миша** (mouse). These are the most common **тварини** (animals) you'll meet.
"""
    for module_num in (1, 2, 3):
        issues = detect_language_salad(content, "a1", module_num)
        error_types = {i.type for i in issues}
        assert "SALAD_EXCESSIVE_INLINE_GLOSSES" not in error_types, (
            f"A1 M{module_num:02d} (alphabet phase) should not flag dense glosses"
        )
