"""Unit tests for the quote-host byte checks (issue #9487 gate C12).

The Cyrillic strings are fixture data for the byte rules, not claims about Ukrainian; the VESUM
lookup is a stub.
"""

from __future__ import annotations

import pytest

from scripts.curriculum.validate import quote_bytes


def _kinds(text: str) -> list[str]:
    return [defect.kind for defect in quote_bytes.byte_defects(text)]


def test_private_use_code_points_in_any_plane_are_defects() -> None:
    assert _kinds("слово ") == [quote_bytes.PRIVATE_USE]
    assert _kinds("слово \U000f0000") == [quote_bytes.PRIVATE_USE]
    assert _kinds("слово") == []


def test_only_brackets_holding_a_cyrillic_letter_are_transcriptions() -> None:
    assert _kinds("гілка [г’¾лка]") == [quote_bytes.TRANSCRIPTION_SYMBOL]
    assert _kinds("[ = • – ] [ =•|–• ]") == []  # primer schemes
    assert _kinds("[йа́ма] [дз′] [з′:а] [ма|ма]") == []


def test_web_addresses_are_watermarks() -> None:
    defects = quote_bytes.byte_defects("Марі\nPidruchnyk.com.ua\nя")
    assert [(d.kind, d.detail) for d in defects] == [(quote_bytes.WATERMARK, "'Pidruchnyk.com.ua'")]
    assert _kinds("див. www.example.org") == [quote_bytes.WATERMARK]
    assert _kinds("Ма-ма. Тато.") == []


def test_word_tokens_skip_letters_syllables_and_brackets_and_join_divided_words() -> None:
    tokens = quote_bytes.word_tokens("А а ма мо [мама] Ма-ма предме-\nтів ри́ба")
    assert [(token.surface, token.spellings) for token in tokens] == [
        ("Ма-ма", ("Мама", "Ма-ма")),
        ("предметів", ("предметів",)),
        ("риба", ("риба",)),
    ]


def test_word_tokens_skip_every_alphabet_table_cell() -> None:
    alphabet = "АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ"
    assert len(alphabet) == 33
    table = " ".join(letter + letter.lower() for letter in alphabet)
    assert quote_bytes.word_tokens(f"{table} Дждж Дздз") == []
    assert quote_bytes.word_tokens("Єє, Ии, Іі, Оо, Яя") == []


def test_word_tokens_look_up_letter_runs_that_are_not_a_capital_and_its_own_small_letter() -> None:
    tokens = quote_bytes.word_tokens("ЄИ єє ЯЯ Оа Єєє Єє-Яя ЄєЯя Аб")
    assert [token.surface for token in tokens] == ["ЄИ", "єє", "ЯЯ", "Оа", "Єєє", "Єє-Яя", "ЄєЯя"]
    # «Аб» is no alphabet cell either; it holds one vowel letter, so the syllable rule already skips it.


def test_unknown_words_consult_the_store_before_the_lookup() -> None:
    seen: list[list[str]] = []

    def lookup(words: list[str]) -> set[str]:
        seen.append(words)
        return {"риба"}

    tokens = quote_bytes.word_tokens("Мама риба кукуру м’яч")
    known = quote_bytes.known_spellings(["мама", "м'яч"])
    assert quote_bytes.unknown_words(tokens, known, lookup) == ["кукуру"]
    assert seen == [["кукуру", "риба"]]


def test_unknown_words_propagate_an_unavailable_vesum() -> None:
    def lookup(words: list[str]) -> set[str]:
        raise quote_bytes.VesumUnavailable("gone")

    with pytest.raises(quote_bytes.VesumUnavailable):
        quote_bytes.unknown_words(quote_bytes.word_tokens("кукуру"), set(), lookup)


def test_vesum_lookup_reports_a_missing_database_as_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    import scripts.verification.vesum as vesum

    def missing(words: list[str]) -> dict:
        raise FileNotFoundError("VESUM database not found")

    monkeypatch.setattr(vesum, "verify_words", missing)
    with pytest.raises(quote_bytes.VesumUnavailable):
        quote_bytes.vesum_lookup(["слово"])


def test_vesum_lookup_returns_the_words_with_matches(monkeypatch: pytest.MonkeyPatch) -> None:
    import scripts.verification.vesum as vesum

    monkeypatch.setattr(vesum, "verify_words", lambda words: {"слово": [{"lemma": "слово"}], "кукуру": []})
    assert quote_bytes.vesum_lookup(["слово", "кукуру"]) == {"слово"}
