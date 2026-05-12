from __future__ import annotations

import yaml

from scripts.build.linear_pipeline import (
    _iter_vesum_word_surfaces,
    _normalize_for_vesum,
    _vesum_gate,
)


def test_reflexive_verb_not_split() -> None:
    text = (
        "вмиваюся прокидаєшся вмивається вмиваємося вмиваєтеся "
        "вмиваються ся сь тся ться шся 'навчаюся' прокидаюс'"
    )

    tokens = _iter_vesum_word_surfaces(text)

    assert tokens == [
        "вмиваюся",
        "прокидаєшся",
        "вмивається",
        "вмиваємося",
        "вмиваєтеся",
        "вмиваються",
        "навчаюся",
    ]
    assert not {"шся", "тся", "ться"} & set(tokens)


def test_compound_hyphen_word_not_split() -> None:
    text = "синьо-жовтий англо-український"

    tokens = _iter_vesum_word_surfaces(text)

    assert tokens == ["синьо-жовтий", "англо-український"]


def test_em_dash_splits_sentences() -> None:
    text = "Привіт — як справи?"

    tokens = _iter_vesum_word_surfaces(text)

    assert tokens == ["Привіт", "як", "справи"]


def test_normalize_for_vesum_strips_stress_and_markdown() -> None:
    assert _normalize_for_vesum("вмива́ю**ся**") == "вмиваюся"
    assert _normalize_for_vesum("вмива́ю") == "вмиваю"
    assert _normalize_for_vesum("**ся**") == "ся"
    assert _normalize_for_vesum("чу́до**в**") == "чудов"


def test_vesum_gate_normalizes_stress_and_markdown_before_lookup() -> None:
    seen: list[list[str]] = []

    def verify_words(words: list[str]) -> dict[str, list[dict[str, str]]]:
        seen.append(words)
        valid = {"вмиваюся", "вмиваю", "ся", "чудов"}
        return {word: ([{"lemma": word}] if word in valid else []) for word in words}

    gate = _vesum_gate(
        module_text="вмива́ю**ся** вмива́ю **ся** чу́до**в**",
        activities=[],
        vocabulary=[],
        resources=[],
        verify_words_fn=verify_words,
    )

    assert gate["passed"] is True
    assert seen == [["вмиваю", "вмиваюся", "ся", "чудов"]]
    assert gate["missing"] == []


def test_vesum_gate_missing_report_preserves_decorated_surface() -> None:
    def verify_words(words: list[str]) -> dict[str, list[dict[str, str]]]:
        assert words == ["вмиваюся"]
        return {word: [] for word in words}

    gate = _vesum_gate(
        module_text="вмива́ю**ся**",
        activities=[],
        vocabulary=[],
        resources=[],
        verify_words_fn=verify_words,
    )

    assert gate["passed"] is False
    assert gate["missing"] == ["вмива́ю**ся**"]


def test_proper_noun_genitive_resolves() -> None:
    seen: list[list[str]] = []

    def verify_words(words: list[str]) -> dict[str, list[dict[str, str]]]:
        seen.append(words)
        return {
            word: (
                [{"lemma": word}]
                if word in {"вірш", "Білоуса", "Дмитра"}
                else []
            )
            for word in words
        }

    gate = _vesum_gate(
        module_text="Вірш Дмитра Білоуса.",
        activities=[],
        vocabulary=[],
        resources=[],
        verify_words_fn=verify_words,
    )

    assert gate["passed"] is True
    assert seen == [["білоуса", "вірш", "дмитра"], ["Білоуса", "Дмитра"]]


def test_unknown_capitalized_name_stays_missing() -> None:
    def verify_words(words: list[str]) -> dict[str, list[dict[str, str]]]:
        return {word: [] for word in words}

    gate = _vesum_gate(
        module_text="Дрімлюша Драбадана тут немає.",
        activities=[],
        vocabulary=[],
        resources=[],
        verify_words_fn=verify_words,
    )

    assert gate["passed"] is False
    assert gate["missing"] == ["Драбадана", "Дрімлюша", "немає", "тут"]


def test_my_morning_module_passes_vesum_gate() -> None:
    module_text = """
## Діалог
— Коли ти прокидаєшся?
— Я прокидаюся о сьомій і вмиваюся.

У вправі є форма Дмитра Білоуса.
"""
    activities = yaml.safe_load(
        """
- id: a1-20-reflexive-postfix
  type: fill-in
  items:
    - sentence: Я вмиваю__ о сьомій.
      answer: ся
      options: [ся, сь, тся]
    - sentence: Він прокидаєть__ пізно.
      answer: ся
      options: [ся, сь, шся]
    - sentence: Вона вмиваєть__ холодною водою.
      answer: ся
      options: [ся, сь, ться]
"""
    )

    def verify_words(words: list[str]) -> dict[str, list[dict[str, str]]]:
        valid = {
            "коли",
            "ти",
            "прокидаєшся",
            "прокидаюся",
            "сьомій",
            "вмиваюся",
            "вправі",
            "він",
            "вона",
            "форма",
            "діалог",
            "пізно",
            "холодною",
            "водою",
        }
        original_case_valid = {"Білоуса", "Дмитра"}
        return {
            word: (
                [{"lemma": word}]
                if word in valid or word in original_case_valid
                else []
            )
            for word in words
        }

    gate = _vesum_gate(
        module_text=module_text,
        activities=activities,
        vocabulary=[],
        resources=[],
        verify_words_fn=verify_words,
    )

    assert gate["passed"] is True
    assert gate["missing"] == []
