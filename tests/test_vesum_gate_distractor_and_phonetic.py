"""Regression tests for VESUM gate false-positive classes."""

from __future__ import annotations

from scripts.build.linear_pipeline import (
    _bad_form_heritage_gate,
    _build_vesum_text,
    _vesum_gate,
)


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


def test_highlight_morphemes_answer_key_not_verified() -> None:
    """highlight-morphemes `morphemes:` values are bare answer-key fragments."""
    activity = {
        "type": "highlight-morphemes",
        "text": "обрядовість посівання колядування веснянка",
        "items": [
            {"word": "веснянка", "morphemes": ["весн", "янк", "а"]},
            {"word": "колядування", "morphemes": ["коляд", "ува", "ння"]},
            {"word": "посівання", "morphemes": ["по", "сів", "ання"]},
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
    assert result["missing"] == []
    assert {"весн", "янк", "коляд", "ува", "ння", "сів", "ання"}.isdisjoint(
        sent_for_verification
    )
    assert {"обрядовість", "посівання", "колядування", "веснянка"}.issubset(
        sent_for_verification
    )


def test_highlight_morphemes_text_still_verified() -> None:
    """A bad form in highlight-morphemes `text:` still fails VESUM."""
    activity = {
        "type": "highlight-morphemes",
        "text": "веснянка дивюся",
        "items": [
            {"word": "веснянка", "morphemes": ["весн", "янк", "а"]},
        ],
    }
    sent_for_verification: set[str] = set()

    def verify_words(words: list[str]) -> dict[str, list[dict[str, str]]]:
        sent_for_verification.update(words)
        return {
            word: ([{"lemma": word}] if word == "веснянка" else [])
            for word in words
        }

    result = _vesum_gate(
        module_text="",
        activities=[activity],
        vocabulary=[],
        resources=[],
        verify_words_fn=verify_words,
    )

    assert result["passed"] is False
    assert result["missing"] == ["дивюся"]
    assert "дивюся" in sent_for_verification
    assert {"весн", "янк"}.isdisjoint(sent_for_verification)


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


def test_aspect_abbreviations_not_verified() -> None:
    """Grammar abbreviations `недок.` and `док.` are metadata, not lemmas."""
    sent_for_verification: set[str] = set()

    def verify_words(words: list[str]) -> dict[str, list[dict[str, str]]]:
        sent_for_verification.update(words)
        return {word: [{"lemma": word}] for word in words}

    result = _vesum_gate(
        module_text="Писати (недок.) і написати (док.) утворюють видову пару.",
        activities=[],
        vocabulary=[],
        resources=[],
        verify_words_fn=verify_words,
    )

    assert result["passed"] is True
    assert "недок" not in sent_for_verification
    assert "док" not in sent_for_verification


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


def test_build_vesum_text_strips_bad_marker_and_verify_comment_args() -> None:
    """Cyrillic inside bad markers and VERIFY comments is not learner prose."""
    module_text = (
        "the form <!-- bad -->одіватися<!-- /bad --> is not used "
        "<!-- VERIFY: check_russian_shadow(word='одіватися') -->"
    )

    text = _build_vesum_text(module_text, [], [], [])

    assert "одіватися" not in text


def test_bad_marker_form_stays_excluded_before_comment_stripping() -> None:
    """Bad marker ordering must remove the inner bad form before HTML comments."""
    text = _build_vesum_text(
        "Use одягатися, not <!-- bad -->одіватися<!-- /bad -->.",
        [],
        [],
        [],
    )

    assert "одягатися" in text
    assert "одіватися" not in text


def test_bad_form_heritage_ignores_unrelated_authentic_hits() -> None:
    """A noisy heritage search hit must not block an unrelated bad marker."""
    result = _bad_form_heritage_gate(
        module_text="Кажи <!-- bad -->несу́чий<!-- /bad --> лише як помилковий зразок.",
        activities=[],
        vocabulary=[],
        resources=[],
        heritage_lookup_fn=lambda _query: [
            {
                "word": "фосфор",
                "is_authentic_ukrainian": True,
                "source_family": "esum",
            }
        ],
    )

    assert result["passed"] is True
    assert result["findings"] == []


def test_bad_form_heritage_blocks_exact_authentic_headword() -> None:
    """Authentic exact hits still reject bad-form markers."""
    result = _bad_form_heritage_gate(
        module_text="Не маркуй <!-- bad -->кобіта<!-- /bad --> як помилку без підстав.",
        activities=[],
        vocabulary=[],
        resources=[],
        heritage_lookup_fn=lambda _query: [
            {
                "word": "кобіта",
                "is_authentic_ukrainian": True,
                "source_family": "grinchenko",
            }
        ],
    )

    assert result["passed"] is False
    assert result["findings"][0]["word"] == "кобіта"


def test_normal_prose_cyrillic_survives_comment_stripping() -> None:
    """Only comments and marked bad forms are stripped from VESUM text."""
    text = _build_vesum_text(
        "Вона одягається. <!-- VERIFY: word='одіватися' -->",
        [],
        [],
        [],
    )

    assert "одягається" in text
    assert "одіватися" not in text


def test_vesum_gate_ignores_verify_comment_russianism_end_to_end() -> None:
    """VERIFY comments with non-VESUM arguments must not fail the gate."""
    module_text = (
        "Вона одягається вранці. "
        "<!-- VERIFY: source='vesum'; check_russian_shadow(word='одіватися') -->"
    )
    sent_for_verification: set[str] = set()

    def verify_words(words: list[str]) -> dict[str, list[dict[str, str]]]:
        sent_for_verification.update(words)
        valid = {"вона", "вранці", "одягається"}
        return {word: ([{"lemma": word}] if word in valid else []) for word in words}

    result = _vesum_gate(
        module_text=module_text,
        activities=[],
        vocabulary=[],
        resources=[],
        verify_words_fn=verify_words,
    )

    assert result["passed"] is True
    assert "одіватися" not in sent_for_verification


def test_highlight_morpheme_fragments_not_verified() -> None:
    """Morpheme labels are fragments; the carrier word remains verified."""
    activity = {
        "type": "highlight-morphemes",
        "text": "писав",
        "items": [
            {
                "word": "писав",
                "morphemes": [
                    {"text": "писа", "type": "stem"},
                    {"morpheme": "-в", "type": "suffix"},
                ],
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
    assert "писав" in sent_for_verification
    assert "писа" not in sent_for_verification
