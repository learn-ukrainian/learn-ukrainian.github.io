from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from yaml_activities import ActivityParser, OrderActivity


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
    - options: [сильніший, молодший, більш цікавий, дорожчий]
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
    assert "<OddOneOut" in parser.to_mdx(activities)


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
