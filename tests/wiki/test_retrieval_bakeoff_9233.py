from __future__ import annotations

import json
import sqlite3
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.wiki.diagnostics import retrieval_bakeoff_9233 as bakeoff


def _vesum(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE forms_all (id INTEGER PRIMARY KEY, word_form TEXT, lemma TEXT, pos TEXT, tags TEXT DEFAULT '');
        CREATE TABLE form_markers (form_id INTEGER, marker TEXT);
        INSERT INTO forms_all(id,word_form,lemma,pos) VALUES
          (1,'як','як','adv'), (2,'апостроф','апостроф','noun'),
          (3,'пишемо','писати','verb'), (4,'з','з','prep'),
          (5,'із','із','prep'), (6,'зі','зі','prep'),
          (7,'і','і','conj'), (8,'й','й','conj');
        """
    )
    conn.commit()
    return conn


@pytest.fixture(autouse=True)
def fixture_sources_and_vesum(tmp_path: Path, monkeypatch):
    # Synthetic corpora test their own scope; production identity validation
    # is exercised separately with an explicitly nonempty list.
    monkeypatch.setattr(bakeoff, "EXTRA_SOURCES", ())
    path = tmp_path / "fixture-vesum.db"
    _vesum(path).close()
    monkeypatch.setattr(bakeoff, "_default_vesum_db", lambda: path)


def test_lemma_stop_words_and_topic_word_exception(tmp_path: Path) -> None:
    conn = _vesum(tmp_path / "vesum.db")
    assert bakeoff.filter_lemma_query("як пишемо апостроф", conn) == ["пишемо", "апостроф"]
    assert bakeoff.filter_lemma_query("з", conn) == ["з"]
    assert bakeoff.filter_lemma_query("з/із/зі", conn) == ["з", "із", "зі"]
    assert bakeoff.filter_lemma_query("і/й", conn) == ["і", "й"]
    # If filtering would leave fewer than two content terms, preserve the query.
    assert bakeoff.filter_lemma_query("як апостроф", conn) == ["як", "апостроф"]
    conn.close()


def test_reciprocal_rank_fusion_uses_k60_and_stable_ties() -> None:
    rankings = [["a", "x2", "x3", "x4", "b"], ["c", "c2", "c3", "c4", "b", "c6", "c7", "c8", "c9", "a"]]
    assert bakeoff.reciprocal_rank_fusion(rankings, limit=2) == ["b", "a"]
    assert bakeoff.reciprocal_rank_fusion(rankings, k=1, limit=2) == ["a", "c"]


def test_pool_is_blind_and_sealed_key_maps_back(tmp_path: Path) -> None:
    work = tmp_path / "work"
    work.mkdir()
    corpus = sqlite3.connect(work / "corpus.sqlite3")
    corpus.execute("CREATE TABLE chunks (id INTEGER,chunk_id TEXT,title TEXT,text TEXT,source_file TEXT,subject TEXT,parent_section_id INTEGER)")
    corpus.executemany("INSERT INTO chunks VALUES (?,?,?,?,?,?,?)", [(1, "c1", "t1", "текст перший", "ukrmova-a", "ukrmova", None), (2, "c2", "t2", "текст другий", "bukvar-b", "bukvar", None)])
    corpus.commit()
    corpus.close()
    (work / "search-results.json").write_text(json.dumps({
        "queries": [{"id": "G3-001", "family": "G3", "query": "приклад", "stratum": "G3-area-kind", "cluster": "G3-001"}],
        "arms": {"L": {"G3-001": ["c1"]}, "D:model": {"G3-001": ["c2"]}},
    }), encoding="utf-8")

    result = bakeoff.pool(work, query_limit=1)
    blind_text = (work / "judging/pool.json").read_text(encoding="utf-8")
    key = json.loads((work / "sealed/pool-key.json").read_text(encoding="utf-8"))
    assert "D:model" not in blind_text and '"L"' not in blind_text
    assert {item["chunk_id"] for item in key} == {"c1", "c2"}
    assert {item["arm"] for item in key if item["arm"]} == {"L", "D:model"}
    assert result["queries"] == 1
    assert '"chunk_id"' not in blind_text and '"source_identity"' not in blind_text
    for item in key:
        expected = bakeoff.hashlib.sha256(f"{item['query_id']}\0{item['chunk_id']}".encode()).hexdigest()[:20]
        assert item["item_id"] == expected
    labels = work / "judging/judge-a.jsonl"
    labels.write_text("already judged")
    with pytest.raises(ValueError, match="overwrite-pool"):
        bakeoff.pool(work)
    assert labels.read_text() == "already judged"
    bakeoff.pool(work, overwrite=True)
    assert labels.read_text() == ""


class StubTokenizer:
    def encode(self, text, **kwargs):
        return list(map(ord, text))

    def decode(self, ids, **kwargs):
        return "".join(map(chr, ids))


def _compute_fixture(monkeypatch, query=None):
    # These existing unit tests isolate pipeline mechanics. Real manifest,
    # budget and refusal gates are exercised without these mocks in v61 tests.
    monkeypatch.setattr(bakeoff, "_validate_run", lambda *a: {"sha256": "run"})
    monkeypatch.setattr(bakeoff, "_measurement_binding", lambda *a: {"run_manifest_sha256": "run"})
    monkeypatch.setattr(bakeoff, "_check_runtime", lambda *a: None)
    monkeypatch.setattr(bakeoff, "_admission", lambda *a: {"admitted_embedders": [bakeoff.E5], "rerankers": {"Qwen/Qwen3-Reranker-0.6B": {"variant": "fp32"}}, "measurements": {"lexical_query_seconds": 1}})
    if query is not None:
        monkeypatch.setattr(bakeoff, "_evaluation", lambda *a: {"queries": [query], "cost_query_ids": [query["id"]], "sha256": "eval"})


def test_encode_stub_is_resumable_and_uses_repository_prefix(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "sources.db"
    conn = sqlite3.connect(source)
    conn.execute("CREATE TABLE textbooks (id INTEGER PRIMARY KEY,chunk_id TEXT,title TEXT,text TEXT,source_file TEXT,subject TEXT,parent_section_id INTEGER)")
    conn.executemany("INSERT INTO textbooks VALUES (?,?,?,?,?,?,?)", [
        (1, "e1", "title one", "first text", "book-one", "ukrmova", None),
        (2, "e2", "title two", "second text", "book-two", "bukvar", None),
        (3, "outside", "other", "excluded", "book-three", "history", None),
    ])
    conn.commit()
    conn.close()
    _compute_fixture(monkeypatch)
    calls: list[list[str]] = []

    class StubEncoder:
        tokenizer = StubTokenizer()

        def encode(self, texts, **kwargs):
            calls.append(list(texts))
            return [[1.0, float(index + 1)] for index, _ in enumerate(texts)]

    monkeypatch.setattr(bakeoff, "_new_encoder", lambda repo, work: (StubEncoder(), {"kind": "sentence", "max_tokens": 64}))
    work = tmp_path / "work"
    first = bakeoff.encode(source, work, "intfloat/multilingual-e5-small", limit=None, batch_size=2)
    second = bakeoff.encode(source, work, "intfloat/multilingual-e5-small", limit=None, batch_size=2)
    assert first["rows_encoded_this_run"] == 2
    assert second["rows_encoded_this_run"] == 0
    assert second["rows_resumed"] == 2
    assert calls == [["passage: first text", "passage: second text"]]


def test_jina_encoder_stub_receives_retrieval_task_prompt() -> None:
    calls = {}

    class StubEncoder:
        def encode(self, texts, **kwargs):
            calls["texts"] = texts
            calls["kwargs"] = kwargs
            return [[1.0, 0.0]]

    model = StubEncoder()
    vector = bakeoff._query_vector(model, {"kind": "jina", "max_tokens": 128}, "запит", "jinaai/jina-embeddings-v5-text-nano")
    assert vector == [1.0, 0.0]
    assert calls["texts"] == ["запит"]
    assert calls["kwargs"]["task"] == "retrieval"
    assert calls["kwargs"]["prompt_name"] == "query"


def test_dense_ranking_uses_cosine_similarity_and_stable_ties(tmp_path: Path) -> None:
    path = tmp_path / "vectors.sqlite3"
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE vectors (chunk_id TEXT, text_sha256 TEXT, vector BLOB, dimensions INTEGER)")
    import numpy as np

    conn.executemany("INSERT INTO vectors VALUES (?,?,?,?)", [
        ("aligned", "", np.asarray([1.0, 0.0], dtype="float32").tobytes(), 2),
        ("also-aligned", "", np.asarray([2.0, 0.0], dtype="float32").tobytes(), 2),
        ("orthogonal", "", np.asarray([0.0, 1.0], dtype="float32").tobytes(), 2),
    ])
    conn.commit()
    conn.close()
    assert bakeoff._dense_rank([1.0, 0.0], path, limit=3) == ["aligned", "also-aligned", "orthogonal"]


def test_rerank_adapters_rank_candidates_without_model_downloads() -> None:
    candidates = [{"chunk_id": "a", "text": "first"}, {"chunk_id": "b", "text": "second"}]

    class CrossEncoderStub:
        tokenizer = StubTokenizer()

        def predict(self, pairs, **kwargs):
            assert len(pairs) == 2
            return [0.9, 0.1]

    class JinaStub:
        _tokenizer = StubTokenizer()

        def rerank(self, query, documents):
            assert query == "query" and documents == ["first", "second"]
            return [{"index": 1}, {"index": 0}]

    assert bakeoff._rerank(CrossEncoderStub(), {"kind": "cross_encoder", "max_tokens": 512}, "query", candidates) == ["a", "b"]
    assert bakeoff._rerank(JinaStub(), {"kind": "jina", "max_tokens": 512}, "query", candidates) == ["b", "a"]


def test_search_orchestration_builds_dense_hybrid_and_reranked_arms(tmp_path: Path, monkeypatch) -> None:
    work = tmp_path / "work"
    work.mkdir()
    corpus = sqlite3.connect(work / "corpus.sqlite3")
    corpus.execute("CREATE TABLE chunks (id INTEGER,chunk_id TEXT,title TEXT,text TEXT,source_file TEXT,subject TEXT,parent_section_id INTEGER)")
    corpus.executemany("INSERT INTO chunks VALUES (?,?,?,?,?,?,?)", [(1, "c1", "t1", "text 1", "book", "ukrmova", None), (2, "c2", "t2", "text 2", "book", "ukrmova", None)])
    corpus.commit()
    corpus.close()
    vectors = work / "embeddings/intfloat--multilingual-e5-small.sqlite3"
    vectors.parent.mkdir()
    vector_conn = sqlite3.connect(vectors)
    vector_conn.execute("CREATE TABLE index_metadata (key TEXT, value TEXT)")
    vector_conn.execute("INSERT INTO index_metadata VALUES ('run_manifest_sha256','run')")
    vector_conn.execute("CREATE TABLE vectors (chunk_id TEXT, text_sha256 TEXT, vector BLOB, dimensions INTEGER)")
    vector_conn.executemany("INSERT INTO vectors VALUES (?,'',x'0000803f00000000',2)", [("c1",), ("c2",)])
    vector_conn.commit()
    vector_conn.close()
    repo = "intfloat/multilingual-e5-small"
    (work / f"{repo.replace('/', '--')}-encode.json").write_text(json.dumps({"index_size_bytes": 123, "wall_seconds": 4.0, "steady_state_chunks_per_second": 2.0, "peak_rss_bytes": 456}), encoding="utf-8")
    query = {"id": "G3-001", "family": "G3", "query": "query", "stratum": "area", "cluster": "G3-001"}
    _compute_fixture(monkeypatch, query)
    monkeypatch.setattr(bakeoff, "_load_queries", lambda: ([query], [query]))
    monkeypatch.setattr(bakeoff, "_fts_search", lambda *args, **kwargs: ["c2"])
    monkeypatch.setattr(bakeoff, "get_vesum_connection", lambda path: nullcontext(object()))
    monkeypatch.setattr(bakeoff, "_new_encoder", lambda model, root: (SimpleNamespace(tokenizer=StubTokenizer()), {"kind": "sentence", "max_tokens": 32}))
    monkeypatch.setattr(bakeoff, "_query_vector", lambda *args: [1.0, 0.0])
    monkeypatch.setattr(bakeoff, "_dense_rank", lambda *args, **kwargs: ["c1"])
    monkeypatch.setattr(bakeoff, "_new_reranker", lambda model, root: (SimpleNamespace(tokenizer=StubTokenizer()), {"kind": "test", "max_tokens": 32}))
    monkeypatch.setattr(bakeoff, "_rerank", lambda model, meta, text, candidates: [str(row["chunk_id"]) for row in candidates][::-1])

    monkeypatch.setattr(bakeoff, "_copy_subset", lambda *args: work / "corpus.sqlite3")
    monkeypatch.setattr(bakeoff, "_isolated_arm", bakeoff._run_arm)
    result = bakeoff.search(tmp_path / "unused.db", work, models=[repo], rerankers=["Qwen/Qwen3-Reranker-0.6B"], query_limit=1, families=["G1", "G2", "G3"])
    assert set(result["arms"]) == {"L", f"D:{repo}", f"H:{repo}", f"R:Qwen/Qwen3-Reranker-0.6B|{repo}"}
    assert result["arms"][f"H:{repo}"]["G3-001"][0] == "c1"
    assert result["vector_coverage"][repo] == {"indexed_vectors": 2, "corpus_rows": 2}
    assert result["costs"][f"D:{repo}"]["index_size_bytes"] == vectors.stat().st_size
    assert result["costs"][f"H:{repo}"]["index_size_bytes"] == vectors.stat().st_size + (work / "corpus.sqlite3").stat().st_size
    assert result["costs"][f"R:Qwen/Qwen3-Reranker-0.6B|{repo}"]["reranker"]["max_tokens"] == 32


def test_strict_and_lenient_labels_drive_recall_scoring(tmp_path: Path, monkeypatch) -> None:
    work = tmp_path / "work"
    (work / "sealed").mkdir(parents=True)
    (work / "judging").mkdir()
    query = {"id": "G3-001", "family": "G3", "query": "приклад", "stratum": "G3-area-kind", "cluster": "G3-001"}
    items = [{"item_id": "i1", "chunk_id": "c1"}, {"item_id": "i2", "chunk_id": "c2"}]
    (work / "search-results.json").write_text(json.dumps({"queries": [query], "arms": {"A": {"G3-001": ["c1", "c2"]}, "B": {"G3-001": ["c1"]}}, "costs": {}}), encoding="utf-8")
    (work / "judging/pool.json").write_text(json.dumps([{"query_id": "G3-001", "query": "приклад", "items": items}]), encoding="utf-8")
    (work / "sealed/pool-key.json").write_text(json.dumps([
        {"query_id": "G3-001", "item_id": "i1", "chunk_id": "c1", "arm": "A"},
        {"query_id": "G3-001", "item_id": "i2", "chunk_id": "c2", "arm": "A"},
        {"query_id": "G3-001", "item_id": "i1", "chunk_id": "c1", "arm": "B"},
    ]), encoding="utf-8")
    labels_a = [
        {"query_id": "G3-001", "item_id": "i1", "usable_quotation": True, "usable_exercise": False, "usable_example": False, "reason": "One line."},
        {"query_id": "G3-001", "item_id": "i2", "usable_quotation": True, "usable_exercise": False, "usable_example": False, "reason": "One line."},
    ]
    labels_b = [
        {"query_id": "G3-001", "item_id": "i1", "usable_quotation": False, "usable_exercise": False, "usable_example": False, "reason": "One line."},
        {"query_id": "G3-001", "item_id": "i2", "usable_quotation": True, "usable_exercise": False, "usable_example": False, "reason": "One line."},
    ]
    a_path, b_path = tmp_path / "a.jsonl", tmp_path / "b.jsonl"
    a_path.write_text("\n".join(json.dumps(row) for row in labels_a) + "\n", encoding="utf-8")
    b_path.write_text("\n".join(json.dumps(row) for row in labels_b) + "\n", encoding="utf-8")
    monkeypatch.setattr(bakeoff, "ROOT", tmp_path)

    result = bakeoff.score(work, a_path, b_path, iterations=20)
    assert bakeoff.stricter_label(True, False) is False
    assert bakeoff.lenient_label(True, False) is True
    assert result["strata"]["A"]["G3-area-kind"]["recall_at_20_strict"] == 1.0
    assert result["strata"]["B"]["G3-area-kind"]["recall_at_20_strict"] == 0.0
    assert result["strata"]["B"]["G3-area-kind"]["recall_at_20_lenient"] == 0.5
    assert result["kappa_gate"] is False
    assert (work / "phase2-results.md").exists()
    assert not (tmp_path / "docs").exists()
    # A same-size label file from a different pool must fail by identity.
    labels_a[0]["item_id"] = "stale-id"
    a_path.write_text("\n".join(json.dumps(row) for row in labels_a))
    with pytest.raises(ValueError, match="label ids"):
        bakeoff.score(work, a_path, b_path, iterations=20)


def test_paired_cluster_bootstrap_keeps_query_pairs_and_clusters_together() -> None:
    values = {"base": (1.0, 0.5), "inflected": (0.8, 0.3), "other": (0.4, 0.0)}
    clusters = {"base": "pair-1", "inflected": "pair-1", "other": "pair-2"}
    first = bakeoff.paired_cluster_bootstrap(values, clusters, iterations=250, seed=19)
    second = bakeoff.paired_cluster_bootstrap(values, clusters, iterations=250, seed=19)
    assert first == second
    assert first["estimate"] == pytest.approx(0.45)
    assert first["lower_95"] <= first["estimate"] <= first["upper_95"]


def _sources(path: Path, rows: list[tuple]) -> None:
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE textbooks (id INTEGER PRIMARY KEY,chunk_id TEXT,title TEXT,text TEXT,source_file TEXT,subject TEXT,parent_section_id INTEGER)")
        conn.executemany("INSERT INTO textbooks VALUES (?,?,?,?,?,?,?)", rows)


def test_unmocked_lemma_index_finds_surface_forms_and_shares_probe_expansion(tmp_path: Path) -> None:
    vesum_path = tmp_path / "vesum.db"
    with _vesum(vesum_path) as conn:
        conn.executemany("INSERT INTO forms_all(id,word_form,lemma,pos) VALUES (?,?,?,?)", [
            (10, "родового", "родовий", "adj"), (11, "відмінка", "відмінок", "noun"),
            (12, "бачу", "бачити", "verb"), (13, "чую", "чути", "verb"),
            (14, "родовий", "родовий", "adj"), (15, "відмінок", "відмінок", "noun"),
        ])
    source = tmp_path / "sources.db"
    _sources(source, [(1, "inflected", "", "родового відмінка", "book", "ukrmova", None),
                      (2, "verbs", "бачу чую", "", "book", "ukrmova", None),
                      (3, "base", "", "родовий відмінок", "book", "ukrmova", None)])
    index = bakeoff._copy_subset(source, tmp_path / "work", vesum_path=vesum_path)
    with bakeoff._ro_connect(index) as conn, bakeoff._ro_connect(vesum_path) as vesum:
        assert "inflected" in bakeoff._fts_search(conn, "родового відмінка", vesum, lemma=True, limit=20)
        assert bakeoff._fts_search(conn, "бачу чую", vesum, lemma=True, limit=20) == ["verbs"]
    probe_index, _ = bakeoff.phase1._create_lemma_index(source, vesum_path, tmp_path / "probe")
    with sqlite3.connect(probe_index) as probe, sqlite3.connect(index) as harness:
        assert probe.execute("SELECT chunk_id,title_terms,text_terms FROM lemma_fts ORDER BY rowid").fetchall() == harness.execute("SELECT chunk_id,title,text FROM chunks_fts ORDER BY rowid").fetchall()


def test_pool_deduplicates_before_cap_and_keeps_conceptual_queries() -> None:
    queries, _ = bakeoff._load_queries()
    chosen = bakeoff._pool_queries(queries)
    assert len(chosen) == 120
    assert bakeoff.Counter(q["family"] for q in chosen) == {"G1": 7, "G2": 24, "G3": 89}
    assert len({q["query"] for q in chosen}) == 120
    assert chosen == bakeoff._pool_queries(queries)
    assert len(bakeoff._pool_queries(queries, 5)) == 5


def test_loaded_clusters_follow_query_string_and_term_triple() -> None:
    queries, _ = bakeoff._load_queries()
    for family, expected in [("G1", 7), ("G2", 12)]:
        subset = [q for q in queries if q["family"] == family]
        assert len({q["cluster"] for q in subset}) == expected
    g2 = [q for q in queries if q["family"] == "G2"]
    for query in g2:
        triple = json.loads(query["cluster"][3:])
        assert len(triple) == 3 and query["query"] in triple
        assert all(q["cluster"] == query["cluster"] for q in g2 if q["query"] in triple)


def test_pool_ids_stable_in_two_hash_seed_subprocesses(tmp_path: Path) -> None:
    import os
    import subprocess
    import sys

    code = '''
import json, sqlite3, sys
from pathlib import Path
from types import SimpleNamespace
from scripts.wiki.diagnostics import retrieval_bakeoff_9233 as b
work = Path(sys.argv[1]); work.mkdir()
with sqlite3.connect(work / "corpus.sqlite3") as c:
 c.execute("CREATE TABLE chunks(id INTEGER,chunk_id TEXT,title TEXT,text TEXT,source_file TEXT,subject TEXT,parent_section_id INTEGER)")
 c.executemany("INSERT INTO chunks VALUES (?,?,?,?,?,?,?)", [(i, f"c{i}", "", f"text {i}", "book", "ukrmova", None) for i in range(8)])
(work / "search-results.json").write_text(json.dumps({"queries": [{"id":"q","family":"G3","query":"query"}], "arms":{"L":{"q":[f"c{i}" for i in range(8)]}}}))
b.pool(work)
print((work / "sealed/pool-key.json").read_text())
print((work / "judging/pool.json").read_text())
'''
    outputs = [subprocess.check_output([sys.executable, "-c", code, str(tmp_path / f"seed-{seed}")], env={**os.environ, "PYTHONHASHSEED": str(seed)}, text=True, timeout=60) for seed in (17, 91)]
    assert outputs[0] == outputs[1]


def test_function_filter_preserves_topics_and_content_homonyms(tmp_path: Path) -> None:
    conn = _vesum(tmp_path / "vesum.db")
    conn.executemany("INSERT INTO forms_all(id,word_form,lemma,pos,tags) VALUES (?,?,?,?,?)", [
        (10, "у", "у", "prep", "prep"), (11, "в", "в", "prep", "prep"),
        (12, "біля", "біля", "prep", "prep"), (13, "до", "до", "prep", "prep"),
        (14, "навпроти", "навпроти", "prep", "prep"), (15, "навпроти", "навпроти", "adv", "adv"),
        (16, "поруч", "поруч", "prep", "prep"), (17, "поруч", "поруч", "adv", "adv"),
        (18, "раніше", "раніше", "prep", "prep"), (19, "раніше", "раніше", "adv", "adv:compc:predic"),
        (20, "де", "де", "adv", "adv:pron:int:rel"),
    ])
    _, g3 = bakeoff._load_queries()
    by_id = {q["id"]: q["query"] for q in g3}
    for qid, topics in [("G3-028", {"у", "в"}), ("G3-066", {"біля", "до", "навпроти"}), ("G3-067", {"і", "й"}), ("G3-138", {"у", "в"})]:
        assert topics <= set(bakeoff.filter_lemma_query(by_id[qid], conn))
    assert bakeoff.filter_lemma_query("де поруч раніше", conn) == ["поруч", "раніше"]
    assert bakeoff.filter_lemma_query("з пишемо апостроф", conn) == ["пишемо", "апостроф"]
    conn.close()


def test_cached_corpus_digest_and_missing_source_identity(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "sources.db"
    _sources(source, [(1, "c1", "", "text", "book", "ukrmova", None)])
    work = tmp_path / "work"
    target = bakeoff._copy_subset(source, work)
    assert bakeoff._copy_subset(source, work) == target
    with sqlite3.connect(target) as conn:
        conn.execute("UPDATE chunks SET text='tampered'")
    with pytest.raises(ValueError, match="digest"):
        bakeoff._copy_subset(source, work)
    monkeypatch.setattr(bakeoff, "EXTRA_SOURCES", ("pohribnyi-ukrainska-literaturna-vymova-1992",))
    with pytest.raises(ValueError, match="zero rows"):
        bakeoff._copy_subset(source, tmp_path / "empty")


def test_bm25_title_weight_in_harness_and_probe(tmp_path: Path) -> None:
    source = tmp_path / "sources.db"
    _sources(source, [(1, "text", "", "апостроф", "book", "ukrmova", None),
                      (2, "title", "апостроф", "", "book", "ukrmova", None)])
    target = bakeoff._copy_subset(source, tmp_path / "work")
    with bakeoff._ro_connect(target) as conn, bakeoff._ro_connect(bakeoff._default_vesum_db()) as vesum:
        assert bakeoff._fts_search(conn, "апостроф", vesum, lemma=True, limit=2) == ["title", "text"]
        probe, _ = bakeoff.phase1._create_lemma_index(source, bakeoff._default_vesum_db(), tmp_path / "probe")
        assert bakeoff.phase1._lemma_search(probe, "апостроф", vesum, 2) == ["title", "text"]


def test_complete_arm_latency_includes_all_stages(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "sources.db"
    _sources(source, [(1, "c1", "", "text", "book", "ukrmova", None)])
    work = tmp_path / "work"
    corpus = bakeoff._copy_subset(source, work)
    repo = "intfloat/multilingual-e5-small"
    vectors = work / "embeddings" / (repo.replace("/", "--") + ".sqlite3")
    vectors.parent.mkdir()
    vectors.write_text("fixture")
    clock = [0.0]
    def stage(seconds, value):
        def call(*args, **kwargs):
            clock[0] += seconds
            return value
        return call
    monkeypatch.setattr(bakeoff.time, "perf_counter", lambda: clock[0])
    monkeypatch.setattr(bakeoff, "_new_encoder", lambda *args: (SimpleNamespace(tokenizer=StubTokenizer()), {"kind": "test", "max_tokens": 512}))
    monkeypatch.setattr(bakeoff, "_new_reranker", lambda *args: (SimpleNamespace(tokenizer=StubTokenizer()), {"kind": "test", "max_tokens": 8192}))
    monkeypatch.setattr(bakeoff, "_fts_search", stage(1, ["c1"]))
    monkeypatch.setattr(bakeoff, "_query_vector", stage(2, [1]))
    monkeypatch.setattr(bakeoff, "_load_vectors", lambda *a: (["c1"], [[1]]))
    monkeypatch.setattr(bakeoff, "_dense_rank", stage(3, ["c1"]))
    monkeypatch.setattr(bakeoff, "reciprocal_rank_fusion", stage(4, ["c1"]))
    monkeypatch.setattr(bakeoff, "_rerank", stage(5, ["c1"]))
    query = {"id": "q", "query": "query", "family": "G3"}
    _compute_fixture(monkeypatch, query)
    bakeoff._write_json(work / "search-progress" / (bakeoff.hashlib.sha256(f"H:{repo}".encode()).hexdigest() + ".json"), {"binding": {"run_manifest_sha256": "run"}, "rankings": {"q": ["c1"]}})
    for arm, embedder, ranker, expected in [("L", None, None, 1), ("D:x", repo, None, 5), ("H:x", repo, None, 10), ("R:x", repo, "ranker", 15)]:
        result = bakeoff._run_arm(corpus, work, [query], arm, embedder, ranker)
        assert result["cost"]["query_p95_seconds"] == expected
        assert result["cost"]["query_n"] == 1


def test_guarded_arm_dispatches_complete_lexical_pipeline(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "sources.db"
    _sources(source, [(1, "c1", "", "апостроф", "book", "ukrmova", None)])
    work = tmp_path / "work"
    corpus = bakeoff._copy_subset(source, work)
    query = {"id": "q", "query": "апостроф", "family": "G3"}
    _compute_fixture(monkeypatch, query)
    guarded = []
    def guard(function, args, kwargs, root, step, projection):
        guarded.append((step, projection))
        return function(*args, **kwargs)
    monkeypatch.setattr(bakeoff, "_guarded_step", guard)
    result = bakeoff._isolated_arm(corpus, work, [query], "L", None, None, bakeoff._default_vesum_db())
    assert guarded[0] == ("search-timing:L", 1800)
    assert guarded[1][0] == "search:L" and guarded[1][1] > 0
    assert result["rankings"] == {"q": ["c1"]}
    assert result["cost"]["query_peak_rss_bytes"] > 0
    assert result["cost"]["query_p95_seconds"] > 0


def test_model_config_prompts_and_runtime_limits_without_downloads(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(bakeoff, "_model_options", lambda *a: {"revision": "a" * 40})
    import sys
    from types import SimpleNamespace

    class Encoder:
        def __init__(self, repo, **kwargs):
            self.max_seq_length = 8192
            self.tokenizer = SimpleNamespace(truncation_side="left")
            self.prompts = {"query": "query: ", "document": "document: "}
            self.calls = []
        def encode(self, texts, **kwargs):
            self.calls.append((texts, kwargs))
            return [[1.0, 0.0]]
    class Cross:
        def __init__(self, *args, **kwargs):
            assert "max_length" not in kwargs
            self.tokenizer = SimpleNamespace(model_max_length=8192, truncation_side="left")
            self.model = SimpleNamespace(config=SimpleNamespace(max_position_embeddings=8194), float=lambda: None)
    monkeypatch.setitem(sys.modules, "sentence_transformers", SimpleNamespace(SentenceTransformer=Encoder, CrossEncoder=Cross))
    repo = "Snowflake/snowflake-arctic-embed-l-v2.0"
    encoder, meta = bakeoff._new_encoder(repo, tmp_path)
    bakeoff._query_vector(encoder, meta, "query", repo)
    bakeoff._encode_batch(encoder, meta, ["document"], repo, 1)
    assert encoder.calls[0][0] == ["query"] and encoder.calls[0][1]["prompt_name"] == "query"
    assert encoder.calls[1][0] == ["document"] and encoder.calls[1][1]["prompt_name"] == "document"
    assert meta["prefixes"] == {"query": "query: ", "passage": "document: "}
    assert encoder.tokenizer.truncation_side == "right"
    ranker, rmeta = bakeoff._new_reranker("BAAI/bge-reranker-v2-m3", tmp_path)
    assert ranker.max_seq_length == rmeta["max_tokens"] == 8192
    assert ranker.tokenizer.truncation_side == "right"
    assert bakeoff.EMBEDDERS["Qwen/Qwen3-Embedding-0.6B"]["query_prefix"].endswith("\nQuery:")
    with pytest.raises(ValueError, match="finite token limit"):
        bakeoff._model_token_limit(SimpleNamespace(model_max_length=10**30), SimpleNamespace())


def test_native_jina_limits_are_recorded_without_downloads(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(bakeoff, "_model_options", lambda *a: {"revision": "a" * 40})
    import sys
    from types import SimpleNamespace

    class Jina:
        config = SimpleNamespace(max_position_embeddings=131072)
        _tokenizer = SimpleNamespace(model_max_length=131072, truncation_side="left")
        def to(self, device):
            return self
        def float(self):
            return self

        def eval(self):
            return self
        def _ensure_tokenizer(self):
            pass
        def rerank(self, query, documents):
            max_query_length = 1024
            max_doc_length = 8192
            return max_query_length, max_doc_length
    monkeypatch.setitem(sys.modules, "transformers", SimpleNamespace(AutoModel=SimpleNamespace(from_pretrained=lambda *a, **kw: Jina())))
    model, meta = bakeoff._new_reranker("jinaai/jina-reranker-v3.5", tmp_path)
    assert meta["max_query_length"] == 1024 and meta["max_doc_length"] == 8192
    assert meta["max_tokens"] == 131072
    assert model._tokenizer.truncation_side == "right"
    assert "first 128 + last 384" in meta["truncation"]


def test_qwen_yes_no_scoring_preserves_template_without_joint_truncation(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(bakeoff, "_model_options", lambda *a: {"revision": "a" * 40})
    import sys
    from types import SimpleNamespace

    import numpy as np

    def softmax(values, dim):
        assert dim == 1
        weights = np.exp(values - values.max(axis=dim, keepdims=True))
        return weights / weights.sum(axis=dim, keepdims=True)

    torch = SimpleNamespace(tensor=np.asarray, no_grad=nullcontext, softmax=softmax)
    monkeypatch.setitem(sys.modules, "torch", torch)

    class Tokenizer:
        model_max_length = 100
        def encode(self, text, **kwargs):
            assert "max_length" not in kwargs and "truncation" not in kwargs
            if "<Query>:" in text:
                assert "<Query>: query" in text and "<Document>:" in text
                return [3, 4, 5]
            if text in {"document", "query"}:
                return [3]
            return [1, 2] if text.startswith("<|im_start|>") else [8, 9]

        def decode(self, ids, **kwargs):
            return "document"

        def pad(self, inputs, **kwargs):
            assert inputs["input_ids"] == [[1, 2, 3, 4, 5, 8, 9]]
            return {"input_ids": torch.tensor(inputs["input_ids"])}
        def convert_tokens_to_ids(self, text):
            return {"no": 0, "yes": 1}[text]
    class Model:
        config = SimpleNamespace(max_position_embeddings=128)
        def to(self, device):
            return self
        def float(self):
            return self

        def eval(self):
            return self
        def __call__(self, **inputs):
            return SimpleNamespace(logits=torch.tensor([[[0.0, 2.0]]]))
    tokenizer = Tokenizer()
    def new_tokenizer(*args, **kwargs):
        assert kwargs["truncation_side"] == "right"
        return tokenizer
    monkeypatch.setitem(sys.modules, "transformers", SimpleNamespace(AutoTokenizer=SimpleNamespace(from_pretrained=new_tokenizer), AutoModelForCausalLM=SimpleNamespace(from_pretrained=lambda *a, **kw: Model())))
    adapter, meta = bakeoff._new_reranker("Qwen/Qwen3-Reranker-0.6B", tmp_path)
    assert meta["max_tokens"] == 100
    assert bakeoff._qwen_scores(adapter, meta, "query", ["document"]) == pytest.approx([0.880797])
    assert bakeoff._rerank(adapter, meta, "query", [{"chunk_id": "c", "text": "document"}]) == ["c"]
    assert bakeoff._rerank(adapter, meta, "query", []) == []


def test_peak_rss_platform_units(monkeypatch) -> None:
    from types import SimpleNamespace

    monkeypatch.setattr(bakeoff.resource, "getrusage", lambda *args: SimpleNamespace(ru_maxrss=10))
    monkeypatch.setattr(bakeoff.sys, "platform", "darwin")
    assert bakeoff._peak_rss_bytes() == 10
    monkeypatch.setattr(bakeoff.sys, "platform", "linux")
    assert bakeoff._peak_rss_bytes() == 10240


def test_repeated_g1_queries_keep_every_known_citation(tmp_path: Path, monkeypatch) -> None:
    work = tmp_path / "work"
    work.mkdir()
    with sqlite3.connect(work / "corpus.sqlite3") as conn:
        conn.execute("CREATE TABLE chunks(id INTEGER,chunk_id TEXT,title TEXT,text TEXT,source_file TEXT,subject TEXT,parent_section_id INTEGER)")
        conn.executemany("INSERT INTO chunks VALUES (?,?,?,?,?,?,?)", [(1, "c1", "", "one", "book", "ukrmova", None), (2, "c2", "", "two", "book", "ukrmova", None)])
    queries = [{"id": "g1a", "family": "G1", "query": "same", "gold_chunk_id": "c1"}, {"id": "g1b", "family": "G1", "query": "same", "gold_chunk_id": "c2"}]
    monkeypatch.setattr(bakeoff, "_load_queries", lambda: (queries, []))
    (work / "search-results.json").write_text(json.dumps({"queries": queries, "arms": {"L": {}}}))
    result = bakeoff.pool(work)
    assert result["queries"] == 1 and result["items"] == 2
    key = json.loads((work / "sealed/pool-key.json").read_text())
    assert {row["chunk_id"] for row in key} == {"c1", "c2"}


def test_corpus_manifest_and_cli_paths(tmp_path: Path, monkeypatch, capsys) -> None:
    source = tmp_path / "sources.db"
    _sources(source, [(1, "c1", "", "text", "book", "ukrmova", None)])
    work = tmp_path / "work"
    assert bakeoff.main(["corpus", "--sources-db", str(source), "--work-dir", str(work)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["rows"] == 1 and result["identity_counts"] == {"ukrmova": 1}
    assert len(result["row_digest_sha256"]) == 64
    with pytest.raises(ValueError, match="outside"):
        bakeoff._work_dir(bakeoff.ROOT / "scratch")
    args = bakeoff.build_parser().parse_args(["pool", "--work-dir", str(work), "--overwrite-pool"])
    assert args.overwrite_pool
    with pytest.raises(SystemExit):
        bakeoff.build_parser().parse_args(["search", "--work-dir", str(work), "--batch-size", "2"])


def test_example_agreement_is_diagnostic_not_decision_gate(tmp_path: Path, monkeypatch) -> None:
    # Reuse a fully exercised pool fixture, then make the two decision labels
    # agree while the example-only appendix label disagrees.
    test_strict_and_lenient_labels_drive_recall_scoring(tmp_path, monkeypatch)
    work = tmp_path / "work"
    pool = json.loads((work / "judging/pool.json").read_text())
    paths = [tmp_path / "a.jsonl", tmp_path / "b.jsonl"]
    for index, path in enumerate(paths):
        path.write_text("\n".join(json.dumps({"query_id": "G3-001", "item_id": item["item_id"], "usable_quotation": True, "usable_exercise": False, "usable_example": bool(index), "reason": "Decision labels agree."}) for item in pool[0]["items"]))
    result = bakeoff.score(work, *paths, iterations=20)
    assert result["cohen_kappa"]["usable_example"] == 0.0
    assert result["kappa_gate"] is True
