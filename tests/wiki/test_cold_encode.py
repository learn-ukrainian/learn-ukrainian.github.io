from __future__ import annotations

import hashlib
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from wiki.embedding_manifest import EmbeddingManifest

from wiki import cold_encode, dense_rerank


class FakeTokenizer:
    def encode(
        self,
        text: str,
        add_special_tokens: bool = True,
        truncation: bool = True,
        max_length: int | None = None,
    ) -> list[int]:
        tokens = list(range(1, len(text.split()) + 1))
        if max_length is not None:
            limit = max_length - (2 if add_special_tokens else 0)
            tokens = tokens[:limit]
        if add_special_tokens:
            return [0, *tokens, 1]
        return tokens

    def decode(self, token_ids: list[int], skip_special_tokens: bool = True) -> str:
        ids = [token for token in token_ids if not skip_special_tokens or token not in {0, 1}]
        return " ".join(f"tok{token}" for token in ids)


class FakeEncoder:
    def encode(self, texts: list[str], batch_size: int = 16, max_length: int = 512) -> np.ndarray:
        vectors: list[np.ndarray] = []
        for text in texts:
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            seed = np.frombuffer(digest * 64, dtype=np.uint8)[: dense_rerank.EMBEDDING_DIMS].astype(np.float32)
            vector = seed / np.clip(np.linalg.norm(seed), 1e-12, None)
            vectors.append(vector.astype(np.float16))
        return np.stack(vectors, axis=0)


def _db_path(tmp_path: Path) -> Path:
    return tmp_path / "sources.db"


def _manifest_path(tmp_path: Path) -> Path:
    return tmp_path / "embeddings" / "manifest.db"


def _make_db(tmp_path: Path) -> None:
    conn = sqlite3.connect(_db_path(tmp_path))
    conn.execute(
        """
        CREATE TABLE test_small_sources (
            id INTEGER PRIMARY KEY,
            group_name TEXT NOT NULL,
            text TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def _seed_rows(tmp_path: Path, count: int, *, start: int = 1) -> None:
    conn = sqlite3.connect(_db_path(tmp_path))
    conn.executemany(
        "INSERT INTO test_small_sources (id, group_name, text) VALUES (?, ?, ?)",
        [
            (index, f"group-{((index - 1) // 5) + 1}", f"synthetic text {index}")
            for index in range(start, start + count)
        ],
    )
    conn.commit()
    conn.close()


def _loader(conn: sqlite3.Connection):
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, group_name, text FROM test_small_sources ORDER BY id"
    ).fetchall()
    for row in rows:
        text = str(row["text"])
        yield dense_rerank.CorpusUnit(
            unit_key=f"test_small:{int(row['id'])}",
            corpus="test_small",
            parent_key=str(row["group_name"]),
            text=text,
            text_sha256=dense_rerank.text_sha256(text),
            metadata={"group_name": str(row["group_name"])},
        )


def _configure(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_tokenizer = FakeTokenizer()
    fake_encoder = FakeEncoder()
    monkeypatch.setitem(dense_rerank.CORPUS_UNIT_LOADERS, "test_small", _loader)
    monkeypatch.setattr(dense_rerank, "_TOKENIZER", fake_tokenizer)
    monkeypatch.setattr(dense_rerank, "_get_tokenizer", lambda: fake_tokenizer)
    monkeypatch.setattr(dense_rerank, "_ENCODER", fake_encoder)
    monkeypatch.setattr(dense_rerank, "_get_encoder", lambda: fake_encoder)


def test_cold_encode_incremental_append_adds_only_new_units(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _make_db(tmp_path)
    _seed_rows(tmp_path, 10)
    _configure(monkeypatch)

    first = dense_rerank.cold_encode_corpus(
        "test_small",
        db_path=_db_path(tmp_path),
        manifest_db=_manifest_path(tmp_path),
    )
    assert first["encoded_units"] == 10
    assert first["shards_written"] == 1

    manifest = EmbeddingManifest(_manifest_path(tmp_path))
    before_units = {
        row.unit_key: (row.shard_id, row.row_idx, row.text_sha256)
        for row in manifest.active_units_for_corpus("test_small")
    }
    manifest.close()

    _seed_rows(tmp_path, 3, start=11)
    exit_code = cold_encode.main(
        [
            "--corpora",
            "test_small",
            "--db-path",
            str(_db_path(tmp_path)),
            "--manifest-db",
            str(_manifest_path(tmp_path)),
        ]
    )
    assert exit_code == 0

    manifest = EmbeddingManifest(_manifest_path(tmp_path))
    active = {row.unit_key: row for row in manifest.active_units_for_corpus("test_small")}
    shard_map = manifest.shard_map_for_corpus("test_small")
    manifest.close()

    assert len(active) == 13
    assert len(shard_map) == 2
    for unit_key, (shard_id, row_idx, text_sha) in before_units.items():
        assert (active[unit_key].shard_id, active[unit_key].row_idx, active[unit_key].text_sha256) == (
            shard_id,
            row_idx,
            text_sha,
        )
    assert {f"test_small:{index}" for index in range(11, 14)} <= set(active)


def test_cold_encode_reencodes_only_changed_units(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _make_db(tmp_path)
    _seed_rows(tmp_path, 10)
    _configure(monkeypatch)

    dense_rerank.cold_encode_corpus(
        "test_small",
        db_path=_db_path(tmp_path),
        manifest_db=_manifest_path(tmp_path),
    )

    manifest = EmbeddingManifest(_manifest_path(tmp_path))
    before = {row.unit_key: row for row in manifest.active_units_for_corpus("test_small")}
    first_shards = manifest.shard_map_for_corpus("test_small")
    old_vectors = {
        key: np.asarray(np.load(first_shards[row.shard_id], mmap_mode="r")[row.row_idx], dtype=np.float32)
        for key, row in before.items()
        if key in {"test_small:2", "test_small:7"}
    }
    manifest.close()

    conn = sqlite3.connect(_db_path(tmp_path))
    conn.execute("UPDATE test_small_sources SET text = ? WHERE id = 2", ("changed text 2",))
    conn.execute("UPDATE test_small_sources SET text = ? WHERE id = 7", ("changed text 7",))
    conn.commit()
    conn.close()

    exit_code = cold_encode.main(
        [
            "--corpora",
            "test_small",
            "--db-path",
            str(_db_path(tmp_path)),
            "--manifest-db",
            str(_manifest_path(tmp_path)),
        ]
    )
    assert exit_code == 0

    manifest = EmbeddingManifest(_manifest_path(tmp_path))
    after = {row.unit_key: row for row in manifest.active_units_for_corpus("test_small")}
    shard_map = manifest.shard_map_for_corpus("test_small")
    manifest.close()

    assert len(shard_map) == 2
    for unit_key in {"test_small:2", "test_small:7"}:
        assert after[unit_key].shard_id != before[unit_key].shard_id
        new_vector = np.asarray(
            np.load(shard_map[after[unit_key].shard_id], mmap_mode="r")[after[unit_key].row_idx],
            dtype=np.float32,
        )
        assert not np.allclose(new_vector, old_vectors[unit_key])

    for unit_key in set(after) - {"test_small:2", "test_small:7"}:
        assert after[unit_key].shard_id == before[unit_key].shard_id
        assert after[unit_key].row_idx == before[unit_key].row_idx
