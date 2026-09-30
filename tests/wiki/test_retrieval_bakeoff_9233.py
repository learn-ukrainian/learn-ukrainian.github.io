from __future__ import annotations

import json
import sqlite3
from contextlib import nullcontext
from pathlib import Path

import pytest

from scripts.wiki.diagnostics import retrieval_bakeoff_9233 as bakeoff


def _vesum(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE forms_all (id INTEGER PRIMARY KEY, word_form TEXT, lemma TEXT, pos TEXT);
        CREATE TABLE form_markers (form_id INTEGER, marker TEXT);
        INSERT INTO forms_all VALUES
          (1,'як','як','adv.int'), (2,'апостроф','апостроф','noun'),
          (3,'пишемо','писати','verb'), (4,'з','з','prep'),
          (5,'із','із','prep'), (6,'зі','зі','prep'),
          (7,'і','і','conj'), (8,'й','й','conj');
        """
    )
    conn.commit()
    return conn


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
    assert {item["arm"] for item in key} == {"L", "D:model"}
    assert result["queries"] == 1


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
    calls: list[list[str]] = []

    class StubEncoder:
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

    class FlagStub:
        def compute_score(self, pairs, normalize):
            assert normalize is True and len(pairs) == 2
            return [0.1, 0.9]

    class CrossEncoderStub:
        def predict(self, pairs, **kwargs):
            assert len(pairs) == 2
            return [0.9, 0.1]

    class JinaStub:
        def rerank(self, query, documents):
            assert query == "query" and documents == ["first", "second"]
            return [{"index": 1}, {"index": 0}]

    assert bakeoff._rerank(FlagStub(), {"kind": "flag"}, "query", candidates) == ["b", "a"]
    assert bakeoff._rerank(CrossEncoderStub(), {"kind": "cross_encoder"}, "query", candidates) == ["a", "b"]
    assert bakeoff._rerank(JinaStub(), {"kind": "jina"}, "query", candidates) == ["b", "a"]


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
    vector_conn.execute("CREATE TABLE vectors (chunk_id TEXT, text_sha256 TEXT, vector BLOB, dimensions INTEGER)")
    vector_conn.execute("INSERT INTO vectors VALUES ('c1','',x'0000803f00000000',2)")
    vector_conn.commit()
    vector_conn.close()
    repo = "intfloat/multilingual-e5-small"
    (work / f"{repo.replace('/', '--')}-encode.json").write_text(json.dumps({"index_size_bytes": 123, "wall_seconds": 4.0, "steady_state_chunks_per_second": 2.0, "peak_rss_bytes": 456}), encoding="utf-8")
    query = {"id": "G3-001", "family": "G3", "query": "query", "stratum": "area", "cluster": "G3-001"}
    monkeypatch.setattr(bakeoff, "_load_queries", lambda: ([query], [query]))
    monkeypatch.setattr(bakeoff, "_fts_search", lambda *args, **kwargs: ["c2"])
    monkeypatch.setattr(bakeoff, "get_vesum_connection", lambda path: nullcontext(object()))
    monkeypatch.setattr(bakeoff, "_new_encoder", lambda model, root: (object(), {"kind": "sentence", "max_tokens": 32}))
    monkeypatch.setattr(bakeoff, "_query_vector", lambda *args: [1.0, 0.0])
    monkeypatch.setattr(bakeoff, "_dense_rank", lambda *args, **kwargs: ["c1"])
    monkeypatch.setattr(bakeoff, "_new_reranker", lambda model, root: (object(), {"kind": "test", "max_tokens": 32}))
    monkeypatch.setattr(bakeoff, "_rerank", lambda model, meta, text, candidates: [str(row["chunk_id"]) for row in candidates][::-1])

    result = bakeoff.search(tmp_path / "unused.db", work, models=[repo], rerankers=["Qwen/Qwen3-Reranker-0.6B"], query_limit=1, batch_size=2, families=["G3"])
    assert set(result["arms"]) == {"L", f"D:{repo}", f"H:{repo}", f"R:Qwen/Qwen3-Reranker-0.6B|{repo}"}
    assert result["arms"][f"H:{repo}"]["G3-001"][0] == "c1"
    assert result["vector_coverage"][repo] == {"indexed_vectors": 1, "corpus_rows": 2}
    assert result["costs"][f"D:{repo}"]["index_size_bytes"] == 123


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


def test_paired_cluster_bootstrap_keeps_query_pairs_and_clusters_together() -> None:
    values = {"base": (1.0, 0.5), "inflected": (0.8, 0.3), "other": (0.4, 0.0)}
    clusters = {"base": "pair-1", "inflected": "pair-1", "other": "pair-2"}
    first = bakeoff.paired_cluster_bootstrap(values, clusters, iterations=250, seed=19)
    second = bakeoff.paired_cluster_bootstrap(values, clusters, iterations=250, seed=19)
    assert first == second
    assert first["estimate"] == pytest.approx(0.4666666666666666)
    assert first["lower_95"] <= first["estimate"] <= first["upper_95"]
