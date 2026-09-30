from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

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


def _ambiguous_fixture(tmp_path: Path) -> tuple[Path, Path]:
    sources, vesum = tmp_path / "sources.db", tmp_path / "vesum.db"
    _make_sources(sources)
    _make_vesum(vesum)
    with sqlite3.connect(vesum) as conn:
        conn.execute("INSERT INTO forms_all VALUES (7, 3, 'відмінок', 'аналіз', 'noun', '', '', '')")
    with sqlite3.connect(sources) as conn:
        conn.execute("UPDATE textbooks SET text='відмінок ксенотокен' WHERE id=1")
    return sources, vesum


def test_indexes_every_analysis_of_ambiguous_token(tmp_path: Path) -> None:
    sources, vesum = _ambiguous_fixture(tmp_path)
    index, _ = probe._create_lemma_index(sources, vesum, tmp_path / "temp")
    with sqlite3.connect(index) as conn:
        words = conn.execute("SELECT text_terms FROM lemma_fts WHERE rowid=1").fetchone()[0].split()
    assert {"аналіз", "відмінок"} <= set(words)


def test_retains_unknown_tokens_in_index_and_query(tmp_path: Path) -> None:
    sources, vesum = _ambiguous_fixture(tmp_path)
    index, _ = probe._create_lemma_index(sources, vesum, tmp_path / "temp")
    with probe.get_vesum_connection(vesum) as conn:
        assert probe._lemma_query("ксенотокен", conn) == ["ксенотокен"]
        assert probe._lemma_search(index, "ксенотокен", conn, 20) == ["gold-chunk"]


def test_query_expands_all_analyses(tmp_path: Path) -> None:
    _, vesum = _ambiguous_fixture(tmp_path)
    with probe.get_vesum_connection(vesum) as conn:
        assert set(probe._lemma_query("відмінок", conn)) == {"аналіз", "відмінок"}


def test_one_word_span_is_english_only(tmp_path: Path) -> None:
    sources, vesum = tmp_path / "sources.db", tmp_path / "vesum.db"
    _make_sources(sources)
    _make_vesum(vesum)
    pack, arc, grammar = tmp_path / "pack.yaml", tmp_path / "arc.yaml", tmp_path / "grammar.md"
    pack.write_text("texts:\n- id: T-1\n  source: {table: textbooks, chunk_id: gold-chunk}\n  span: {first_words: відмінок, last_words: відмінок}\n  supports: Find grammatical case\n")
    arc.write_text("positions: []\n")
    grammar.write_text("відмінок")
    result = probe.build_query_set(sources_path=sources, vesum_path=vesum, pack_path=pack, arc_paths={"a1": arc}, grammar_source=grammar)
    assert [q["stratum"] for q in result["g1"]] == ["english"]
    assert result["counts"]["g1_cited_chunks"] == 1


def test_g1_rejects_homographs_proper_names_pronouns_and_fragments(tmp_path: Path) -> None:
    _, vesum = _ambiguous_fixture(tmp_path)
    with sqlite3.connect(vesum) as conn:
        conn.executemany("INSERT INTO forms_all VALUES (?, 8, ?, ?, ?, ?, '', '')", [
            (8, 'Київ', 'Київ', 'noun', 'noun:prop:geo'),
            (9, 'київ', 'кий', 'noun', 'noun:p:v_rod'),
            (10, 'ти', 'ти', 'noun', 'noun:pron:pers'),
            (11, 'воя', 'вій', 'noun', 'noun:arch'),
        ])
        assert not probe._is_content_word("відмінок", conn)
        assert not probe._is_content_word("Київ", conn)
        assert not probe._is_content_word("ти", conn)
        assert not probe._is_content_word("воя", conn)
        assert probe._make_form_mismatch_query("родовий- родового-", conn) is None
        assert probe._make_form_mismatch_query("родовий – родового –", conn) is None


def test_g1_prefers_unused_combinations(tmp_path: Path) -> None:
    vesum = tmp_path / "vesum.db"
    _make_vesum(vesum)
    with sqlite3.connect(vesum) as conn:
        conn.executemany("INSERT INTO forms_all VALUES (?, 8, ?, 'слово', 'noun', '', '', '')", [(7, 'слово'), (8, 'слова')])
        first = probe._make_form_mismatch_query("родовий відмінок слово", conn)
        second = probe._make_form_mismatch_query("родовий відмінок слово", conn, used_queries={first["query"]})
    assert first["query"] == "родового відмінка слова"
    assert second["query"] == "родового відмінка"
    with sqlite3.connect(vesum) as conn:
        assert probe._make_form_mismatch_query("родовий — відмінок", conn)["query"] == "родового відмінка"


