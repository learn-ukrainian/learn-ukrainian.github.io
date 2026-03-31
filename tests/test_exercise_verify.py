"""Tests for exercise verification — grounding check for exercise items.

Issue: #1016
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build.exercise_verify import (
    extract_exercise_items,
    extract_exercise_items_from_yaml,
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

    # V6 modules use separate YAML activities (not inline DSL).
    # If no DSL exercises found, the test is not applicable.
    if result.total_items == 0:
        return  # V6 module — exercises are in activities/{slug}.yaml

    # A well-built module should have most items grounded
    assert result.total_items > 0
    # Allow some ungrounded (e.g., meta-linguistic terms) but not too many
    grounded_ratio = result.grounded_items / result.total_items if result.total_items else 0
    assert grounded_ratio > 0.5, (
        f"Only {grounded_ratio:.0%} of exercise items grounded — expected > 50%"
    )


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
    assert "читай" in words
    assert "друже" in words
    assert "читайте" in words
    assert "читати" in words


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
    assert "оленко" in words
    assert "підручник" in words
    assert "дай" in words
    assert "дайте" in words


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


def test_yaml_empty_activities():
    assert extract_exercise_items_from_yaml({}) == []
    assert extract_exercise_items_from_yaml({"inline": None, "workbook": None}) == []
    assert extract_exercise_items_from_yaml({"inline": [], "workbook": []}) == []


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
            "required": ["читати (to read)", "писати (to write)"],
        }
    }
    result = verify_exercises(content, plan, activities=activities)
    # Must find exercise items from YAML
    assert result.total_items > 0
    # "читати" from plan vocab should be found in exercise words
    assert result.vocab_coverage["tested_in_exercises"] > 0


def test_yaml_vocab_coverage():
    """Plan vocabulary tested_in_exercises should count words present in YAML activities."""
    content = "## Lesson\n\nЧитай, слухай, говори."
    activities = {
        "inline": [
            {
                "type": "fill-in",
                "items": [
                    {"sentence": "Учні, ___!", "answer": "читайте", "options": ["читайте", "читай"]},
                    {"sentence": "Друже, ___!", "answer": "слухай", "options": ["слухай", "слухайте"]},
                ],
            }
        ]
    }
    plan = {
        "vocabulary_hints": {
            "required": [
                "читати (to read)",
                "слухати (to listen)",
                "говорити (to speak)",
            ],
        }
    }
    result = verify_exercises(content, plan, activities=activities)
    vc = result.vocab_coverage
    assert vc["plan_vocab_total"] == 3
    # "читати" won't match "читайте" (different forms) but "слухай" contains "слухай"
    # The plan has lemmas, exercises have inflected forms — coverage checks exact match
    # Only "говорити" is not tested (no exercise uses it)
    assert "говорити" in vc["not_tested"]


def test_real_module_please_do_this_yaml():
    """Integration test: verify please-do-this with real YAML activities. Issue #1121."""
    import yaml as _yaml

    base = Path(__file__).resolve().parents[1] / "curriculum" / "l2-uk-en"
    content_path = base / "a1" / "please-do-this.md"
    activities_path = base / "a1" / "activities" / "please-do-this.yaml"
    plan_path = base / "plans" / "a1" / "please-do-this.yaml"

    if not all(p.exists() for p in (content_path, activities_path, plan_path)):
        return  # skip if files not available

    content = content_path.read_text("utf-8")
    activities = _yaml.safe_load(activities_path.read_text("utf-8"))
    plan = _yaml.safe_load(plan_path.read_text("utf-8"))

    result = verify_exercises(content, plan, activities=activities)

    # With YAML activities, we must find exercise items
    assert result.total_items > 0, "Should find exercise items from YAML"
    # Plan has 15 vocab words; with 4 exercises covering imperatives,
    # many should be tested
    assert result.vocab_coverage["tested_in_exercises"] > 0, (
        "tested_in_exercises must be > 0 with YAML activities (was the bug in #1121)"
    )
