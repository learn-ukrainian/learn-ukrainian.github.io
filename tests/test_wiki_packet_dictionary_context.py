from __future__ import annotations

from scripts.build import linear_pipeline


def _fixture_plan() -> dict:
    return {
        "module": "a1-999",
        "level": "A1",
        "sequence": 999,
        "slug": "dictionary-context",
        "title": "Dictionary Context",
        "subtitle": "Fixture plan",
        "content_outline": [
            {
                "section": "Vocabulary",
                "words": 120,
                "points": ["Use the required vocabulary in short examples."],
            }
        ],
        "word_target": 120,
        "references": [{"title": "Fixture source"}],
        "vocabulary_hints": {
            "required": [
                "мама (mom)",
                "тато (dad)",
                "йти (to go)",
                "кава (coffee)",
                {"word": "школа"},
            ],
        },
    }


def test_build_knowledge_packet_appends_dictionary_context(monkeypatch) -> None:
    from scripts.verification import vesum
    from wiki import sources_db

    long_definition = " ".join(f"довге{i}" for i in range(80))
    long_definition += " TAIL_SHOULD_NOT_APPEAR"

    def fake_verify_words(words: list[str]) -> dict[str, list[dict]]:
        return {
            word: [
                {
                    "lemma": word,
                    "pos": "verb" if word == "йти" else "noun",
                    "tags": "verb:imperf:inf" if word == "йти" else "noun:anim",
                }
            ]
            for word in words
        }

    def fake_verify_lemma(lemma: str) -> list[dict]:
        return [
            {
                "word_form": lemma,
                "pos": "verb" if lemma == "йти" else "noun",
                "tags": "verb:imperf:inf" if lemma == "йти" else "noun:anim",
            }
        ]

    def fake_search_definitions(lemma: str, limit: int = 1) -> list[dict]:
        assert limit == 1
        definition = long_definition if lemma == "кава" else f"{lemma}: short SUM-11 definition"
        return [{"word": lemma, "definition": definition, "source": "СУМ-11"}]

    def fake_search_style_guide(lemma: str, limit: int = 1) -> list[dict]:
        assert limit == 1
        if lemma == "йти":
            return [{"word": lemma, "text": "Style guidance for йти."}]
        return []

    monkeypatch.setattr(
        linear_pipeline,
        "_build_wiki_packet",
        lambda level, slug: (
            "### Вікі: pedagogy/a1/dictionary-context.md\n\n"
            "## Overview\n"
            "мама тато йти кава школа"
        ),
    )
    monkeypatch.setattr(vesum, "verify_words", fake_verify_words)
    monkeypatch.setattr(vesum, "verify_lemma", fake_verify_lemma)
    monkeypatch.setattr(sources_db, "search_definitions", fake_search_definitions)
    monkeypatch.setattr(sources_db, "search_style_guide", fake_search_style_guide)

    packet = linear_pipeline.build_knowledge_packet(
        level="a1",
        slug="dictionary-context",
        plan=_fixture_plan(),
    )

    assert "## Dictionary context" in packet
    for lemma in ("мама", "тато", "йти", "кава", "школа"):
        assert f"**{lemma}**" in packet
    assert "- **йти** [verb]" in packet
    assert "Style note: Style guidance for йти." in packet
    assert "TAIL_SHOULD_NOT_APPEAR" not in packet
    assert "Definition: довге0 довге1" in packet
    assert "..." in packet