def test_descriptive_gate_reports_both_readings_without_g2_input(tmp_path: Path) -> None:
    queries = [{"id": "q1", "gold_chunk_id": "gold", "query": "query", "stratum": "ukrainian_form_mismatch"}]
    rankings = {"A0-chunk": {"q1": []}, "A1-lemma": {"q1": ["other"] * 20 + ["gold"]}}
    metrics = {arm: probe._rank_metrics(queries, ranks, arm) for arm, ranks in rankings.items()}
    g2 = [{"pairs": [{"arms": {"A1-lemma": {"any_shared_chunk": True}, "A0-chunk": {"any_shared_chunk": False}}}]}]
    # A hit@20 tie picks A0-chunk, so make A1 the better arm explicitly.
    metrics["A1-lemma"]["ukrainian_form_mismatch"]["hit_at_20"] = .5
    result = probe._descriptive_gate(queries, metrics, rankings, g2)
    assert result["status"] == "descriptive_only" and "opens" not in result
    assert result["readings"][0]["any_miss_at_20"] is True
    assert result["readings"][0]["v2_threshold_met"] is False
    assert result["g2_overlap_recoveries"] == 1
    assert result["readings"] == probe._descriptive_gate(queries, metrics, rankings, [])["readings"]


def test_bootstrap_clusters_repeated_query_strings() -> None:
    queries = [{"id": f"q{i}", "gold_chunk_id": "gold", "stratum": "ukrainian_form_mismatch", "query": "same"} for i in range(3)]
    ranks = {"A0-chunk": {q["id"]: [] for q in queries}, "A1-lemma": {q["id"]: ["gold"] for q in queries}}
    result = probe._g1_bootstrap(queries, ranks, iterations=100)
    assert result["clusters"] == 1 and result["ci95"] == [1, 1]
    assert result == probe._g1_bootstrap(queries, ranks, iterations=100)
    assert probe._g1_bootstrap([], ranks)["gain"] is None


def test_production_maps_direct_chunks_and_actual_result_ranks(tmp_path: Path, monkeypatch) -> None:
    sources = tmp_path / "sources.db"
    _make_sources(sources)
    monkeypatch.setattr(probe.sources_db, "search_sources", lambda *a, **kw: [
        {"corpus": "external", "chunk_id": "other"},
        {"corpus": "textbook_sections", "chunk_id": "ulp-direct"},
        {"corpus": "textbook_sections", "chunk_id": "S7"},
    ])
    with probe._ro_connect(sources) as conn:
        assert probe._production_search("query", "a1", conn) == {"ulp-direct": 2, "gold-chunk": 3, "neighbor-chunk": 3}
        monkeypatch.setattr(probe.sources_db, "search_sources", lambda *a, **kw: [])
        assert probe._production_search("query", "a1", conn) == {}


def test_regeneration_refuses_frozen_overwrite_without_flag(tmp_path: Path, monkeypatch) -> None:
    frozen = tmp_path / "queries.yaml"
    frozen_bytes = probe.yaml.safe_dump({"design_sha256": probe.EXPECTED_DESIGN_SHA256, "g1": []})
    frozen.write_text(frozen_bytes)
    replacement = {"g1": [], "g2": [], "counts": {"g1_ukrainian_form_mismatch": 0, "g1_english": 0}}
    monkeypatch.setattr(probe, "build_query_set", lambda **kw: replacement)
    arguments = ["--output-dir", str(tmp_path), "--temp-dir", str(tmp_path / "temp"), "--regenerate-queries", "--queries-only"]
    args = probe.build_parser().parse_args(arguments)
    with pytest.raises(ValueError, match="overwrite-frozen-queries"):
        probe.run_probe(args)
    assert frozen.read_text() == frozen_bytes
    approved = probe.build_parser().parse_args([*arguments, "--overwrite-frozen-queries"])
    assert probe.run_probe(approved)["frozen_only"] is True
    assert probe.yaml.safe_load(frozen.read_text())["g1"] == []


def test_production_snapshot_is_exact_git_source(monkeypatch) -> None:
    def output(argv, **kwargs):
        if argv[1] == "rev-parse":
            return "a" * 40 + "\n"
        return b"snapshot_value = 9233\n"
    monkeypatch.setattr(probe.subprocess, "check_output", output)
    module, provenance = probe._production_snapshot("revision")
    assert module.snapshot_value == 9233
    assert provenance["revision"] == "a" * 40
    assert len(provenance["source_sha256"]) == 64


