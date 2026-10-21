"""Tests for exercise verification — grounding check for exercise items.

Issue: #1016
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.reads_content

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build.exercise_verify import (
    extract_exercise_items,
    extract_exercise_items_from_yaml,
    extract_plan_vocab,
    extract_prose_words,
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


# --- verify_exercises ---


# --- format_verify_result ---


# --- Integration: real module content ---


# --- extract_exercise_items_from_yaml (V6 YAML activities) ---


def test_yaml_fill_in():
    activities = {
        "inline": [
            {
                "type": "fill-in",
                "items": [
                    {"sentence": "Друже, ___ цей текст!", "answer": "читай", "options": ["читай", "читайте", "читати"]},
                ],
            }
        ]
    }
    items = extract_exercise_items_from_yaml(activities)
    words = {i.word for i in items}
    assert "читай" in words   # answer — extracted
    assert "друже" in words    # sentence context — extracted
    # Options (distractors) are intentionally skipped — they include wrong answers
    assert "читайте" not in words
    assert "читати" not in words


def test_yaml_quiz():
    activities = {
        "inline": [
            {
                "type": "quiz",
                "items": [
                    {"question": "Оленко, ___ мені підручник!", "options": ["дайте", "дати", "дай"], "correct": 2},
                ],
            }
        ]
    }
    items = extract_exercise_items_from_yaml(activities)
    words = {i.word for i in items}
    assert "оленко" in words      # question context — extracted
    assert "підручник" in words    # question context — extracted
    # Options (mix of correct + distractors) are skipped — can't distinguish
    assert "дай" not in words
    assert "дайте" not in words


def test_yaml_match_up():
    activities = {
        "workbook": [
            {
                "type": "match-up",
                "pairs": [
                    {"left": "читати", "right": "читай"},
                    {"left": "писати", "right": "пиши"},
                ],
            }
        ]
    }
    items = extract_exercise_items_from_yaml(activities)
    words = {i.word for i in items}
    assert "читати" in words
    assert "читай" in words
    assert "писати" in words
    assert "пиши" in words


def test_yaml_group_sort():
    activities = {
        "inline": [
            {
                "type": "group-sort",
                "groups": [
                    {"label": "Ти-форма", "items": ["читай", "пиши"]},
                    {"label": "Ви-форма", "items": ["читайте", "пишіть"]},
                ],
            }
        ]
    }
    items = extract_exercise_items_from_yaml(activities)
    words = {i.word for i in items}
    assert "читай" in words
    assert "пиши" in words
    assert "читайте" in words
    assert "пишіть" in words


def test_yaml_true_false():
    activities = {
        "workbook": [
            {
                "type": "true-false",
                "items": [
                    {"statement": "Вчителька використовує ви-форми.", "correct": True},
                ],
            }
        ]
    }
    items = extract_exercise_items_from_yaml(activities)
    words = {i.word for i in items}
    assert "вчителька" in words
    assert "використовує" in words


def test_yaml_error_correction():
    activities = {
        "workbook": [
            {
                "type": "error-correction",
                "items": [
                    {
                        "sentence": "Вчителю, читай текст!",
                        "error": "читай",
                        "correction": "читайте",
                        "options": ["читайте", "читати"],
                    },
                ],
            }
        ]
    }
    items = extract_exercise_items_from_yaml(activities)
    words = {i.word for i in items}
    assert "читайте" in words  # correction
    assert "вчителю" in words  # sentence


def test_yaml_order():
    activities = {
        "inline": [
            {
                "type": "order",
                "items": [
                    {"segments": ["Добрий", "ранок", "пане", "Іване"]},
                ],
            }
        ]
    }
    items = extract_exercise_items_from_yaml(activities)
    words = {i.word for i in items}
    assert "добрий" in words
    assert "ранок" in words
    assert "пане" in words


def test_yaml_no_exercises_in_markdown_but_yaml_provided():
    """Bug #1121: verify_exercises should use YAML activities when provided."""
    content = "## Lesson\n\nЧитай книжку. Пиши речення."
    activities = {
        "inline": [
            {
                "type": "fill-in",
                "items": [
                    {"sentence": "Друже, ___ книжку!", "answer": "читай", "options": ["читай", "читати"]},
                ],
            }
        ]
    }
    plan = {
        "vocabulary_hints": {
            "required": ["читай (read — imperative)", "писати (to write)"],
        }
    }
    result = verify_exercises(content, plan, activities=activities)
    # Must find exercise items from YAML (answer + sentence context)
    assert result.total_items > 0
    # "читай" from plan vocab is the answer in the fill-in exercise
    assert result.vocab_coverage["tested_in_exercises"] > 0
