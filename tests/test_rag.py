"""Tests for SQLite-backed legacy RAG compatibility helpers."""

from __future__ import annotations

from scripts.rag import query


def test_build_filter_returns_plain_descriptor():
    assert query.build_filter(grade=3, subject="mova", trust_tier=1) == {
        "grade": 3,
        "subject": "mova",
        "trust_tier": 1,
    }


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


def test_search_text_preserves_legacy_subject_substring_filter(monkeypatch):
    def fake_search_textbooks(keywords, max_total, *, subject=None):
        assert "мова" in keywords
        assert max_total == 6
        assert subject is None
        return [
            {
                "_kw_score": 3,
                "chunk_id": "chunk-1",
                "text": "Українська мова",
                "title": "Title",
                "section_title": "Апостроф",
                "source_file": "3-klas-mova.pdf",
            },
            {
                "_kw_score": 2,
                "chunk_id": "chunk-2",
                "text": "Other",
                "title": "Other",
                "section_title": "Інший розділ",
                "source_file": "5-klas-ukrlit.pdf",
            },
        ]

    monkeypatch.setattr(query.sources_db, "search_textbooks", fake_search_textbooks)

    hits = query.search_text("мова", subject="апостроф", limit=2)

    assert [hit["chunk_id"] for hit in hits] == ["chunk-1"]


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
            "text": "SUM-11: historical Soviet occupation context only; modern meaning withheld.",
            "word": "мова",
            "collection": "sum11",
            "source": "sum11",
            "metadata": {
                "soviet_colonization_context": {
                    "word": "мова",
                    "source": "sum11",
                    "sovietization_risk": None,
                    "sovietization_keywords": None,
                    "ideological_markers": None,
                }
            },
        }
    ]


def test_search_images_is_retired_empty_result():
    assert query.search_images("яблуко", limit=3) == []


def test_collection_stats_reports_sources_db(monkeypatch):
    monkeypatch.setattr(query.sources_db, "source_count", lambda: 42)
    monkeypatch.setattr(query.sources_db, "list_tables", lambda: ["textbooks"])

    assert query.collection_stats() == {
        "sources_db": {
            "points_count": 42,
            "tables": ["textbooks"],
            "status": "ok",
        }
    }


# These are invented sentinels, not linguistic evidence.
def test_sum11_aliases_context_and_cli(monkeypatch, capsys):
    import json
    import sys

    for alias in ("sum11", "SuM", "DEFINITIONS"):
        for raw_field in ("text", "definition"):
            for risk in (0, 3, None):
                row = {
                    "word": "sentinel_head",
                    raw_field: "RAW_SENTINEL",
                    "source": "sum11",
                    "sovietization_risk": risk,
                    "sovietization_keywords": "KEYWORD_SENTINEL",
                    "ideological_markers": ["MARKER_SENTINEL"],
                }
                monkeypatch.setattr(query.sources_db, "search_definitions", lambda *a, row=row, **k: [row])
                hits = query.search_dictionary("sentinel_head", alias)
                assert hits[0]["text"] == (
                    "SUM-11: historical Soviet occupation context only; modern meaning withheld."
                )
                context = hits[0]["metadata"]["soviet_colonization_context"]
                assert context["sovietization_risk"] == risk
                assert context["sovietization_keywords"] == "KEYWORD_SENTINEL"
                assert context["ideological_markers"] == ["MARKER_SENTINEL"]
                if risk is None:
                    assert "RAW_SENTINEL" not in json.dumps(hits)
                else:
                    assert context[raw_field] == "RAW_SENTINEL"
                monkeypatch.setattr(sys, "argv", ["query", "dict", alias, "sentinel_head"])
                query.main()
                assert json.loads(capsys.readouterr().out) == hits


def test_sum11_missing_editorial_metadata_withholds_raw(monkeypatch):
    import json

    for missing in ("sovietization_risk", "sovietization_keywords", "ideological_markers"):
        row = {
            "word": "sentinel_head",
            "text": "RAW_SENTINEL",
            "definition": "GLOSS_SENTINEL",
            "sovietization_risk": 0,
            "sovietization_keywords": [],
            "ideological_markers": [],
        }
        del row[missing]
        monkeypatch.setattr(query.sources_db, "search_definitions", lambda *a, row=row, **k: [row])
        hit = query.search_dictionary("sentinel_head", "sum11")[0]
        assert hit["metadata"]["soviet_colonization_context"][missing] is None
        assert "RAW_SENTINEL" not in json.dumps(hit)
        assert "GLOSS_SENTINEL" not in json.dumps(hit)
        assert row["text"] == "RAW_SENTINEL"


def test_other_dictionary_routes_preserve_text(monkeypatch):
    for alias, helper in (
        ("grinchenko", "search_grinchenko_1907"),
        ("style", "search_style_guide"),
        ("cefr", "query_cefr_level"),
        ("idioms", "search_idioms"),
        ("synonyms", "search_synonyms"),
        ("esum", "search_esum"),
        ("other", "search_sources"),
    ):
        row = {"word": "sentinel_head", "text": "OTHER_ROUTE"}
        monkeypatch.setattr(query.sources_db, helper, lambda *a, row=row, **k: [row])
        hit = query.search_dictionary("sentinel_head", alias)[0]
        assert hit["text"] == "OTHER_ROUTE"
        assert hit["metadata"] == row