def test_number_and_verb_terms_come_from_registered_textbook(tmp_path: Path) -> None:
    sources, vesum = tmp_path / "sources.db", tmp_path / "vesum.db"
    _make_sources(sources)
    _make_vesum(vesum)
    with sqlite3.connect(sources) as conn:
        conn.execute("INSERT INTO textbooks VALUES (3, ?, 'grammar', 'число дієслово', 'ukrmova-fixture', 'ukrmova', 8)", (probe.GRAMMAR_TEXTBOOK_CHUNK,))
    with sqlite3.connect(vesum) as conn:
        conn.executemany("INSERT INTO forms_all VALUES (?, 8, ?, ?, 'noun', '', '', '')", [(7, 'число', 'число'), (8, 'числа', 'число'), (9, 'числу', 'число'), (10, 'дієслово', 'дієслово'), (11, 'дієслова', 'дієслово'), (12, 'дієслову', 'дієслово')])
    pack, arc, grammar = tmp_path / "pack.yaml", tmp_path / "arc.yaml", tmp_path / "grammar.md"
    pack.write_text("texts: []\n")
    arc.write_text("positions:\n- {position: 1, slug: plural, job: 'Plural nouns'}\n- {position: 2, slug: verbs, job: 'Conjugate verbs'}\n")
    grammar.write_text("відмінок")
    result = probe.build_query_set(sources_path=sources, vesum_path=vesum, pack_path=pack, arc_paths={"a1": arc}, grammar_source=grammar)
    assert [q["category"] for q in result["g2"]] == ["number", "verb"]
    assert [q["base_query"] for q in result["g2"]] == ["число", "дієслово"]
    assert all(q["source_path"] == f"textbooks:{probe.GRAMMAR_TEXTBOOK_CHUNK}" for q in result["g2"])


def test_run_cleans_index_and_writes_descriptive_deduplicated_report(tmp_path: Path, monkeypatch) -> None:
    sources, vesum = tmp_path / "sources.db", tmp_path / "vesum.db"
    _make_sources(sources)
    _make_vesum(vesum)
    query = {"id": "q1", "gold_chunk_id": "gold-chunk", "query": "родового відмінка", "forms": [], "stratum": "ukrainian_form_mismatch", "source_file": "ukrmova-fixture", "subject": "ukrmova"}
    g2 = {"id": "G2-A1-001", "level": "a1", "position": 1, "category": "case", "base_query": "відмінок", "inflected_queries": ["відмінка", "відмінку"]}
    data = {"design_sha256": probe.EXPECTED_DESIGN_SHA256, "g1_rule": "fixture rule", "g1": [query], "g2": [g2, {**g2, "id": "G2-A1-002", "position": 2}], "counts": {"g1_cited_chunks": 1, "g1_ukrainian_form_mismatch": 1, "g1_english": 0}}
    frozen = tmp_path / "queries.yaml"
    frozen.write_text(probe.yaml.safe_dump(data))
    monkeypatch.setattr(probe.sources_db, "search_sources", lambda *a, **kw: [])
    args = probe.build_parser().parse_args(["--sources-db", str(sources), "--vesum-db", str(vesum), "--output-dir", str(tmp_path), "--temp-dir", str(tmp_path / "temp")])
    result = probe.run_probe(args)
    assert result["phase2_gate"]["status"] == "descriptive_only"
    assert not list((tmp_path / "temp").glob("*.sqlite3"))
    report = (tmp_path / "phase1-results.md").read_text()
    assert "v3 dropped the numeric threshold" in report and "v5 superseded" in report
    assert "G2-A1-002" not in report and "1 triples" in report
    assert "Outside top 100" in report and "Any-miss reading" in report
    monkeypatch.setattr(probe, "_write_results", lambda *a: (_ for _ in ()).throw(RuntimeError("report failure")))
    with pytest.raises(RuntimeError, match="report failure"):
        probe.run_probe(args)
    assert not list((tmp_path / "temp").glob("*.sqlite3"))
    monkeypatch.setattr(probe, "get_vesum_connection", lambda *a: (_ for _ in ()).throw(RuntimeError("index failure")))
    with pytest.raises(RuntimeError, match="index failure"):
        probe._create_lemma_index(sources, vesum, tmp_path / "temp")
    assert not list((tmp_path / "temp").glob("*.sqlite3"))
