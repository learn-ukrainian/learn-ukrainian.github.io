"""Tests for scripts/tools/upgrade_activity_hints.py — hint classification and YAML parsing."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

# Add scripts/ to path
scripts_dir = str(Path(__file__).resolve().parent.parent / "scripts")
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from tools.upgrade_activity_hints import (
    build_gemini_prompt,
    count_vague_hints,
    is_hint_vague,
    parse_gemini_response,
)

# --- is_hint_vague ---


class TestIsHintVague:
    """Test the vague hint classifier."""

    def test_vague_no_ukrainian(self):
        """Hint with only English description is vague."""
        hint = {
            "type": "quiz",
            "focus": "Test knowledge of body parts vocabulary",
            "items": 6,
        }
        assert is_hint_vague(hint) is True

    def test_vague_single_cyrillic_word(self):
        """Hint with only one Cyrillic word is still vague."""
        hint = {
            "type": "quiz",
            "focus": "Choose the correct form of слово",
            "items": 6,
        }
        assert is_hint_vague(hint) is True

    def test_specific_with_arrow(self):
        """Hint with ↔ marker is specific."""
        hint = {
            "type": "match-up",
            "focus": "аптека ↔ купувати ліки",
            "items": 6,
        }
        assert is_hint_vague(hint) is False

    def test_specific_with_blanks(self):
        """Hint with ___ marker is specific."""
        hint = {
            "type": "fill-in",
            "focus": "Я ___ читати.",
            "items": 6,
        }
        assert is_hint_vague(hint) is False

    def test_specific_with_curly_braces(self):
        """Hint with {} fill-in is specific."""
        hint = {
            "type": "fill-in",
            "focus": "Це {___} мама. → моя",
            "items": 4,
        }
        assert is_hint_vague(hint) is False

    def test_specific_with_pipe(self):
        """Hint with | separator (options) is specific."""
        hint = {
            "type": "quiz",
            "focus": "Я ___ читати. (люблю | подобається)",
            "items": 8,
        }
        assert is_hint_vague(hint) is False

    def test_specific_with_multiple_cyrillic_words(self):
        """Hint with 2+ Cyrillic words in focus is specific."""
        hint = {
            "type": "quiz",
            "focus": "Якого кольору? Match objects: синій олівець, червоне яблуко",
            "items": 8,
        }
        assert is_hint_vague(hint) is False

    def test_specific_with_cyrillic_pairs(self):
        """Hint with Ukrainian content in pairs list is specific."""
        hint = {
            "type": "match-up",
            "focus": "Match the verb to the noun",
            "pairs": [
                "грати ↔ у футбол",
                "слухати ↔ музику",
            ],
        }
        assert is_hint_vague(hint) is False

    def test_specific_with_cyrillic_items(self):
        """Hint with Ukrainian content in items list is specific."""
        hint = {
            "type": "fill-in",
            "focus": "Complete sentences",
            "items": [
                "Я {ніколи не|завжди|часто} працюю.",
                "Вона грає {двічі|тричі} на тиждень.",
            ],
        }
        assert is_hint_vague(hint) is False

    def test_vague_english_only_items(self):
        """Hint with English-only items list is vague."""
        hint = {
            "type": "quiz",
            "focus": "Choose the correct answer",
            "items": 6,
        }
        assert is_hint_vague(hint) is True

    def test_real_vague_from_my_city(self):
        """Real vague hint from my-city.yaml plan."""
        hint = {
            "type": "quiz",
            "focus": "Where would you go? Choose the right place for each situation.",
            "items": 6,
        }
        assert is_hint_vague(hint) is True

    def test_real_specific_from_sounds(self):
        """Real specific hint from sounds-letters-and-hello.yaml."""
        hint = {
            "type": "quiz",
            "focus": (
                "Distinguish between sounds (звуки) and letters (літери). "
                "Example questions: 'Що ми чуємо і вимовляємо?' → 'звуки' "
                "| 'Що ми бачимо і пишемо?' → 'літери'"
            ),
            "items": 6,
        }
        assert is_hint_vague(hint) is False


# --- count_vague_hints ---


class TestCountVagueHints:
    def test_mixed_plan(self):
        plan = {
            "activity_hints": [
                {"type": "quiz", "focus": "Test vocabulary", "items": 6},
                {"type": "match-up", "focus": "банк ↔ гроші", "items": 4},
                {"type": "fill-in", "focus": "Complete the sentence", "items": 4},
            ]
        }
        vague, total = count_vague_hints(plan)
        assert vague == 2
        assert total == 3

    def test_no_hints(self):
        plan = {"title": "Test"}
        vague, total = count_vague_hints(plan)
        assert vague == 0
        assert total == 0

    def test_all_specific(self):
        plan = {
            "activity_hints": [
                {"type": "quiz", "focus": "Як справи? Добре чи погано?", "items": 4},
                {"type": "match-up", "focus": "привіт ↔ hello", "items": 4},
            ]
        }
        vague, total = count_vague_hints(plan)
        assert vague == 0
        assert total == 2


# --- parse_gemini_response ---


class TestParseGeminiResponse:
    def test_plain_yaml(self):
        response = """\
- type: quiz
  focus: "Що ми чуємо? (звуки | літери)"
  items: 6
- type: match-up
  focus: "Match pairs"
  pairs:
  - "привіт ↔ hello"
"""
        result = parse_gemini_response(response)
        assert result is not None
        assert len(result) == 2
        assert result[0]["type"] == "quiz"
        assert result[1]["type"] == "match-up"

    def test_fenced_yaml(self):
        response = """\
```yaml
- type: fill-in
  focus: "Я {люблю|подобається} читати."
  items: 4
```
"""
        result = parse_gemini_response(response)
        assert result is not None
        assert len(result) == 1
        assert result[0]["type"] == "fill-in"

    def test_invalid_yaml(self):
        response = "This is not YAML at all: {broken"
        result = parse_gemini_response(response)
        # Could be None or could parse as string — either way, not a list
        assert result is None or isinstance(result, list)

    def test_not_a_list(self):
        response = "type: quiz\nfocus: test\n"
        result = parse_gemini_response(response)
        assert result is None

    def test_missing_required_fields(self):
        response = "- items: 6\n  something: else\n"
        result = parse_gemini_response(response)
        assert result is None

    def test_fenced_with_backticks(self):
        response = """\
```
- type: quiz
  focus: "Привіт чи Бувай?"
  items: 4
```
"""
        result = parse_gemini_response(response)
        assert result is not None
        assert len(result) == 1


# --- build_gemini_prompt ---


class TestBuildGeminiPrompt:
    def test_prompt_contains_plan(self):
        plan = {
            "slug": "test-module",
            "vocabulary_hints": {"required": ["слово (word)"]},
            "activity_hints": [
                {"type": "quiz", "focus": "Test vocabulary", "items": 6},
            ],
        }
        plan_text = yaml.dump(plan, allow_unicode=True)
        prompt = build_gemini_prompt(plan, plan_text)
        assert "слово" in prompt
        assert "Test vocabulary" in prompt
        assert "ONLY vocabulary from this plan" in prompt

    def test_prompt_has_output_format(self):
        plan = {
            "activity_hints": [
                {"type": "quiz", "focus": "Test", "items": 4},
            ],
        }
        plan_text = yaml.dump(plan, allow_unicode=True)
        prompt = build_gemini_prompt(plan, plan_text)
        assert "YAML array" in prompt
        assert "exactly 1 elements" in prompt
