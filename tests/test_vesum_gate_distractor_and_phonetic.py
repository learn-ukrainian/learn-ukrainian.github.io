"""Regression tests for VESUM gate false-positive classes."""

from __future__ import annotations

from scripts.build.linear_pipeline import _vesum_gate


def test_mc_distractor_text_not_verified() -> None:
    """correct: false option text must not be checked against VESUM."""
    activity = {
        "type": "multiple-choice",
        "questions": [
            {
                "question": "Я ___ каву.",
                "options": [
                    {"text": "п'ю", "correct": True},
                    {"text": "п'юся", "correct": False},
                    {"text": "п'єшся", "correct": False},
                ],
            }
        ],
    }
    sent_for_verification: set[str] = set()

    def verify_words(words: list[str]) -> dict[str, list[dict[str, str]]]:
        sent_for_verification.update(words)
        return {word: [{"lemma": word}] for word in words}

    _vesum_gate(
        module_text="",
        activities=[activity],
        vocabulary=[],
        resources=[],
        verify_words_fn=verify_words,
    )

    assert "п'юся" not in sent_for_verification
    assert "п'єшся" not in sent_for_verification


def test_correct_option_text_still_verified() -> None:
    """correct: true option text must still be checked."""
    activity = {
        "type": "multiple-choice",
        "questions": [
            {
                "question": "Я ___ каву.",
                "options": [
                    {"text": "п'ю", "correct": True},
                    {"text": "п'юся", "correct": False},
                ],
            }
        ],
    }
    sent_for_verification: set[str] = set()

    def verify_words(words: list[str]) -> dict[str, list[dict[str, str]]]:
        sent_for_verification.update(words)
        return {word: [{"lemma": word}] for word in words}

    _vesum_gate(
        module_text="",
        activities=[activity],
        vocabulary=[],
        resources=[],
        verify_words_fn=verify_words,
    )

    assert "п'ю" in sent_for_verification


def test_error_correction_sentence_not_verified() -> None:
    """error-correction sentence text contains the deliberate wrong form."""
    activity = {
        "type": "error-correction",
        "items": [
            {
                "sentence": "Я снідаюся о восьмій.",
                "errors": ["снідаюся"],
                "corrected": "Я снідаю о восьмій.",
            }
        ],
    }
    sent_for_verification: set[str] = set()

    def verify_words(words: list[str]) -> dict[str, list[dict[str, str]]]:
        sent_for_verification.update(words)
        return {word: [{"lemma": word}] for word in words}

    result = _vesum_gate(
        module_text="",
        activities=[activity],
        vocabulary=[],
        resources=[],
        verify_words_fn=verify_words,
    )

    assert result["passed"] is True
    assert "снідаюся" not in sent_for_verification


def test_dialect_abbreviation_not_verified() -> None:
    """Textbook abbreviation `діал.` is metadata, not a VESUM lemma."""
    sent_for_verification: set[str] = set()

    def verify_words(words: list[str]) -> dict[str, list[dict[str, str]]]:
        sent_for_verification.update(words)
        return {word: [{"lemma": word}] for word in words}

    result = _vesum_gate(
        module_text="Я ся не бою (діал.).",
        activities=[],
        vocabulary=[],
        resources=[],
        verify_words_fn=verify_words,
    )

    assert result["passed"] is True
    assert "діал" not in sent_for_verification


def test_pronunciation_transcription_stripped_in_prose() -> None:
    """A bold phonetic form following 'sounds like' must not hit VESUM."""
    module_text = (
        "The spelling **вмиваєшся** sounds like **вмиваєсся**, and "
        "**вмивається** sounds like **вмиваєцця**."
    )
    sent_for_verification: set[str] = set()

    def verify_words(words: list[str]) -> dict[str, list[dict[str, str]]]:
        sent_for_verification.update(words)
        return {word: [{"lemma": word}] for word in words}

    _vesum_gate(
        module_text=module_text,
        activities=[],
        vocabulary=[],
        resources=[],
        verify_words_fn=verify_words,
    )

    assert "вмиваєсся" not in sent_for_verification
    assert "вмиваєцця" not in sent_for_verification
    assert "вмиваєшся" in sent_for_verification


def test_isolated_misspelling_still_caught() -> None:
    """A non-standard form outside a transcription context must be flagged."""
    module_text = "She написала вмиваєсся without context."

    def verify_words(words: list[str]) -> dict[str, list[dict[str, str]]]:
        return {word: [] for word in words}

    result = _vesum_gate(
        module_text=module_text,
        activities=[],
        vocabulary=[],
        resources=[],
        verify_words_fn=verify_words,
    )

    assert "вмиваєсся" in result["missing"]
