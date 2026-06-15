from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from jsonschema import Draft7Validator

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from yaml_activities import ActivityParser, OrderActivity


def _a1_schema_validator() -> Draft7Validator:
    schema_path = Path(__file__).parent.parent / "schemas" / "activities-a1.schema.json"
    return Draft7Validator(json.loads(schema_path.read_text(encoding="utf-8")))


def test_v7_authoring_types_parse_and_render(tmp_path):
    fixture = tmp_path / "activities.yaml"
    fixture.write_text(
        """
- id: observe-1
  type: observe
  title: Observe
  instruction: Notice the pattern.
  prompt: What changes?
  examples:
    - text: мию → миюся
    - text: одягаю → одягаюся
- id: order-1
  type: order
  title: Order
  instruction: Put the actions in order.
  items: [прокидатися, вмиватися, снідати]
  correct_order: [0, 1, 2]
- id: count-1
  type: count-syllables
  title: Count
  instruction: Count syllables.
  maxCount: 5
  items:
    - word: молоко
      correct: 3
      translation: milk
- id: divide-1
  type: divide-words
  title: Divide
  instruction: Divide words.
  items:
    - word: молоко
      answer: мо-ло-ко
- id: morphemes-1
  type: highlight-morphemes
  title: Morphemes
  instruction: Find suffixes.
  text: прокидаюся вмиваюся
  items:
    - word: прокидаюся
      morphemes:
        - morpheme: ся
          type: suffix
- id: grid-1
  type: letter-grid
  title: Letters
  letters:
    - upper: А
      lower: а
      emoji: 🍉
      key_word: кавун
      sound_type: vowel
- id: odd-1
  type: odd-one-out
  title: Odd
  instruction: Pick the odd word.
  items:
    - words: [кава, чай, хліб, вода]
      correct: 2
      explanation: Хліб is not a drink.
- id: pick-1
  type: pick-syllables
  title: Pick
  instruction: Pick open syllables.
  syllables: [ма, мок, ко]
  correctIndices: [0, 2]
  category: відкриті
  explanation: Open syllables end in vowels.
""",
        encoding="utf-8",
    )

    parser = ActivityParser()
    activities = parser.parse(fixture)
    assert [activity.type for activity in activities] == [
        "observe",
        "order",
        "count-syllables",
        "divide-words",
        "highlight-morphemes",
        "letter-grid",
        "odd-one-out",
        "pick-syllables",
    ]

    mdx = parser.to_mdx(activities)
    for tag in (
        "<Observe",
        "<Order",
        "<CountSyllables",
        "<DivideWords",
        "<HighlightMorphemes",
        "<LetterGrid",
        "<OddOneOut",
        "<PickSyllables",
    ):
        assert tag in mdx

    assert '### Letters' in mdx
    assert '<LetterGrid client:only=\'react\'' in mdx
    assert 'title="Letters"' not in mdx
    assert "ActivityPlaceholder" not in mdx


def test_order_accepts_item_string_permutation_as_correct_order(tmp_path):
    """Writers (codex on m20 act-3) express order answers as the ordered ITEM
    STRINGS rather than integer indices. When correct_order is an exact
    permutation of unique items, the parser resolves it to indices instead of
    HARD-failing at MDX assembly with 'correct_order must contain integers'.
    """
    fixture = tmp_path / "order.yaml"
    fixture.write_text(
        """
- id: order-strings
  type: order
  title: Order
  instruction: Put the morning routine in order.
  items:
    - "Потім я вмиваюся."
    - "Нарешті я йду на роботу."
    - "Спочатку я прокидаюся."
    - "Після цього я снідаю."
  correct_order:
    - "Спочатку я прокидаюся."
    - "Потім я вмиваюся."
    - "Після цього я снідаю."
    - "Нарешті я йду на роботу."
""",
        encoding="utf-8",
    )
    parser = ActivityParser()
    activities = parser.parse(fixture)
    order_activity = activities[0]
    assert isinstance(order_activity, OrderActivity)
    assert order_activity.correct_order == [2, 0, 3, 1]
    assert "<Order" in parser.to_mdx(activities)


