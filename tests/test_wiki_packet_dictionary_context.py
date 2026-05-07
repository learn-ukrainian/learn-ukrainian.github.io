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


def test_build_knowledge_packet_appends_textbook_excerpts(monkeypatch) -> None:
    from wiki import sources_db

    queries: list[str] = []

    plan = _fixture_plan()
    plan["title"] = "My Morning"
    plan["references"] = [
        {"title": "Караман Grade 10, p.176"},
        {"title": "Захарійчук Grade 4, p.162"},
    ]

    def fake_search_sources(query: str, *, track: str, limit: int = 10, **_kwargs):
        queries.append(query)
        assert track == "a1"
        if "Караман" in query:
            return [
                {
                    "source_type": "textbook",
                    "title": "Українська мова",
                    "author": "Караман",
                    "grade": 10,
                    "page": 176,
                    "source_file": "10-klas-ukrmova-karaman",
                    "text": "Зворотна форма дієслова походить від короткої форми займенника себе.",
                }
            ]
        return [
            {
                "source_type": "textbook",
                "title": "Українська мова",
                "author": "Захарійчук",
                "grade": 4,
                "page": 162,
                "source_file": "4-klas-ukrmova-zakhariichuk",
                "text": "Умиваюся, одягаюся, вітаюся — ці дієслова називають дію, спрямовану на себе.",
            }
        ]

    monkeypatch.setattr(
        linear_pipeline,
        "_build_wiki_packet",
        lambda level, slug: "### Вікі: pedagogy/a1/dictionary-context.md\n\n## Overview\nранок",
    )
    monkeypatch.setattr(sources_db, "search_sources", fake_search_sources)

    packet = linear_pipeline.build_knowledge_packet(
        level="a1",
        slug="dictionary-context",
        plan=plan,
    )

    assert "## Textbook Excerpts (verbatim, must be cited)" in packet
    assert "### Караман Grade 10, p.176" in packet
    assert "Source: Українська мова (Караман, Grade 10, p.176, 10-klas-ukrmova-karaman)" in packet
    assert "> Зворотна форма дієслова походить" in packet
    assert "### Захарійчук Grade 4, p.162" in packet
    assert "> Умиваюся, одягаюся, вітаюся" in packet
    assert len(queries) == 2
    assert all("My Morning" in query for query in queries)
