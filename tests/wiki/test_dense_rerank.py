from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

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