def test_order_preserves_activity_ukrainian_flag(tmp_path):
    fixture = tmp_path / "order_ukrainian.yaml"
    fixture.write_text(
        """
- id: order-uk
  type: order
  title: Order
  instruction: Put the lines in order.
  is_ukrainian: true
  items:
    - "Привіт!"
    - "Як справи?"
  correct_order: [0, 1]
""",
        encoding="utf-8",
    )

    parser = ActivityParser()
    activities = parser.parse(fixture)

    assert isinstance(activities[0], OrderActivity)
    assert activities[0].is_ukrainian is True
    assert "isUkrainian={true}" in parser.to_mdx(activities)


def test_count_syllables_accepts_snake_case_max_count(tmp_path):
    fixture = tmp_path / "count.yaml"
    fixture.write_text(
        """
- id: count-1
  type: count-syllables
  title: Count
  max_count: 4
  items:
    - word: молоко
      correct: 3
""",
        encoding="utf-8",
    )

    parser = ActivityParser()
    activities = parser.parse(fixture)

    assert activities[0].max_count == 4
    assert "maxCount={4}" in parser.to_mdx(activities)


def test_translate_renderer_preserves_explanations(tmp_path):
    fixture = tmp_path / "translate.yaml"
    fixture.write_text(
        """
- id: translate-1
  type: translate
  title: Meanings
  items:
    - source: Привіт!
      options:
        - text: Hi!
          correct: true
        - text: Goodbye!
          correct: false
      explanation: Привіт is informal.
""",
        encoding="utf-8",
    )

    parser = ActivityParser()
    mdx = parser.to_mdx(parser.parse(fixture))

    assert "<Translate" in mdx
    assert "Привіт is informal." in mdx


def test_core_a1_renderers_preserve_instruction_and_quiz_anchor(tmp_path):
    fixture = tmp_path / "core.yaml"
    fixture.write_text(
        """
- id: quiz-1
  type: quiz
  title: Quiz title
  anchor_id: repair-quiz
  instruction: Choose the best reply.
  items:
    - question: Привіт!
      options:
        - text: Hi!
          correct: true
        - text: Bye!
          correct: false
- id: true-false-1
  type: true-false
  title: Check
  instruction: Decide if the sentence is natural.
  items:
    - statement: Це місто.
      correct: true
- id: fill-in-1
  type: fill-in
  title: Complete
  instruction: Choose the missing word.
  items:
    - sentence: Я ____ каву.
      answer: п'ю
      options: [п'ю, їм]
- id: match-1
  type: match-up
  title: Match
  instruction: Match each situation with a phrase.
  pairs:
    - left: greeting
      right: Привіт
    - left: thanks
      right: Дякую
- id: sort-1
  type: group-sort
  title: Sort
  instruction: Sort the phrases.
  groups:
    - name: food
      items: [хліб]
    - name: drink
      items: [вода]
- id: translate-1
  type: translate
  title: Translate
  instruction: Choose the Ukrainian phrase.
  items:
    - source: Thank you.
      options:
        - text: Дякую.
          correct: true
        - text: Бувай.
          correct: false
- id: unjumble-1
  type: unjumble
  title: Build
  instruction: Put the words in order.
  items:
    - jumbled: Я / п'ю / воду
      answer: Я п'ю воду
- id: anagram-1
  type: anagram
  title: Letters
  instruction: Unscramble the word.
  items:
    - letters: [к, а, в, а]
      answer: кава
""",
        encoding="utf-8",
    )

    parser = ActivityParser()
    mdx = parser.to_mdx(parser.parse(fixture))

    assert '<span id="repair-quiz"></span>' in mdx
    for instruction in (
        'instruction={"Choose the best reply."}',
        'instruction={"Decide if the sentence is natural."}',
        'instruction={"Choose the missing word."}',
        'instruction={"Match each situation with a phrase."}',
        'instruction={"Sort the phrases."}',
        'instruction={"Choose the Ukrainian phrase."}',
        'instruction={"Put the words in order."}',
        'instruction={"Unscramble the word."}',
    ):
        assert instruction in mdx


def test_watch_and_repeat_renderer_preserves_instruction(tmp_path):
    fixture = tmp_path / "watch.yaml"
    fixture.write_text(
        """
- id: watch-1
  type: watch-and-repeat
  title: Repeat
  instruction: Watch once, then repeat aloud.
  items:
    - video: https://youtu.be/dQw4w9WgXcQ
      letter: А
      word: мама
      sound: /a/
""",
        encoding="utf-8",
    )

    parser = ActivityParser()
    mdx = parser.to_mdx(parser.parse(fixture))

    assert "<WatchAndRepeat" in mdx
    assert 'instruction={"Watch once, then repeat aloud."}' in mdx


