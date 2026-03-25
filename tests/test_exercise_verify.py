"""Tests for exercise verification — grounding check for exercise items.

Issue: #1016
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build.exercise_verify import (
    extract_exercise_items,
    extract_plan_vocab,
    extract_prose_words,
    format_verify_result,
    verify_exercises,
)

# --- extract_exercise_items ---


def test_extract_quiz_items():
    content = """\
## Section

Some prose here.

:::quiz
title: "Test quiz"
---
- q: "What gender is **студент**?"
  o: ["чоловічий", "жіночий", "середній"]
  a: 0
:::
"""
    items = extract_exercise_items(content)
    words = {i.word for i in items}
    assert "студент" in words
    assert "чоловічий" in words
    assert "жіночий" in words
    assert "середній" in words


def test_extract_fill_in_items():
    content = """\
## Section

Some prose.

:::fill-in
title: "Fill in"
---
- sentence: "Це ___ мама."
  answer: "моя"
- sentence: "Це ___ стіл."
  answer: "мій"
:::
"""
    items = extract_exercise_items(content)
    words = {i.word for i in items}
    assert "моя" in words
    assert "мій" in words
    assert "мама" in words
    assert "стіл" in words


def test_extract_match_up_items():
    content = """\
## Section

:::match-up
title: "Match"
---
- left: "parents"
  right: "батьки"
- left: "uncle"
  right: "дядько"
:::
"""
    items = extract_exercise_items(content)
    words = {i.word for i in items}
    assert "батьки" in words
    assert "дядько" in words
    # English words should not be extracted
    assert "parents" not in words
    assert "uncle" not in words


def test_extract_group_sort_items():
    content = """\
## Section

:::group-sort
title: "Sort"
---
groups:
  - name: "Чоловічий"
    items: ["стіл", "зошит"]
  - name: "Жіночий"
    items: ["книга", "ручка"]
:::
"""
    items = extract_exercise_items(content)
    words = {i.word for i in items}
    assert "стіл" in words
    assert "зошит" in words
    assert "книга" in words
    assert "ручка" in words
    assert "Чоловічий".lower() in words
    assert "Жіночий".lower() in words


def test_extract_true_false_items():
    content = """\
## Section

:::true-false
title: "True or false?"
---
- statement: "В українській мові 33 літери."
  answer: true
:::
"""
    items = extract_exercise_items(content)
    words = {i.word for i in items}
    assert "українській" in words
    assert "літери" in words


def test_no_exercises_returns_empty():
    content = "## Section\n\nJust prose, no exercises."
    items = extract_exercise_items(content)
    assert items == []


# --- extract_prose_words ---


def test_extract_prose_words_basic():
    content = """\
## Розділ

Це моя книга і мій стіл.

:::quiz
title: "Test"
---
- q: "What is зошит?"
  o: ["notebook", "pen", "table"]
  a: 0
:::
"""
    words = extract_prose_words(content)
    assert "книга" in words
    assert "стіл" in words
    assert "моя" in words
    # Exercise content should NOT be in prose words
    # (зошит only appears in exercise, not prose)
    assert "зошит" not in words


def test_extract_prose_words_strips_enrichment():
    content = """\
## Lesson

Мій телефон тут.

<!-- TAB:Словник -->

### Vocabulary table
| стілець | chair |
"""
    words = extract_prose_words(content)
    assert "телефон" in words
    # Words after TAB:Словник should NOT be included
    assert "стілець" not in words


def test_extract_prose_words_handles_stress_marks():
    content = "## Розділ\n\nМоя кімна\u0301та гарна."
    words = extract_prose_words(content)
    # Both with and without stress should match
    assert "кімната" in words


# --- extract_plan_vocab ---


def test_extract_plan_vocab():
    plan = {
        "vocabulary_hints": {
            "required": [
                "яблуко (apple)",
                "молоко (milk) — 3 syllables",
            ],
            "recommended": [
                "університет (university)",
            ],
        }
    }
    words = extract_plan_vocab(plan)
    assert "яблуко" in words
    assert "молоко" in words
    assert "університет" in words


def test_extract_plan_vocab_empty():
    assert extract_plan_vocab({}) == set()
    assert extract_plan_vocab({"vocabulary_hints": {}}) == set()


# --- verify_exercises ---


def test_verify_all_grounded():
    content = """\
## Розділ

Це моя книга і мій стіл. Мій зошит тут.

:::fill-in
title: "Test"
---
- sentence: "Це ___ книга."
  answer: "моя"
- sentence: "Це ___ стіл."
  answer: "мій"
:::
"""
    result = verify_exercises(content)
    assert result.all_grounded
    assert result.total_items > 0
    assert len(result.ungrounded) == 0


def test_verify_ungrounded_items():
    content = """\
## Розділ

Це моя книга.

:::fill-in
title: "Test"
---
- sentence: "Це ___ олівець."
  answer: "мій"
:::
"""
    result = verify_exercises(content)
    # "олівець" is NOT in the prose, so it should be ungrounded
    ungrounded_words = {u["word"] for u in result.ungrounded}
    assert "олівець" in ungrounded_words


def test_verify_with_plan_vocab():
    content = """\
## Розділ

Це моя книга. Мій олівець тут.

:::fill-in
title: "Test"
---
- sentence: "Це ___ олівець."
  answer: "мій"
:::
"""
    plan = {
        "vocabulary_hints": {
            "required": ["олівець (pencil)"],
        }
    }
    result = verify_exercises(content, plan)
    # All exercise words are in prose + plan vocab, so should be grounded
    assert result.all_grounded


def test_verify_vocab_coverage():
    content = """\
## Розділ

Це моя книга і стіл.

:::quiz
title: "Test"
---
- q: "Що це? **книга**"
  o: ["книга", "стіл"]
  a: 0
:::
"""
    plan = {
        "vocabulary_hints": {
            "required": ["книга (book)", "стіл (table)", "вікно (window)"],
        }
    }
    result = verify_exercises(content, plan)
    vc = result.vocab_coverage
    assert vc["plan_vocab_total"] == 3
    assert vc["tested_in_exercises"] >= 1  # at least книга + стіл
    assert "вікно" in vc["not_tested"]


# --- format_verify_result ---


def test_format_all_grounded():
    content = """\
## Розділ

Мій стіл тут.

:::fill-in
title: "Test"
---
- sentence: "Мій ___."
  answer: "стіл"
:::
"""
    result = verify_exercises(content)
    output = format_verify_result(result)
    assert "✅" in output
    assert "grounded" in output


def test_format_ungrounded():
    content = """\
## Розділ

Моя книга.

:::fill-in
title: "Test"
---
- sentence: "Мій ___."
  answer: "олівець"
:::
"""
    result = verify_exercises(content)
    output = format_verify_result(result)
    assert "⚠️" in output
    assert "олівець" in output


# --- Integration: real module content ---


def test_real_module_things_have_gender():
    """Smoke test against a real module if it exists."""
    module_path = (
        Path(__file__).resolve().parents[1]
        / "curriculum"
        / "l2-uk-en"
        / "a1"
        / "things-have-gender.md"
    )
    if not module_path.exists():
        return  # skip if not available

    content = module_path.read_text("utf-8")
    result = verify_exercises(content)

    # A well-built module should have most items grounded
    assert result.total_items > 0
    # Allow some ungrounded (e.g., meta-linguistic terms) but not too many
    grounded_ratio = result.grounded_items / result.total_items if result.total_items else 0
    assert grounded_ratio > 0.5, (
        f"Only {grounded_ratio:.0%} of exercise items grounded — expected > 50%"
    )
