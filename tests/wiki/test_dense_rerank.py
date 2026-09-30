from __future__ import annotations

import sqlite3
import sys
import types
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from wiki import dense_rerank


class FakeEncoder:
    def encode(self, texts: list[str], batch_size: int = 8, max_length: int = 8192) -> np.ndarray:
        rows = []
        for text in texts:
            value = float(text.split(":")[0])
            rows.append(np.full(dense_rerank.EMBEDDING_DIMS, value, dtype=np.float16))
        return np.stack(rows, axis=0)


def test_iter_textbook_units_includes_unsectioned_chunks():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE textbook_sections (
            section_id INTEGER, source_file TEXT, section_title TEXT, full_text TEXT
        );
        CREATE TABLE textbooks (
            id INTEGER, chunk_id TEXT, source_file TEXT, title TEXT, text TEXT,
            parent_section_id INTEGER
        );
        INSERT INTO textbook_sections VALUES (7, 'section-book', 'Section', 'section text');
        INSERT INTO textbooks VALUES (1, 'section-chunk', 'section-book', 'Child', 'child text', 7);
        INSERT INTO textbooks VALUES (2, 'ulp-chunk', 'ulp-book', 'ULP title', 'unsectioned text', NULL);
        """
    )

    units = list(dense_rerank._iter_textbook_units(conn))

    assert [unit.unit_key for unit in units] == [
        "textbook_sections:7",
        "textbook_sections:ulp-chunk",
    ]
    assert units[1].text == "unsectioned text"
    assert units[1].parent_key == "ulp-book"
    conn.close()


def test_encode_texts_preserves_original_order_after_sorted_batching(monkeypatch):
    texts = ["3: long", "1: short", "2: medium"]
    encoder = FakeEncoder()

    monkeypatch.setattr(
        dense_rerank,
        "_token_count",
        lambda text, *, max_length: max(1, len(text.split())),
    )
    monkeypatch.setattr(
        dense_rerank,
        "_sorted_token_batches",
        lambda _texts, **_kwargs: [[1, 2], [0]],
    )

    vectors = dense_rerank.encode_texts(
        texts,
        encoder=encoder,
        max_length=512,
        max_rows=2,
        max_tokens=64,
    )

    assert vectors.shape == (3, dense_rerank.EMBEDDING_DIMS)
    assert vectors[:, 0].tolist() == [3.0, 1.0, 2.0]


def test_rerank_sections_assigns_textbook_unit_keys_before_delegating(monkeypatch):
    captured: dict[str, object] = {}

    def fake_rerank_candidates(query, candidates, *, corpus, limit, manifest_db, encoder):
        captured["query"] = query
        captured["candidates"] = candidates
        captured["corpus"] = corpus
        captured["limit"] = limit
        captured["manifest_db"] = manifest_db
        captured["encoder"] = encoder
        return candidates[:limit]

    monkeypatch.setattr(dense_rerank, "rerank_candidates", fake_rerank_candidates)

    sections = [
        {"section_id": 2, "section_score": 3},
        {"section_id": 1, "section_score": 5, "unit_key": "textbook_sections:custom"},
    ]

    reranked = dense_rerank.rerank_sections(
        "апостроф наголос гортань",
        sections,
        limit=2,
        encoder=object(),
    )

    assert captured["corpus"] == "textbook_sections"
    assert captured["limit"] == 2
    assert [row["unit_key"] for row in captured["candidates"]] == [
        "textbook_sections:2",
        "textbook_sections:custom",
    ]
    assert reranked == captured["candidates"]


_FLAG_MODEL_CALLS: list[dict[str, object]] = []


class _FakeBGEM3FlagModel:
    def __init__(self, model_name: str, **kwargs: object) -> None:
        _FLAG_MODEL_CALLS.append({"model_name": model_name, **kwargs})


def _install_fake_flagembedding(monkeypatch) -> None:
    _FLAG_MODEL_CALLS.clear()
    monkeypatch.setitem(
        sys.modules,
        "FlagEmbedding",
        types.SimpleNamespace(BGEM3FlagModel=_FakeBGEM3FlagModel),
    )


@pytest.mark.parametrize(("device", "use_fp16"), [("cpu", False), ("cuda:0", True), ("mps", True)])
def test_flagembedding_encoder_loads_bge_m3_on_one_device(monkeypatch, device, use_fp16):
    monkeypatch.delenv(dense_rerank.NO_DENSE_ENV, raising=False)
    _install_fake_flagembedding(monkeypatch)
    monkeypatch.setattr(dense_rerank, "_select_device", lambda: device)

    encoder = dense_rerank.FlagEmbeddingEncoder()

    assert encoder.device == device
    assert [
        {"model_name": "BAAI/bge-m3", "use_fp16": use_fp16, "pooling_method": "cls", "devices": device}
    ] == _FLAG_MODEL_CALLS


def test_flagembedding_encoder_honours_no_dense_switch(monkeypatch):
    monkeypatch.setenv(dense_rerank.NO_DENSE_ENV, "1")
    _install_fake_flagembedding(monkeypatch)

    with pytest.raises(dense_rerank.DenseEncoderUnavailableError, match=dense_rerank.NO_DENSE_ENV):
        dense_rerank.FlagEmbeddingEncoder()
    assert _FLAG_MODEL_CALLS == []


def test_flagembedding_encoder_missing_ml_stack_is_unavailable(monkeypatch):
    monkeypatch.delenv(dense_rerank.NO_DENSE_ENV, raising=False)
    monkeypatch.setitem(sys.modules, "FlagEmbedding", None)

    with pytest.raises(dense_rerank.DenseEncoderUnavailableError):
        dense_rerank.FlagEmbeddingEncoder(device="cpu")


def test_flagembedding_encoder_unreachable_weights_are_unavailable(monkeypatch):
    monkeypatch.delenv(dense_rerank.NO_DENSE_ENV, raising=False)

    def offline_model(*_args, **_kwargs):
        raise OSError("We couldn't connect to 'https://huggingface.co' to load BAAI/bge-m3")

    monkeypatch.setitem(sys.modules, "FlagEmbedding", types.SimpleNamespace(BGEM3FlagModel=offline_model))

    with pytest.raises(dense_rerank.DenseEncoderUnavailableError, match="huggingface"):
        dense_rerank.FlagEmbeddingEncoder(device="cpu")


def test_rerank_candidates_degrades_to_fts_order_when_encoder_unavailable(monkeypatch):
    monkeypatch.setenv(dense_rerank.NO_DENSE_ENV, "1")
    monkeypatch.setattr(dense_rerank, "_ENCODER", None)
    monkeypatch.setattr(dense_rerank, "_QUERY_CACHE", {})
    index = dense_rerank.CorpusEmbeddingIndex(
        corpus="test_corpus",
        shards={0: np.zeros((2, dense_rerank.EMBEDDING_DIMS), dtype=np.float16)},
        unit_rows={"1": (0, 0), "2": (0, 1)},
    )
    monkeypatch.setattr(dense_rerank, "load_corpus_index", lambda *a, **kw: index)

    results = dense_rerank.rerank_candidates(
        "query",
        [{"unit_key": "1", "fts_score": -5.0}, {"unit_key": "2", "fts_score": -10.0}],
        corpus="test_corpus",
    )

    assert [row["unit_key"] for row in results] == ["2", "1"]
    assert {row["dense_score"] for row in results} == {0.0}
    assert {row["cosine_score"] for row in results} == {0.0}


def test_rerank_candidates_truncates_by_keyword_rank_when_encoder_unavailable(monkeypatch):
    monkeypatch.setenv(dense_rerank.NO_DENSE_ENV, "1")
    index = dense_rerank.CorpusEmbeddingIndex(
        corpus="test_corpus",
        shards={0: np.zeros((2, dense_rerank.EMBEDDING_DIMS), dtype=np.float16)},
        unit_rows={"1": (0, 0), "2": (0, 1)},
    )
    monkeypatch.setattr(dense_rerank, "load_corpus_index", lambda *a, **kw: index)

    results = dense_rerank.rerank_candidates(
        "query",
        [
            {"unit_key": "1", "keyword_rank": 2, "fts_score": -100.0},
            {"unit_key": "2", "keyword_rank": 1, "fts_score": -1.0},
        ],
        corpus="test_corpus",
        limit=1,
    )

    assert [row["unit_key"] for row in results] == ["2"]
    assert results[0]["keyword_rank"] == 1


def _two_row_index(monkeypatch) -> None:
    shard = np.zeros((2, dense_rerank.EMBEDDING_DIMS), dtype=np.float16)
    shard[0, 0] = 1.0
    shard[1, 1] = 1.0
    index = dense_rerank.CorpusEmbeddingIndex(
        corpus="test_corpus", shards={0: shard}, unit_rows={"1": (0, 0), "2": (0, 1)}
    )
    monkeypatch.setattr(dense_rerank, "load_corpus_index", lambda *a, **kw: index)
    monkeypatch.setattr(dense_rerank, "_ENCODER", None)
    monkeypatch.setattr(dense_rerank, "_QUERY_CACHE", {})


# FTS puts "2" first; the query vector below points at unit "1".
_CANDIDATES = [{"unit_key": "1", "fts_score": -5.0}, {"unit_key": "2", "fts_score": -10.0}]


class _QueryEncoder:
    def encode(self, texts, batch_size=1, max_length=512):
        vector = np.zeros((1, dense_rerank.EMBEDDING_DIMS), dtype=np.float16)
        vector[0, 0] = 1.0
        return vector


def test_rerank_candidates_falls_back_to_fts_when_first_encode_fails(monkeypatch):
    monkeypatch.delenv(dense_rerank.NO_DENSE_ENV, raising=False)
    monkeypatch.setenv(dense_rerank.CPU_DENSE_ENV, "1")
    monkeypatch.setattr(dense_rerank, "_select_device", lambda: "cuda:0")
    _two_row_index(monkeypatch)

    class _DeviceFailingModel:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def encode(self, *_args, **_kwargs):
            raise RuntimeError("CUDA out of memory. Tried to allocate 2.00 GiB")

    monkeypatch.setitem(sys.modules, "FlagEmbedding", types.SimpleNamespace(BGEM3FlagModel=_DeviceFailingModel))

    results = dense_rerank.rerank_candidates("query", _CANDIDATES, corpus="test_corpus")

    assert [row["unit_key"] for row in results] == ["2", "1"]
    assert {row["dense_score"] for row in results} == {0.0}


def test_rerank_candidates_is_keyword_only_on_cpu_without_opt_in(monkeypatch):
    monkeypatch.delenv(dense_rerank.NO_DENSE_ENV, raising=False)
    monkeypatch.delenv(dense_rerank.CPU_DENSE_ENV, raising=False)
    monkeypatch.setattr(dense_rerank, "_accelerator_available", lambda: False)
    _two_row_index(monkeypatch)

    def _must_not_load():
        raise AssertionError("the encoder must not load on a CPU host without opt-in")

    monkeypatch.setattr(dense_rerank, "_get_encoder", _must_not_load)

    results = dense_rerank.rerank_candidates("query", _CANDIDATES, corpus="test_corpus")

    assert [row["unit_key"] for row in results] == ["2", "1"]
    assert {row["dense_score"] for row in results} == {0.0}


@pytest.mark.parametrize(
    "failure",
    [RuntimeError("CUDA driver initialization failed"), MemoryError(), OSError("libcudart.so: cannot open")],
)
def test_accelerator_probe_failure_means_no_accelerator(monkeypatch, failure):
    def failing_select_device():
        raise failure

    monkeypatch.setattr(dense_rerank, "_select_device", failing_select_device)
    dense_rerank._accelerator_available.cache_clear()
    try:
        assert dense_rerank._accelerator_available() is False
    finally:
        dense_rerank._accelerator_available.cache_clear()


def test_dense_rerank_enabled_checks_switch_and_index_before_device(monkeypatch, tmp_path):
    monkeypatch.delenv(dense_rerank.NO_DENSE_ENV, raising=False)
    monkeypatch.delenv(dense_rerank.CPU_DENSE_ENV, raising=False)

    def _must_not_probe():
        raise AssertionError("device discovery must not run without an index or with dense switched off")

    monkeypatch.setattr(dense_rerank, "_accelerator_available", _must_not_probe)
    assert dense_rerank.dense_rerank_enabled("test_corpus", manifest_db=tmp_path / "missing.db") is False

    _two_row_index(monkeypatch)
    monkeypatch.setenv(dense_rerank.NO_DENSE_ENV, "1")
    assert dense_rerank.dense_rerank_enabled("test_corpus") is False

    monkeypatch.delenv(dense_rerank.NO_DENSE_ENV)
    monkeypatch.setattr(dense_rerank, "_accelerator_available", lambda: False)
    assert dense_rerank.dense_rerank_enabled("test_corpus") is False
    monkeypatch.setattr(dense_rerank, "_accelerator_available", lambda: True)
    assert dense_rerank.dense_rerank_enabled("test_corpus") is True


@pytest.mark.parametrize(("accelerator", "cpu_opt_in"), [(True, False), (False, True)])
def test_rerank_candidates_uses_dense_on_accelerator_or_cpu_opt_in(monkeypatch, accelerator, cpu_opt_in):
    monkeypatch.delenv(dense_rerank.NO_DENSE_ENV, raising=False)
    if cpu_opt_in:
        monkeypatch.setenv(dense_rerank.CPU_DENSE_ENV, "1")
    else:
        monkeypatch.delenv(dense_rerank.CPU_DENSE_ENV, raising=False)
    monkeypatch.setattr(dense_rerank, "_accelerator_available", lambda: accelerator)
    _two_row_index(monkeypatch)
    monkeypatch.setattr(dense_rerank, "_get_encoder", _QueryEncoder)

    results = dense_rerank.rerank_candidates("query", _CANDIDATES, corpus="test_corpus")

    assert [row["unit_key"] for row in results] == ["1", "2"]
    assert results[0]["dense_score"] == pytest.approx(1.0)


def test_rerank_candidates_keeps_best_unsectioned_chunk_by_dense_score(monkeypatch):
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE textbook_sections (
            section_id INTEGER, source_file TEXT, section_title TEXT, full_text TEXT
        );
        CREATE TABLE textbooks (
            id INTEGER, chunk_id TEXT, source_file TEXT, title TEXT, text TEXT,
            parent_section_id INTEGER
        );
        INSERT INTO textbook_sections VALUES (7, 'section-book', 'Section', 'section text');
        INSERT INTO textbooks VALUES (1, 'ulp-chunk', 'ulp-book', 'ULP title', 'unsectioned text', NULL);
        """
    )
    units = list(dense_rerank._iter_textbook_units(conn))
    conn.close()
    shard = np.zeros((len(units), dense_rerank.EMBEDDING_DIMS), dtype=np.float16)
    unit_rows = {}
    for row_idx, unit in enumerate(units):
        unit_rows[unit.unit_key] = (0, row_idx)
        shard[row_idx, 0 if unit.unit_key.endswith("ulp-chunk") else 1] = 1.0
    index = dense_rerank.CorpusEmbeddingIndex(
        corpus="textbook_sections",
        shards={0: shard},
        unit_rows=unit_rows,
    )
    monkeypatch.setattr(dense_rerank, "load_corpus_index", lambda *a, **kw: index)

    results = dense_rerank.rerank_candidates(
        "query",
        [
            {"unit_key": units[0].unit_key, "keyword_rank": 1},
            {"unit_key": units[1].unit_key, "keyword_rank": 8},
        ],
        corpus="textbook_sections",
        limit=1,
        encoder=_QueryEncoder(),
    )

    assert [row["unit_key"] for row in results] == ["textbook_sections:ulp-chunk"]
    assert results[0]["dense_score"] == pytest.approx(1.0)
