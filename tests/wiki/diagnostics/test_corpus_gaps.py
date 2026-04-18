"""Tests for the corpus gap audit diagnostic."""

from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

import yaml

_project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.insert(0, os.path.join(_project_root, "scripts"))

from wiki.diagnostics.corpus_gaps import audit


def _make_db(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE textbooks (
            id INTEGER PRIMARY KEY,
            chunk_id TEXT NOT NULL,
            title TEXT NOT NULL,
            text TEXT NOT NULL,
            source_file TEXT NOT NULL,
            grade TEXT,
            author TEXT,
            char_count INTEGER
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE external_articles (
            id INTEGER PRIMARY KEY,
            chunk_id TEXT NOT NULL,
            url TEXT NOT NULL,
            url_normalized TEXT NOT NULL,
            title TEXT NOT NULL,
            text TEXT NOT NULL,
            source_file TEXT NOT NULL,
            domain TEXT,
            char_count INTEGER,
            channel_id TEXT,
            speaker TEXT,
            register_tag TEXT,
            decolonization_tag TEXT,
            quality_tier INTEGER,
            publish_date TEXT,
            duration_s INTEGER,
            chunk_start_ts INTEGER,
            chunk_end_ts INTEGER,
            video_id TEXT
        )
        """
    )
    return conn


def test_concept_extraction_count(tmp_path, monkeypatch):
    discovery_path = tmp_path / "sample.yaml"
    discovery_path.write_text(
        yaml.safe_dump(
            {
                "query_keywords": [
                    "Де це?",
                    "Use в/у and на + locative to answer Де? (Where?)",
                    "Distinguish в (inside) from на (on/at) with place vocabulary",
                    "школа → в школі",
                    "вулиця → на вулиці",
                ]
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        audit,
        "run_codex_concept_extraction",
        lambda prompt, model="gpt-5.4": {
            "concepts": [
                {"concept": f"концепт {index}", "variants": [f"концепт {index}", f"варіант {index}"]}
                for index in range(1, 9)
            ]
        },
    )

    payload = audit.derive_article_concepts(
        track="a1",
        slug="where-is-it",
        discovery_path=discovery_path,
        cache={"articles": {}},
    )
    assert 8 <= len(payload["concepts"]) <= 15
    assert payload["objectives"]
    assert "в/у and на + locative" in payload["llm_prompt"]


def test_existence_check_against_synthetic_corpus(tmp_path):
    db_path = tmp_path / "sources.db"
    conn = _make_db(db_path)
    conn.execute(
        """
        INSERT INTO textbooks (chunk_id, title, text, source_file, grade, author, char_count)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "tb-1",
            "Phonetics",
            "Українська буква ї завжди позначає два звуки і допомагає чути [йі].",
            "tb.jsonl",
            "2",
            "Автор",
            90,
        ),
    )
    conn.execute(
        """
        INSERT INTO external_articles (
            chunk_id, url, url_normalized, title, text, source_file, domain, char_count,
            channel_id, speaker, register_tag, decolonization_tag, quality_tier,
            publish_date, duration_s, chunk_start_ts, chunk_end_ts, video_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "ext-1",
            "https://example.com",
            "https://example.com",
            "History",
            "У правописі 1933 року літеру ґ було вилучено з абетки.",
            "ext.jsonl",
            "example.com",
            72,
            "",
            "",
            "",
            "",
            2,
            "",
            0,
            None,
            None,
            "",
        ),
    )
    conn.commit()

    present = audit.check_concept_coverage(
        conn,
        {
            "concept": "буква ї позначає два звуки",
            "variants": ["буква ї позначає два звуки", "[йі]"],
        },
    )
    missing = audit.check_concept_coverage(
        conn,
        {
            "concept": "неіснуюча прогалина",
            "variants": ["неіснуюча прогалина"],
        },
    )

    assert present["in_textbooks"] is True
    assert present["in_external"] is False
    assert present["textbooks_match_count"] == 1
    assert missing["absent_from_corpus"] is True


def test_gap_classification_groups_by_severity():
    coverage_map = {
        "metadata": {"generated_at": "2026-04-19T00:00:00+00:00", "tracks": ["a1", "b1", "c1"], "article_count": 3, "concept_count": 3, "absent_concept_count": 3},
        "articles": [
            {
                "track": "a1",
                "slug": "sounds",
                "severity_tier": "BLOCKER",
                "concepts": [{"concept": "літеру ґ було вилучено", "variants": ["літеру ґ було вилучено", "правопис 1933 року"], "absent_from_corpus": True}],
            },
            {
                "track": "b1",
                "slug": "morphology",
                "severity_tier": "MAJOR",
                "concepts": [{"concept": "чергування приголосних у словотворі", "variants": ["чергування приголосних", "словотвір"], "absent_from_corpus": True}],
            },
            {
                "track": "c1",
                "slug": "syntax",
                "severity_tier": "MINOR",
                "concepts": [{"concept": "порядок слів у складному реченні", "variants": ["порядок слів", "складне речення"], "absent_from_corpus": True}],
            },
        ],
    }

    categories = audit.classify_gap_categories(coverage_map)
    assert categories[0]["severity_tier"] == "BLOCKER"
    assert any(category["label"] == "Правопис і мовна політика" for category in categories)
    assert any(category["label"] == "Словотвір і морфонологія" for category in categories)
    assert any(category["label"] == "Синтаксис і порядок слів" for category in categories)


def test_roadmap_generation_orders_priority():
    categories = [
        {
            "slug": "phonetics-and-orthoepy",
            "label": "Фонетика й орфоепія",
            "source_tags": ["phonetics"],
            "affected_article_count": 2,
            "affected_articles": ["a1/sounds", "a1/reading"],
            "affected_concept_count": 4,
            "affected_concepts": [],
            "severity_tier": "BLOCKER",
        },
        {
            "slug": "word-formation-and-morphophonemics",
            "label": "Словотвір і морфонологія",
            "source_tags": ["word-formation", "morphology"],
            "affected_article_count": 1,
            "affected_articles": ["b1/morphology"],
            "affected_concept_count": 2,
            "affected_concepts": [],
            "severity_tier": "MAJOR",
        },
        {
            "slug": "miscellaneous-gaps",
            "label": "Інші прогалини",
            "source_tags": [],
            "affected_article_count": 1,
            "affected_articles": ["c1/misc"],
            "affected_concept_count": 1,
            "affected_concepts": [],
            "severity_tier": "MINOR",
        },
    ]

    rows = audit.build_roadmap(categories)
    assert rows[0]["priority"] == "BLOCKER"
    assert any(row["priority"] == "MAJOR" for row in rows)
    assert any(row["priority"] == "MINOR" for row in rows)
