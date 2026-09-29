from __future__ import annotations

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
