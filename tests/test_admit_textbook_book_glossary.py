"""Unit tests for the textbook-glossary admission gate (no network, no sources.db)."""

from __future__ import annotations

import json

from scripts.lexicon import admit_textbook_book_glossary as admit


def test_dmklinger_gloss_dedupes_and_caps_senses() -> None:
    index = {
        "мама": [
            ("noun", json.dumps(["mother", "mama", "mom", "mum", "extra sense"])),
        ]
    }
    gloss = admit.dmklinger_gloss(index, "мама")
    assert gloss == "mother; mama; mom"


def test_dmklinger_gloss_missing_returns_none() -> None:
    assert admit.dmklinger_gloss({}, "невідоме") is None


def test_uk_definition_prefers_sum20_over_vts() -> None:
    cache = {
        "lookup_word": "мама",
        "lookups": {
            "newsum": {"text": "мама МА́МА, и, ж. Ласкаве називання матері.", "word": "мама", "source_url": "u1"},
            "vts": {"text": "мама ма́ма -и, ж. Звертання до матері.", "word": "мама", "source_url": "u2"},
        },
    }
    text, source, url = admit.uk_definition(cache, "мама")
    assert source == "sum20"
    assert url == "u1"
    assert "МА́МА" in text or "Ласкаве" in text


def test_uk_definition_falls_back_to_vts() -> None:
    cache = {"lookup_word": "мама", "lookups": {"newsum": None, "vts": {"text": "мама ма́ма опис.", "word": "мама", "source_url": "u2"}}}
    _text, source, url = admit.uk_definition(cache, "мама")
    assert source == "vts"
    assert url == "u2"


def test_uk_definition_missing_returns_none() -> None:
    cache = {"lookup_word": "х", "lookups": {"newsum": None, "vts": None}}
    assert admit.uk_definition(cache, "х") is None


def test_en_gloss_prefers_dmklinger_then_ukreng() -> None:
    index = {"школа": [("noun", json.dumps(["school"]))]}
    cache = {"lookup_word": "школа", "lookups": {}}
    gloss, source = admit.en_gloss(cache, "школа", index)
    assert (gloss, source) == ("school", "dmklinger")

    cache2 = {"lookup_word": "тест", "lookups": {"ukreng": {"text": "тест test опис.", "word": "тест"}}}
    result = admit.en_gloss(cache2, "тест", {})
    assert result is not None
    assert result[1] == "ukreng"


def test_admit_candidates_requires_both_gates(monkeypatch) -> None:
    def fake_cache(lemma: str) -> dict:
        caches = {
            "мама": {"lookup_word": "мама", "lookups": {"newsum": {"text": "означення мами.", "word": "мама"}}},
            "хмара": {"lookup_word": "хмара", "lookups": {"newsum": None, "vts": None}},
        }
        return caches.get(lemma, {"lookup_word": lemma, "lookups": {}})

    monkeypatch.setattr(admit, "ensure_slovnyk_cache", fake_cache)
    dmklinger_index = {"мама": [("noun", json.dumps(["mother"]))]}
    candidates = [
        {"lemma": "мама", "pos": "noun", "count": 5, "locators": ["p.1"]},
        {"lemma": "хмара", "pos": "noun", "count": 2, "locators": ["p.2"]},
    ]
    admitted, residual = admit.admit_candidates(candidates, dmklinger_index=dmklinger_index)
    assert [item["lemma"] for item in admitted] == ["мама"]
    assert admitted[0]["gloss"] == "mother"
    assert residual == [{"lemma": "хмара", "pos": "noun", "count": 2, "reasons": ["no_uk_definition", "no_en_gloss"]}]
