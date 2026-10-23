"""Tests for SQLite-backed legacy RAG compatibility helpers."""

from __future__ import annotations

from scripts.rag import query


def test_search_text_maps_sqlite_rows(monkeypatch):
    def fake_search_textbooks(keywords, max_total, *, subject=None):
        assert "мова" in keywords
        assert max_total == 6
        assert subject == "ukrmova"
        return [
            {
                "_kw_score": 4,
                "chunk_id": "chunk-1",
                "text": "Українська мова",
                "title": "Title",
                "grade": 3,
                "author_uk": "Автор",
                "source_file": "3-klas-mova.pdf",
                "subject": "ukrmova",
            },
            {
                "_kw_score": 1,
                "chunk_id": "chunk-2",
                "text": "Other",
                "title": "Other",
                "grade": 7,
            },
        ]

    monkeypatch.setattr(query.sources_db, "search_textbooks", fake_search_textbooks)

    hits = query.search_text("мова", grade=3, subject="ukrmova", limit=2)

    assert hits == [
        {
            "score": 4.0,
            "chunk_id": "chunk-1",
            "text": "Українська мова",
            "section_title": "Title",
            "grade": 3,
            "author": "Автор",
            "page": "",
            "trust_tier": 0,
            "source_type": "textbook",
            "source_file": "3-klas-mova.pdf",
            "subject": "ukrmova",
        }
    ]


def test_search_literary_maps_and_filters(monkeypatch):
    def fake_search_literary(keywords, max_total):
        assert "дума" in keywords
        assert max_total == 6
        return [
            {
                "_kw_score": 2,
                "chunk_id": "lit-1",
                "text": "Дума",
                "title": "Думи",
                "author": "Народ",
                "work": "Українські думи",
                "genre": "folk",
                "language_period": "modern",
            },
            {
                "chunk_id": "lit-2",
                "text": "Other",
                "work": "Other",
                "genre": "poetry",
            },
        ]

    monkeypatch.setattr(query.sources_db, "search_literary", fake_search_literary)

    hits = query.search_literary("дума", work="думи", genre="folk", limit=2)

    assert len(hits) == 1
    assert hits[0]["chunk_id"] == "lit-1"
    assert hits[0]["work"] == "Українські думи"
    assert hits[0]["score"] == 2.0


def test_search_dictionary_uses_sqlite_dictionary_helpers(monkeypatch):
    monkeypatch.setattr(
        query.sources_db,
        "search_definitions",
        lambda word, limit: [{"word": word, "definition": "пояснення", "source": "sum11"}],
    )

    hits = query.search_dictionary("мова", "sum11", limit=1)

    assert hits == [
        {
            "score": 0.0,
            "text": "Historical Soviet colonization context only; cannot verify modern Ukrainian.",
            "word": "мова",
            "collection": "sum11",
            "soviet_colonization_context": {
                "source": "СУМ-11 (1970–1980)",
                "source_role": "soviet_colonization_context",
                "red_flag": True,
                "historical_only": True,
                "contrast_only": True,
                "can_verify_modern_ukrainian": False,
                "sovietization_risk": None,
                "sovietization_keywords": None,
                "ideological_markers": None,
                "entry": {"word": "мова", "definition": "пояснення", "source": "sum11"},
            },
        }
    ]
