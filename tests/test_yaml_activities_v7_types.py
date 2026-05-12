from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from yaml_activities import ActivityParser


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