def test_a1_schema_accepts_unjumble_parser_aliases():
    data = [
        {
            "type": "unjumble",
            "instruction": "Put the words in order.",
            "items": [
                {"jumbled": "Я / читаю", "answer": "Я читаю"},
                {"prompt": ["Ти", "пишеш"], "answer": "Ти пишеш"},
                {"scrambled": "Він їсть", "answer": "Він їсть"},
            ],
        }
    ]

    errors = list(_a1_schema_validator().iter_errors(data))

    assert errors == []


def test_a1_schema_rejects_quiz_string_options_without_answer():
    data = [
        {
            "type": "quiz",
            "instruction": "Choose one.",
            "items": [
                {
                    "question": "Which one?",
                    "options": ["Так", "Ні"],
                }
            ],
        }
    ]

    errors = list(_a1_schema_validator().iter_errors(data))

    assert errors


def test_order_still_rejects_non_permutation_strings(tmp_path):
    """A string correct_order that is NOT an exact permutation of items must
    still fail (no silent coercion of bogus answers)."""
    fixture = tmp_path / "order_bad.yaml"
    fixture.write_text(
        """
- id: order-bad
  type: order
  title: Order
  instruction: Order them.
  items: ["a", "b", "c"]
  correct_order: ["a", "b", "zzz"]
""",
        encoding="utf-8",
    )
    parser = ActivityParser()
    # parse() wraps the per-activity TypeError in a ValueError context.
    with pytest.raises(ValueError, match="must contain integers"):
        parser.parse(fixture)


def test_grammar_identify_accepts_sentence_alias(tmp_path):
    fixture = tmp_path / "grammar.yaml"
    fixture.write_text(
        """
- id: grammar-1
  type: grammar-identify
  title: Конструкція
  instruction: Визначте модель порівняння.
  items:
    - sentence: Петро вищий за Марію.
      answer: за + знахідний відмінок
""",
        encoding="utf-8",
    )

    parser = ActivityParser()
    activities = parser.parse(fixture)

    assert activities[0].items[0].text == "Петро вищий за Марію."
    assert activities[0].items[0].form == "Визначте модель порівняння."
    assert "<GrammarIdentify" in parser.to_mdx(activities)


def test_grammar_identify_requires_text_sentence_or_word(tmp_path):
    fixture = tmp_path / "grammar.yaml"
    fixture.write_text(
        """
- id: grammar-1
  type: grammar-identify
  title: Конструкція
  instruction: Визначте модель порівняння.
  items:
    - answer: за + знахідний відмінок
""",
        encoding="utf-8",
    )

    parser = ActivityParser()

    with pytest.raises(ValueError, match="requires text, sentence, or word"):
        parser.parse(fixture)


def test_odd_one_out_accepts_options_answer_alias(tmp_path):
    fixture = tmp_path / "odd.yaml"
    fixture.write_text(
        """
- id: odd-1
  type: odd-one-out
  title: Зайва форма
  instruction: Оберіть форму, яка не належить до групи.
  items:
    - prompt: Прості форми
      options: [сильніший, молодший, більш цікавий, дорожчий]
      answer: більш цікавий
      explanation: Це складена форма, решта прості.
""",
        encoding="utf-8",
    )

    parser = ActivityParser()
    activities = parser.parse(fixture)

    assert activities[0].items[0].words == [
        "сильніший",
        "молодший",
        "більш цікавий",
        "дорожчий",
    ]
    assert activities[0].items[0].correct == 2
    assert activities[0].items[0].prompt == "Прості форми"
    mdx = parser.to_mdx(activities)
    assert "<OddOneOut" in mdx
    assert '"prompt": "Прості форми"' in mdx


def test_highlight_morphemes_accepts_answer_alias(tmp_path):
    fixture = tmp_path / "morphemes.yaml"
    fixture.write_text(
        """
- id: morphemes-1
  type: highlight-morphemes
  title: Суфікси
  instruction: Позначте суфікс.
  text: сильніший
  items:
    - word: сильніший
      answer: -іш-
""",
        encoding="utf-8",
    )

    parser = ActivityParser()
    activities = parser.parse(fixture)

    assert activities[0].morphemes[0].word == "сильніший"
    assert activities[0].morphemes[0].morpheme == "-іш-"
    assert activities[0].morphemes[0].type == "suffix"
    assert "<HighlightMorphemes" in parser.to_mdx(activities)
