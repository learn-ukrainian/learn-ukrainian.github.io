from __future__ import annotations

import sqlite3
from pathlib import Path

from scripts.wiki.diagnostics import retrieval_probe_9233 as probe


def _make_vesum(path: Path) -> None:
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE forms_all (
            id INTEGER PRIMARY KEY, entry_id INTEGER NOT NULL, word_form TEXT NOT NULL,
            lemma TEXT NOT NULL, pos TEXT NOT NULL, tags TEXT NOT NULL,
            source_comment TEXT, source_location TEXT NOT NULL
        );
        CREATE TABLE form_markers (form_id INTEGER, marker TEXT, origin TEXT, marker_class TEXT);
        INSERT INTO forms_all VALUES
            (1, 1, 'родовий', 'родовий', 'adj', '', '', ''),
            (2, 1, 'родового', 'родовий', 'adj', '', '', ''),
            (3, 1, 'родовому', 'родовий', 'adj', '', '', ''),
            (4, 2, 'відмінок', 'відмінок', 'noun', '', '', ''),
            (5, 2, 'відмінка', 'відмінок', 'noun', '', '', ''),
            (6, 2, 'відмінку', 'відмінок', 'noun', '', '', '');
        """
    )
    connection.commit()
    connection.close()


def _make_sources(path: Path) -> None:
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE textbooks (
            id INTEGER PRIMARY KEY, chunk_id TEXT NOT NULL, title TEXT NOT NULL,
            text TEXT NOT NULL, source_file TEXT NOT NULL, subject TEXT,
            parent_section_id INTEGER
        );
        CREATE VIRTUAL TABLE textbooks_fts USING fts5(title, text, content='textbooks', content_rowid='id', tokenize='unicode61');
        CREATE TRIGGER textbooks_ai AFTER INSERT ON textbooks BEGIN
            INSERT INTO textbooks_fts(rowid, title, text) VALUES (new.id, new.title, new.text);
        END;
        INSERT INTO textbooks(id, chunk_id, title, text, source_file, subject, parent_section_id)
        VALUES (1, 'gold-chunk', 'grammar', 'родовий відмінок у вправі', 'ukrmova-fixture', 'ukrmova', 7),
               (2, 'neighbor-chunk', 'unrelated', 'інший текст', 'ukrmova-fixture', 'ukrmova', 7);
        """
    )
    connection.commit()
    connection.close()


def test_form_mismatch_query_uses_distinct_vesum_forms(tmp_path: Path) -> None:
    db = tmp_path / "vesum.db"
    _make_vesum(db)
    connection = sqlite3.connect(db)
    query = probe._make_form_mismatch_query("родовий відмінок", connection)
    connection.close()

    assert query is not None
    assert query["query"] == "родового відмінка"
    assert query["query"] != "родовий відмінок"
    assert [item["lemma"] for item in query["forms"]] == ["родовий", "відмінок"]


def test_lemma_arm_recovers_inflected_form_missed_by_exact_arm(tmp_path: Path) -> None:
    sources = tmp_path / "sources.db"
    vesum = tmp_path / "vesum.db"
    _make_sources(sources)
    _make_vesum(vesum)
    source_connection = probe._ro_connect(sources)
    exact = probe._exact_chunk_search(source_connection, "відмінка", 20)

    index_path, _ = probe._create_lemma_index(sources, vesum, tmp_path / "temp")
    with probe.get_vesum_connection(vesum) as vesum_connection:
        lemma = probe._lemma_search(index_path, "відмінка", vesum_connection, 20)
    source_connection.close()

    assert "gold-chunk" not in exact
    assert "gold-chunk" in lemma


def test_production_section_results_expand_to_member_chunk_ids(tmp_path: Path, monkeypatch) -> None:
    sources = tmp_path / "sources.db"
    _make_sources(sources)
    connection = probe._ro_connect(sources)

    def fake_search_sources(query: str, *, track: str, limit: int) -> list[dict[str, object]]:
        assert query == "query" and track == "a1" and limit == 10
        return [{"corpus": "textbook_sections", "chunk_id": "S7"}]

    monkeypatch.setattr(probe.sources_db, "search_sources", fake_search_sources)
    result = probe._production_search("query", "a1", connection)
    connection.close()

    assert result == {"gold-chunk": 1, "neighbor-chunk": 1}


def test_query_set_uses_pack_ids_arc_subset_and_source_grammar_terms(tmp_path: Path) -> None:
    sources = tmp_path / "sources.db"
    vesum = tmp_path / "vesum.db"
    _make_sources(sources)
    _make_vesum(vesum)
    pack = tmp_path / "pack.yaml"
    pack.write_text(
        """texts:\n  - id: T-1\n    source: {table: textbooks, chunk_id: gold-chunk}\n    span: {first_words: 'родовий відмінок', last_words: 'відмінок'}\n    supports: 'Find the grammatical case in a short textbook passage.'\nexercises: []\n""",
        encoding="utf-8",
    )
    arc_a1 = tmp_path / "a1.yaml"
    arc_a1.write_text(
        """positions:\n  - {position: 1, slug: case-intro, job: 'Use the genitive case'}\n  - {position: 2, slug: checkpoint, job: 'Self-check all cases'}\n""",
        encoding="utf-8",
    )
    arc_a2 = tmp_path / "a2.yaml"
    arc_a2.write_text("positions: []\n", encoding="utf-8")
    grammar = tmp_path / "grammar.md"
    grammar.write_text("відмінок", encoding="utf-8")

    queries = probe.build_query_set(
        sources_path=sources,
        vesum_path=vesum,
        pack_path=pack,
        arc_paths={"a1": arc_a1, "a2": arc_a2},
        grammar_source=grammar,
    )

    assert len(queries["g1"]) == 2
    assert queries["g1"][0]["gold_chunk_id"] == "gold-chunk"
    assert queries["g1"][0]["query"] != "родовий відмінок"
    assert [item["position"] for item in queries["g2"]] == [1]
    assert queries["g2"][0]["forms"] == ["відмінок", "відмінка", "відмінку"]


def test_text_helpers_fold_stress_and_require_exact_pack_boundaries() -> None:
    assert probe.tokenize("гото́льʼю") == ["готоль'ю"]
    assert probe._get_cited_span(
        "До́брий день! Після цього є вправа.",
        {"first_words": "Добрий день!", "last_words": "вправа."},
    ) == "До́брий день! Після цього є вправа"


def test_rank_metrics_and_percentile_use_query_denominator() -> None:
    queries = [
        {"id": "q1", "gold_chunk_id": "gold", "stratum": "ukrainian_form_mismatch"},
        {"id": "q2", "gold_chunk_id": "missing", "stratum": "english"},
    ]
    metrics = probe._rank_metrics(queries, {"q1": ["other", "gold"], "q2": []}, "A0-chunk")

    assert metrics["all"] == {"n": 2, "hit_at_20": 0.5, "hit_at_100": 0.5, "mrr": 0.25}
    assert probe._percentile([1.0, 2.0, 3.0, 4.0], 0.95) == 4.0
